"""@package flowtableio

@brief Routines for reading, modifying, and writing RHESSys flow tables.
        The flow table is structured into a dict where the keys are
        instances of FlowTableEntry and the values lists containing
        one or more FlowTableEntries followed by possibly one
        FlowTableEntryReceive objects. To test run with the flow table
        distributed with this file

This software is provided free of charge under the New BSD License. Please see
the following license information:

Copyright (c) 2013, University of North Carolina at Chapel Hill
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the University of North Carolina at Chapel Hill nor 
      the names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE UNIVERSITY OF NORTH CAROLINA AT CHAPEL HILL
BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT 
LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


@author Brian Miles <brian_miles@unc.edu>

"""
import os, sys, errno
from collections import namedtuple
from collections import OrderedDict
import argparse

import rhessystypes

## Constants
LAND_TYPE_ROAD = 2
FLOW_ENTRY_NUM_TOKENS = 11
FLOW_ENTRY_ITEM_NUM_TOKENS = 4

## Type definitions
FlowTableEntry = namedtuple('FlowTableEntry', ['patchID', 'zoneID', 'hillID', 'x', 'y', 'z', 'accumArea', 'area', 'landType', 'totalGamma', 'numAdjacent'], verbose=False)

def getFlowTableEntryFromArray(values):
    """ @brief Build a FlowTableEntry from an array
        @param values Array of strings representing tokenized flow table entry
        @return FlowTableEntry representing the flow table entry
    """
    assert( len(values) == FLOW_ENTRY_NUM_TOKENS )
    return FlowTableEntry(patchID=int(values[0]), \
                          zoneID=int(values[1]), \
                          hillID=int(values[2]), \
                          x=float(values[3]), y=float(values[4]), \
                          z=float(values[5]), \
                          accumArea=float(values[6]), \
                          area=int(values[7]), \
                          landType=int(values[8]), \
                          totalGamma=float(values[9]), \
                          numAdjacent=int(values[10]) )


class FlowTableEntryReceiver:
    def __init__(self, patchID, zoneID, hillID, gamma):
        """ @brief Build a FlowTableEntryReceiver
            @param patchID String representing the patch ID, will be cast to an int
            @param zoneID String representing the zone ID, will be cast to an int
            @param hillID String representing the hill ID, will be cast to an int
            @param gamma String representing the gamma, will be cast to a float
            @return FlowTableEntryReciver representing the flow table entry
        """
        self.patchID = int(patchID)
        self.zoneID = int(zoneID)
        self.hillID = int(hillID)
        self.gamma = float(gamma)
   
FlowTableEntryRoad = namedtuple('FlowTableEntryReceiver', ['streamPatchID', 'streamZoneID', 'streamHillID', 'roadWidth'], verbose=False) 

def getFlowTableEntryRoadFromArray(values):
    """ @brief Build a FlowTableEntryRoad from an array
        @param values Array of strings representing tokenized flow table entry
        road
        @return FlowTableEntryRoad representing the flow table entry
    """
    assert( len(values) == FLOW_ENTRY_ITEM_NUM_TOKENS )
    return FlowTableEntryRoad(streamPatchID=int(values[0]), \
                               streamZoneID=int(values[1]), \
                               streamHillID=int(values[2]), \
                               roadWidth=float(values[3]) )

