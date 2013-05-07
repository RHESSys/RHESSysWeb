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
from grassdatalookup import GrassDataLookup
from grassdatalookup import GRASSConfig

## Constants
ZERO = 4.999

## Unit tests
class TestGRASSDataLookup(TestCase):
    
    @classmethod
    def setUpClass(cls):
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
        
        cls.inPatchID = 309999
        cls.inZoneID = 73
        cls.inHillID = 73
        cls.easting = 349325.089515
        cls.northing = 4350341.816966
        cls.patchMap = "patch_5m"
        cls.zoneMap = "hillslope"
        cls.hillslopeMap = "hillslope"
        
    
    @classmethod
    def tearDownClass(cls):
        rmtree(cls.grassDBasePath)
   
   
    def testGetCoordinatesForFQPatchIDs(self):
        fqPatchIDs = [ (rhessystypes.FQPatchID(patchID=self.inPatchID, \
                                                   zoneID=self.inZoneID, hillID=self.inHillID)) ]
        coords = self.grassdatalookup.getCoordinatesForFQPatchIDs(fqPatchIDs, self.patchMap, self.zoneMap, self.hillslopeMap)
        self.assertTrue( len(coords) == 1 )
        keys = coords.keys()
        coordPair = coords[keys[0]][0]
        self.assertTrue( abs(coordPair.easting - self.easting) < ZERO )
        self.assertTrue( abs(coordPair.northing - self.northing) < ZERO )
        
    
    def testGetFQPatchIDForCoordinates(self):
        fqPatchIDs = [ (rhessystypes.FQPatchID(patchID=self.inPatchID, \
                                                   zoneID=self.inZoneID, hillID=self.inHillID)) ]
        coords = self.grassdatalookup.getCoordinatesForFQPatchIDs(fqPatchIDs, self.patchMap, self.zoneMap, self.hillslopeMap)
        self.assertTrue( len(coords) == 1 )
        keys = coords.keys()
        coordPair = coords[keys[0]][0]
        self.assertTrue( abs(coordPair.easting - self.easting) < ZERO )
        self.assertTrue( abs(coordPair.northing - self.northing) < ZERO )
        
        coordinate = rhessystypes.getCoordinatePair(coordPair.easting, coordPair.northing)
        (patchID, zoneID, hillID) = \
            self.grassdatalookup.getFQPatchIDForCoordinates(coordinate, \
                                       self.patchMap, self.zoneMap, self.hillslopeMap)
        self.assertTrue( self.inPatchID == patchID )
        self.assertTrue( self.inZoneID == zoneID )
        self.assertTrue( self.inHillID == hillID )
        
