"""@package rhessysweb.readflowtable

@brief Read a RHESSys flow table into a dict where the keys are
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

Usage: 
@code
python -m unittest ReadFlowtable
@endcode
"""
import os, sys, errno
from collections import namedtuple
import argparse

import rhessysweb.types

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

FlowTableEntryReceiver = namedtuple('FlowTableEntryReceiver', ['patchID', 'zoneID', 'hillID', 'gamma'], verbose=False)

def getFlowTableEntryReceiverFromArray(values):
    """ @brief Build a FlowTableEntryReceiver from an array
        @param values Array of strings representing tokenized flow table entry
        receiver
        @return FlowTableEntryReciver representing the flow table entry
    """
    assert( len(values) == FLOW_ENTRY_ITEM_NUM_TOKENS )
    return FlowTableEntryReceiver(patchID=int(values[0]),\
                                  zoneID=int(values[1]), \
                                  hillID=int(values[2]), \
                                  gamma=float(values[3]) )

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
def readFlowtable(flowtable):
    """ @brief Read a RHESSys flow table into a dict where the keys are 
        instances of FlowTableEntry and the values lists containing one or more
        FlowTableEntryReceiver objects followed by possibly one 
        FlowTableEntryRoad object.
    
        @param flowtable String representing the absolute path of the file
        containing the RHESSys flowtable

        @return The dict representing the flow table
    """
    flowDict = dict()
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
        if len(values) == FLOW_ENTRY_NUM_TOKENS:
            # Check for error in flow table structure
            if readReceivers and numRead < numAdj:
                raise Exception("Error in flow table at line %d, only %d of %d adjacent recievers read" % (numLines, numRead, numAdj))

            # FlowDict uses a FlowTableKey as reference, adds newEntry and items as entries
            newEntry = getFlowTableEntryFromArray(values)
            newKey = rhessysweb.types.FQPatchID(patchID=newEntry.patchID, zoneID=newEntry.zoneID, hillID=newEntry.hillID)
            flowDict[newKey] = list()
            flowDict[newKey].append(newEntry)
            readReceivers = True
            numRead = 0
            numAdj = int(newEntry.numAdjacent)
            currEntry = newKey
        elif len(values) == FLOW_ENTRY_ITEM_NUM_TOKENS and readReceivers:
            # Check for error in flow table structure
            if numRead > numAdj:
                raise Exception("Error in flow table at line %d, already read %d of %d adjacent" % (numLines, numRead, numAdj))
            # See if we need to read the stream patch to which the road drains
            if numRead == numAdj:
                item = getFlowTableEntryRoadFromArray(values)
            else:
                item = getFlowTableEntryReceiverFromArray(values)
                numRead += 1
            # Write item to flow table entry
            flowDict[currEntry].append(item)
 
    flow.close()   
    return flowDict

    
        