## Function definitions
def writeFlowtable(flowtableDict, flowtableOutfile):
    """ @brief Write a RHESSys flow table from a representation stored in collections.OrderedDict
        returned by readFlowtable.
        
        @param flowtableDict Flow table as returned by readFlowtable
        @param flowtableOutfile String representing the absolute path of the flow table to be written
    """
    flowtableOutdir = os.path.split(flowtableOutfile)[0]
    if not os.access(flowtableOutdir, os.W_OK):
        raise IOError("Unable to write to output directory %s\n" % (flowtableOutdir,) )
    flowFile = open(flowtableOutfile, 'w')
    
    keys = flowtableDict.keys()
    numKeys = len(keys)
    
    flowFile.write("%8d" % (numKeys,) )
    for key in keys:
        items = flowtableDict[key]
        for item in items:
            if isinstance(item, FlowTableEntryReceiver):
                flowFile.write("\n%16d %6d %6d %8.8f  " % \
                               (item.patchID, item.zoneID, item.hillID, item.gamma) )
            elif isinstance(item, FlowTableEntry):
                flowFile.write("\n %6d %6d %6d %6.1f %6.1f %6.1f %10f %d %4d %f %4d" % \
                               (item.patchID, item.zoneID, item.hillID, item.x, item.y, \
                                item.z, item.accumArea, item.area, item.landType, \
                                item.totalGamma, item.numAdjacent) )
            elif isinstance(item, FlowTableEntryRoad):
                flowFile.write("\n%16d %6d %6d %lf" % \
                               (item.streamPatchID, item.streamZoneID, item.streamHillID, \
                               item.roadWidth) )
    
    flowFile.close()

def readFlowtable(flowtable):
    """ @brief Read a RHESSys flow table into a dict where the keys are 
        instances of rhessysweb.types.FQPatchID and the values lists containing one or more
        FlowTableEntryReceiver objects followed by possibly one 
        FlowTableEntryRoad object.
    
        @param flowtable String representing the absolute path of the file
        containing the RHESSys flowtable

        @return The dict representing the flow table
    """
    #flowDict = dict()
    flowDict = OrderedDict()
    flow = open(flowtable, 'r')

    numPatches = flow.readline().lstrip()

    # State variables
    readReceivers = False
    numRead = -1
    numAdj = -1
    numLines = 0
    currEntry = None

    for line in flow:
        numLines += 1
        line = line.strip()
        values = line.split()
        lv = len(values)
        if lv == FLOW_ENTRY_NUM_TOKENS:
            # Check for error in flow table structure
            if readReceivers and numRead < numAdj:
                raise Exception("Error in flow table at line %d, only %d of %d adjacent recievers read" % (numLines, numRead, numAdj))

            # FlowDict uses a FlowTableKey as reference, adds newEntry and items as entries
            newEntry = getFlowTableEntryFromArray(values)
            newKey = rhessystypes.FQPatchID(patchID=newEntry.patchID, zoneID=newEntry.zoneID, hillID=newEntry.hillID)
            flowDict[newKey] = [newEntry]
            readReceivers = True
            numRead = 0
            numAdj = int(newEntry.numAdjacent)
            currEntry = newKey
        elif lv == FLOW_ENTRY_ITEM_NUM_TOKENS and readReceivers:
            # Check for error in flow table structure
            if numRead > numAdj:
                raise Exception("Error in flow table at line %d, already read %d of %d adjacent" % (numLines, numRead, numAdj))
            # See if we need to read the stream patch to which the road drains
            if numRead == numAdj:
                item = getFlowTableEntryRoadFromArray(values)
            else:
                item = FlowTableEntryReceiver(values[0], values[1], values[2], values[3])
                numRead += 1
            # Write item to flow table entry
            flowDict[currEntry].append(item)
 
    flow.close()   
    return flowDict

def getEntryForFlowtableKey(key, flowtable):
    """ @brief Get flow table entry for a given flow table key
    
        @param key rhessysweb.types.FQPatchID
        @param flowtable Dict returned by readFlowtable
    
        @return FlowTableEntry object, None if the table has no such key
    """
    entry = None
    
    try:
        items = flowtable[key]
        for item in items:
            if isinstance(item, FlowTableEntry):
                entry = item
    except KeyError:
        pass
    
    return entry


def getReceiversForFlowtableEntry(key, flowtable):    
    """ @brief Get list of receivers for a given flow table key
    
        @param key rhessysweb.types.FQPatchID
        @param flowtable Dict returned by readFlowtable
    
        @return List of FlowTableEntryReceiver objects
    """
    recvs = list()
    
    items = flowtable[key]
    for item in items:
        if isinstance(item, FlowTableEntryReceiver):
            recvs.append(item)
    
    return recvs


