"""@package tests.test_grassdatalookup
    
@brief Test methods for rhessysweb.grassdatalookup

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
python -m unittest test_grassdatalookup
@endcode

@note Must have GRASS installed and have GISBASE environmental variable set.
""" 
import os, errno
from shutil import rmtree
from zipfile import ZipFile
from unittest import TestCase

import rhessystypes
from grassdatalookup import getFQPatchIDForCoordinates
from grassdatalookup import getCoordinatesForFQPatchIDs
from grassdatalookup import GRASSConfig

## Constants
ZERO = 3

## Unit tests
class TestGRASSDataLookup(TestCase):
    
    def setUp(self):
        # We zip the GRASSData folder to be nice to GitHub, unzip it
        self.grassDBasePath = os.path.abspath('./tests/data/GRASSData')
        grassDBaseZip = "%s.zip" % (self.grassDBasePath,)
        if not os.access(grassDBaseZip, os.R_OK):
            raise IOError(errno.EACCES, "Unable to read GRASS data zip %s" %
                      grassDBaseZip)
        grassDBaseDir = os.path.split(grassDBaseZip)[0]
        if not os.access(grassDBaseDir, os.W_OK):
            raise IOError(errno.EACCES, "Unable to write to GRASS data parent dir %s" %
                          grassDBaseDir)
        zip = ZipFile(grassDBaseZip, 'r')
        extractDir = os.path.split(self.grassDBasePath)[0]
        zip.extractall(path=extractDir)
        
        gisbase = os.environ['GISBASE']
        self.grassMapset = GRASSConfig(gisbase=gisbase, dbase=self.grassDBasePath, location='DR5', mapset='taehee')
        
        self.inPatchID = 288804
        #self.inPatchID = 289650
        self.inZoneID = 145
        self.inHillID = 145
        self.easting = 349100.0
        self.northing = 4350470.0
        self.patchMap = "patch_5m"
        self.zoneMap = "hillslope"
        self.hillslopeMap = "hillslope"
    
    def tearDown(self):
        rmtree(self.grassDBasePath)
   
   
    def testGetCoordindateForFQPatchIDs(self):
        fqPatchIDs = [ (rhessystypes.FQPatchID(patchID=self.inPatchID, \
                                                   zoneID=self.inZoneID, hillID=self.inHillID)) ]
        coords = getCoordinatesForFQPatchIDs(fqPatchIDs, self.grassMapset, self.patchMap, self.zoneMap, self.hillslopeMap)
        self.assertTrue( len(coords) == 1 )
        coordPair = coords[0]
        self.assertTrue( abs(coordPair.easting - self.easting) < ZERO )
        self.assertTrue( abs(coordPair.northing - self.northing) < ZERO )
    
    def testGetFQPatchIDForCoordinates(self):
        (patchID, zoneID, hillID) = \
            getFQPatchIDForCoordinates(self.easting, self.northing, self.grassMapset, \
                                       self.patchMap, self.zoneMap, self.hillslopeMap)
        self.assertTrue( self.inPatchID == patchID )
        self.assertTrue( self.inZoneID == zoneID )
        self.assertTrue( self.inHillID == hillID )
        
