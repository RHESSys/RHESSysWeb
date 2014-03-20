"""@package tests.test_flowtableio
    
@brief Test methods for flowtableio

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
    * Neither the name of the University of North Carolina at Chapel Hill nor the
      names of its contributors may be used to endorse or promote products
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
python -m unittest test_flowtableio
@endcode
""" 
import os, errno
import sys
import gzip
import filecmp
from shutil import rmtree
from zipfile import ZipFile
from unittest import TestCase

from flowtableio import readFlowtable
from flowtableio import writeFlowtable
from flowtableio import getReceiversForFlowtableEntry
from flowtableio import getEntryForFlowtableKey
import rhessystypes

from grassdatalookup import GrassDataLookup
from grassdatalookup import GRASSConfig


## Constants
ZERO = 0.001

## Unit tests
class TestReadFlowtable(TestCase):

    @classmethod
    def setUpClass(cls):
        # We gzip the flow table to be nice to GitHub, unzip it
        cls.flowtablePath = os.path.abspath('./tests/data/world5m_dr5.flow')
        flowtableGz = "%s.gz" % (cls.flowtablePath,)
        if not os.access(flowtableGz, os.R_OK):
            raise IOError(errno.EACCES, "Unable to read flow table %s" %
                      flowtableGz)
        cls.flowtableDir = os.path.split(flowtableGz)[0]
        if not os.access(cls.flowtableDir, os.W_OK):
            raise IOError(errno.EACCES, "Unable to write to flow table dir %s" %
                          cls.flowtableDir)
        fIn = gzip.open(flowtableGz, 'rb')
        fOut = open(cls.flowtablePath, 'wb')
        fOut.write(fIn.read())
        fIn.close()
        fOut.close()
        
        # We zip the GRASSData folder to be nice to GitHub, unzip it
        cls.grassDBasePath = os.path.abspath('./tests/data/GRASSData')
        grassDBaseZip = "%s.zip" % (cls.grassDBasePath,)
        if not os.access(grassDBaseZip, os.R_OK):
            raise IOError(errno.EACCES, "Unable to read GRASS data zip %s" %
                      grassDBaseZip)
        grassDBaseDir = os.path.split(grassDBaseZip)[0]
        if not os.access(grassDBaseDir, os.W_OK):
            raise IOError(errno.EACCES, "Unable to write to GRASS data parent dir %s" %
                          grassDBaseDir)
        zip = ZipFile(grassDBaseZip, 'r')
        extractDir = os.path.split(cls.grassDBasePath)[0]
        zip.extractall(path=extractDir)
        
        gisbase = os.environ['GISBASE']
        grassConfig = GRASSConfig(gisbase=gisbase, dbase=cls.grassDBasePath, location='DR5_5m', mapset='taehee')
        cls.grassdatalookup = GrassDataLookup(grass_config=grassConfig)
        
        cls.patchMap = "patch_5m"
        cls.zoneMap = "hillslope"
        cls.hillslopeMap = "hillslope"
         
        # Build the flow table
        cls.flowtable = readFlowtable(cls.flowtablePath)

    @classmethod
    def tearDownClass(cls):
        # Get rid of the un-gzipped flow table
        os.unlink(cls.flowtablePath)
        # Get rid of unzipped GRASSData
        rmtree(cls.grassDBasePath)

    def testReadWriteFlowtable(self):
        testOutpath = os.path.join(self.flowtableDir, "test-flow.flow")
        writeFlowtable(self.flowtable, testOutpath)
        self.assertTrue( filecmp.cmp(self.flowtablePath, testOutpath) )
        os.unlink(testOutpath)

    def testEntryWithoutRoad(self):
        testKeyStr = "324225     67     67"
        values = testKeyStr.split()
        testEntry = rhessystypes.getFQPatchIDFromArray(values)
        print unicode(testEntry)
        items = self.flowtable[testEntry] 
        self.assertTrue( len(items) == 9 )
        self.assertTrue( items[0].patchID == 324225 )
        self.assertTrue( items[1].patchID == 323378 )
        self.assertTrue( abs(items[1].gamma - 0.00187500 ) < ZERO )
        
    def testEntryWithRoad(self):
        testKeyStr = "367400     67     67"
        values = testKeyStr.split()
        testEntry = rhessystypes.getFQPatchIDFromArray(values)
        items = self.flowtable[testEntry]
        self.assertTrue( len(items) == 10)
        self.assertTrue( items[0].patchID == 367400 )
        self.assertTrue( items[1].patchID == 366553 )
        self.assertTrue( items[8].patchID == 368247 )
        self.assertTrue( abs(items[8].gamma - 0.53678352 ) < ZERO )
        self.assertTrue( abs(items[9].roadWidth - 5.0) < ZERO )
    
    def testGetReceiversForFlowtableEntryWithoutRoad(self):
        testKeyStr = "324225     67     67"
        values = testKeyStr.split()
        testEntry = rhessystypes.getFQPatchIDFromArray(values)
        receivers = getReceiversForFlowtableEntry(testEntry, self.flowtable)
        self.assertTrue( len(receivers) == 8 )
        self.assertTrue( receivers[0].patchID == 323378 )
        self.assertTrue( abs(receivers[7].gamma - 0.00000000) < ZERO )
        
    def testGetReceiversForFlowtableEntryWithRoad(self):
        testKeyStr = "367400     67     67"
        values = testKeyStr.split()
        testEntry = rhessystypes.getFQPatchIDFromArray(values)
        receivers = getReceiversForFlowtableEntry(testEntry, self.flowtable)
        self.assertTrue( len(receivers) == 8 )
        self.assertTrue( receivers[0].patchID == 366553 )
        self.assertTrue( abs(receivers[7].gamma - 0.53678352) < ZERO )
        
    def testUpdateReceiversForFlowtableEntryWithoutRoad(self):
        testKeyStr = "324225     67     67"
        values = testKeyStr.split()
        testEntry = rhessystypes.getFQPatchIDFromArray(values)
        receivers = getReceiversForFlowtableEntry(testEntry, self.flowtable)
        
        items = self.flowtable[testEntry] 
        self.assertTrue( len(items) == 9 )
        # Test flow table entry
        self.assertTrue( items[0].patchID == 324225)
        
        numReceivers = len(receivers)
        newGamma = float(1 / numReceivers)
        for receiver in receivers:
            receiver.gamma = newGamma

        receivers = getReceiversForFlowtableEntry(testEntry, self.flowtable)
        for receiver in receivers:
            self.assertTrue( receiver.gamma == newGamma )
            
        items = self.flowtable[testEntry] 
        self.assertTrue( len(items) == 9 )
        # Test flow table entry
        self.assertTrue( items[0].patchID == 324225 )
        
        
    def testGetTotalGamma(self):
        testKeyStr = "367400     67     67"
        values = testKeyStr.split()
        testEntry = rhessystypes.getFQPatchIDFromArray(values)
        
        totalGamma = getEntryForFlowtableKey(testEntry, self.flowtable).totalGamma
        self.assertTrue( totalGamma == 0.451261 )
        
    
    def testUpdateReceiversForFlowtableEntryWithRoad(self):
        testKeyStr = "367400     67     67"
        values = testKeyStr.split()
        testEntry = rhessystypes.getFQPatchIDFromArray(values)
        
        receivers = getReceiversForFlowtableEntry(testEntry, self.flowtable)
        
        items = self.flowtable[testEntry] 
        self.assertTrue( len(items) == 10 )
        # Test flow table entry
        self.assertTrue( items[0].patchID == 367400 )
        
        numReceivers = len(receivers)
        newGamma = float(1 / numReceivers)
        for receiver in receivers:
            receiver.gamma = newGamma
        
        receivers = getReceiversForFlowtableEntry(testEntry, self.flowtable)
        for receiver in receivers:
            self.assertTrue( receiver.gamma == newGamma )
            
        items = self.flowtable[testEntry] 
        self.assertTrue( len(items) == 10 )
        # Test flow table entry
        self.assertTrue( items[0].patchID == 367400)
        
    def testSpecificPatchReceiverCoordinateLookupWithoutRoad(self):
        testKeyStr = "324225     67     67"
        values = testKeyStr.split()
        testEntry = rhessystypes.getFQPatchIDFromArray(values)
        items = self.flowtable[testEntry] 
        self.assertTrue( len(items) == 9 )
        
        recv = getReceiversForFlowtableEntry(testEntry, self.flowtable)
        self.assertTrue( len(recv) == 8 )
        
        coords = self.grassdatalookup.getCoordinatesForFQPatchIDs(recv, self.patchMap, self.zoneMap, self.hillslopeMap)
        keys = coords.keys()
        for key in keys:
            self.assertTrue( len(coords[key]) == 1 )