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
import gzip
import filecmp
from unittest import TestCase

from flowtableio import readFlowtable
from flowtableio import writeFlowtable
from flowtableio import getReceiversForFlowtableEntry
from rhessystypes import getFQPatchIDFromArray


## Constants
ZERO = 0.001

## Unit tests
class TestReadFlowtable(TestCase):

    def setUp(self):
        # We gzip the flow table to be nice to GitHub, unzip it
        self.flowtablePath = os.path.abspath('./data/dr5_5m_preroof.flow.flow')
        flowtableGz = "%s.gz" % (self.flowtablePath,)
        if not os.access(flowtableGz, os.R_OK):
            raise IOError(errno.EACCES, "Unable to read flow table %s" %
                      flowtableGz)
        self.flowtableDir = os.path.split(flowtableGz)[0]
        if not os.access(self.flowtableDir, os.W_OK):
            raise IOError(errno.EACCES, "Unable to write to flow table dir %s" %
                          self.flowtableDir)
        fIn = gzip.open(flowtableGz, 'rb')
        fOut = open(self.flowtablePath, 'wb')
        fOut.write(fIn.read())
        fIn.close()
        fOut.close()
         
        # Build the flow table
        self.flowtable = readFlowtable(self.flowtablePath)

    def tearDown(self):
        # Get rid of the un-gzipped flow table
        os.unlink(self.flowtablePath)

    def testReadWriteFlowtable(self):
        testOutpath = os.path.join(self.flowtableDir, "test-flow.flow")
        writeFlowtable(self.flowtable, testOutpath)
        self.assertTrue( filecmp.cmp(self.flowtablePath, testOutpath) )
        os.unlink(testOutpath)

    def testEntryWithoutRoad(self):
        testKeyStr = "328469    145    145"
        values = testKeyStr.split()
        testEntry = getFQPatchIDFromArray(values)
        items = self.flowtable[testEntry] 
        self.assertTrue( len(items) == 9 )
        self.assertTrue( items[0].patchID == 328469)
        self.assertTrue( items[1].patchID == 327622 )
        self.assertTrue( abs(items[8].gamma - 0.27929801) < ZERO )
        
    def testEntryWithRoad(self):
        testKeyStr = "366555    145    145"
        values = testKeyStr.split()
        testEntry = getFQPatchIDFromArray(values)
        items = self.flowtable[testEntry]
        self.assertTrue( len(items) == 9)
        self.assertTrue( items[0].patchID == 366555)
        self.assertTrue( items[1].patchID == 365709 )
        self.assertTrue( abs(items[7].gamma - 0.18454391) < ZERO )
        self.assertTrue( abs(items[8].roadWidth - 5.0) < ZERO )
    
    def testGetReceiversForFlowtableEntryWithoutRoad(self):
        testKeyStr = "328469    145    145"
        values = testKeyStr.split()
        testEntry = getFQPatchIDFromArray(values)
        receivers = getReceiversForFlowtableEntry(testEntry, self.flowtable)
        self.assertTrue( len(receivers) == 8 )
        self.assertTrue( receivers[0].patchID == 327622 )
        self.assertTrue( abs(receivers[7].gamma - 0.27929801) < ZERO )
        
    def testGetReceiversForFlowtableEntryWithRoad(self):
        testKeyStr = "366555    145    145"
        values = testKeyStr.split()
        testEntry = getFQPatchIDFromArray(values)
        receivers = getReceiversForFlowtableEntry(testEntry, self.flowtable)
        self.assertTrue( len(receivers) == 7 )
        self.assertTrue( receivers[0].patchID == 365709 )
        self.assertTrue( abs(receivers[6].gamma - 0.18454391) < ZERO )
        
    def testUpdateReceiversForFlowtableEntryWithoutRoad(self):
        testKeyStr = "328469    145    145"
        values = testKeyStr.split()
        testEntry = getFQPatchIDFromArray(values)
        receivers = getReceiversForFlowtableEntry(testEntry, self.flowtable)
        
        items = self.flowtable[testEntry] 
        self.assertTrue( len(items) == 9 )
        # Test flow table entry
        self.assertTrue( items[0].patchID == 328469)
        
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
        self.assertTrue( items[0].patchID == 328469)
        
    def testUpdateReceiversForFlowtableEntryWithRoad(self):
        testKeyStr = "366555    145    145"
        values = testKeyStr.split()
        testEntry = getFQPatchIDFromArray(values)
        receivers = getReceiversForFlowtableEntry(testEntry, self.flowtable)
        
        items = self.flowtable[testEntry] 
        self.assertTrue( len(items) == 9 )
        # Test flow table entry
        self.assertTrue( items[0].patchID == 366555)
        
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
        self.assertTrue( items[0].patchID == 366555)
        

