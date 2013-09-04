"""@package grassdatalookup

@brief Perform lookups against data stored in GRASS GIS datasets 

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
"""
import os, sys
import tempfile
from collections import namedtuple
from collections import OrderedDict
from ctypes import *
import importlib

from osgeo import osr

import rhessystypes

GRASSConfig = namedtuple('GRASSConfig', ['gisbase', 'dbase', 'location', 'mapset'], verbose=False)

class GrassDataLookup(object): 
    def __init__(self, grass_scripting=None, grass_lib=None, grass_config=None):
        """ @brief Constructor for GrassDataLookup
        
            @param grass_scripting Previously imported grass.script (GRASS scripting API), 
            if None, grass.script will be imported
            @param grass_lib Previously imported grass.lib.gis (low-level GRASS API); if None
            grass.lib.gis will be imported
            @param grass_config GRASSConfig instance 
        """
        self.grass_config = grass_config
        
        if not grass_scripting:
            self.g = self._setupGrassScriptingEnvironment()
        else:
            self.g = grass_scripting
            
        if not grass_lib:
            self.grass_lowlevel = self._setupGrassEnvironment()

        else:
            self.grass_lowlevel = grass_lib 
        
    
    def getSpatialReferenceForGRASSDataset(self):
        """ @brief Return the spatial reference for a GRASS mapset 
    
            @param grassConfig GRASSConfig specifying the GRASS mapset
            that contains 
    
            @return osgeo.osr instance representing the
            spatial reference
        """
        
        s_srs = osr.SpatialReference()
        proj = self.g.read_command('g.proj', flags='j')
        s_srs.ImportFromProj4( proj )
        return s_srs
    
    def getCoordinatesForFQPatchIDs(self, fqPatchIDs, patchMap, zoneMap, hillslopeMap):
        """ @brief Get the geographic coordinates for a list of patches identified by
            their fully qualified patch ID. The fully qualified patch ID is the combination 
            of the patchID, zoneID, and hillslopeID.
        
            @param List of rhessystypes.FQPatchID objects representing a fully qualified 
            patch ID
            @param grassConfig GRASSConfig specifying the GRASS mapset that contains 
            the patch, zone, and hillslope maps
            @param patchMap String representing the name of the patch map
            @param zoneMap String representing the name of the zone map 
            @param hillslopeMap String representing the name of the hillslope map
            
            @return Dict mapping rhessystypes.FQPatchID to the list of rhessysweb.types.CoordinatePair 
            objects representing the raster pixels that make up each patch in the input list 
            
        """
        coords = {}
        
        # Set up GRASS environment
        self.grass_lowlevel.G_gisinit('')
        
        # Get the window so we can conver row,col to easting,northing
        window = self.grass_lowlevel.Cell_head()
        self.grass_lowlevel.G_get_window(byref(window))
        numRows = self.grass_lowlevel.G_window_rows()
        numCols = self.grass_lowlevel.G_window_cols()
        
        # Open patch map
        patch = self.grass_lowlevel.G_find_cell2(patchMap, '')
        patch = c_char_p(patch).value
        patchType = self.grass_lowlevel.G_raster_map_type(patchMap, patch)
        if patchType == 0: 
            ptype = POINTER(c_int) 
        elif patchType == 1: 
            ptype = POINTER(c_float) 
        elif patchType == 2: 
            ptype = POINTER(c_double) 
        patchFd = self.grass_lowlevel.G_open_cell_old(patchMap, patch) 
        patchRast = self.grass_lowlevel.G_allocate_raster_buf(patchType)     
        patchRast = cast(c_void_p(patchRast), ptype) 
        
        # Open zone map
        zone = self.grass_lowlevel.G_find_cell2(zoneMap, '')
        zone = c_char_p(zone).value
        zoneType = self.grass_lowlevel.G_raster_map_type(zoneMap, zone)
        if zoneType == 0: 
            ptype = POINTER(c_int) 
        elif zoneType == 1: 
            ptype = POINTER(c_float) 
        elif zoneType == 2: 
            ptype = POINTER(c_double) 
        zoneFd = self.grass_lowlevel.G_open_cell_old(zoneMap, zone) 
        zoneRast = self.grass_lowlevel.G_allocate_raster_buf(zoneType)     
        zoneRast = cast(c_void_p(zoneRast), ptype) 
        
        # Open hill map
        hill = self.grass_lowlevel.G_find_cell2(hillslopeMap, '')
        hill = c_char_p(hill).value
        hillType = self.grass_lowlevel.G_raster_map_type(hillslopeMap, hill)
        if hillType == 0: 
            ptype = POINTER(c_int) 
        elif hillType == 1: 
            ptype = POINTER(c_float) 
        elif hillType == 2: 
            ptype = POINTER(c_double) 
        hillFd = self.grass_lowlevel.G_open_cell_old(hillslopeMap, hill) 
        hillRast = self.grass_lowlevel.G_allocate_raster_buf(hillType)     
        hillRast = cast(c_void_p(hillRast), ptype) 
#        print( "getCoordinatesForFQPatchIDs: patchIDs: %s" % (fqPatchIDs,) )
         
        for row in range(numRows):
            # Get current row for each dataset
            self.grass_lowlevel.G_get_raster_row(patchFd, patchRast, row, patchType)
            self.grass_lowlevel.G_get_raster_row(zoneFd, zoneRast, row, zoneType)
            self.grass_lowlevel.G_get_raster_row(hillFd, hillRast, row, hillType)
        
            for col in range(numCols):
                for fqPatchID in fqPatchIDs:
                    if patchRast[col] == fqPatchID.patchID and \
                        zoneRast[col] == fqPatchID.zoneID and \
                        hillRast[col] == fqPatchID.hillID:
                        # Match found, get its coordinates
                        easting = self.grass_lowlevel.G_col_to_easting(col + 0.5, byref(window))
                        northing = self.grass_lowlevel.G_row_to_northing(row + 0.5, byref(window))
                        try:
                            coordList = coords[fqPatchID]
                        except KeyError:
                            coordList = []
                            coords[fqPatchID] = coordList
                        coordList.append(rhessystypes.getCoordinatePair(easting, northing))
#                        print( "row: %d, col: %d; patch: %d, %d, %d; coordList: %s" % \
#                               (row, col, fqPatchID.patchID, fqPatchID.zoneID, fqPatchID.hillID, coordList) )
        
        # Clean up
        self.grass_lowlevel.G_close_cell(patchFd)
        self.grass_lowlevel.G_free(patchRast)
        self.grass_lowlevel.G_close_cell(zoneFd)
        self.grass_lowlevel.G_free(zoneRast)
        self.grass_lowlevel.G_close_cell(hillFd)
        self.grass_lowlevel.G_free(hillRast)
        
#        os.environ['GIS_LOCK'] = ''
#        os.unlink(os.environ['GISRC'])
        
        returnCoords = OrderedDict()
        for fqPatchID in fqPatchIDs:
            returnCoords[fqPatchID] = coords[fqPatchID]
        
        return returnCoords
    
    
    def _getCentroidCoordinatesForPatches(self, coordDict):
        """ @brief return a list of patch centroid coordinates for each list of patch sub-cell coordinates 
            stored in a dictionary.
            
            @param coordDict Dictionary mapping fully qualified patch ID to a list of patch sub-cell 
            coordindates
            
            @return List of coordinates representing the centroid of each cell
        """
        coords = list()
        keys = coordDict.keys()
        for key in keys:
            coordList = coordDict[key]
            numCoords = len(coordList)
            easting = northing = 0.0
            if numCoords > 0:
                for c in coordList:
                    easting += c.easting
                    northing += c.northing
                easting = easting / numCoords
                northing = northing / numCoords
            coords.append(rhessystypes.getCoordinatePair(easting, northing))
        
        return coords
    
    
    def getFQPatchIDForCoordinates(self, coordinate, patchMap, zoneMap, hillslopeMap):
        """ @brief Get the fully qualified ID of the patch located at a coordinate pair.
            The fully qualified patch ID is the combination of the patchID, zoneID,
            and hillslopeID.
        
            @param coordinate rhessystypes.CoordinatePair
            @param grassConfig GRASSConfig specifying the GRASS mapset that contains 
            the patch, zone, and hillslope maps
            @param patchMap String representing the name of the patch map
            @param zoneMap String representing the name of the zone map 
            @param hillslopeMap String representing the name of the hillslope map
            
            @return FQPatchID
        """
        patchID = None
        zoneID = None
        hillID = None
        
        # Translate coordinates to row, col
        window = self.grass_lowlevel.Cell_head()
        self.grass_lowlevel.G_get_window(byref(window))
        row = int( self.grass_lowlevel.G_northing_to_row(coordinate.northing, byref(window)) )
        col = int( self.grass_lowlevel.G_easting_to_col(coordinate.easting, byref(window)) )
        #print("row: %d, col: %d\n" % (row, col) )
        
        # Get number of rows
        numRows = self.grass_lowlevel.G_window_rows()
        numCols = self.grass_lowlevel.G_window_cols()
        #print("num rows: %d, num cols: %d\n" % (numRows, numCols) )
        
        # Get patch ID
        patchID = self._getValueForCell(patchMap, row, col)
        #print("PatchID: %d\n" % (patchID,) )
        
        # Get zone ID
        zoneID = self._getValueForCell(zoneMap, row, col)
        #print("ZoneID: %d\n" % (zoneID,) )
        
        # Get hillslope ID
        hillID = self._getValueForCell(hillslopeMap, row, col)
        #print("HillID: %d\n" % (hillID,) )
        
#        os.environ['GIS_LOCK'] = ''
#        os.unlink(os.environ['GISRC'])
        
        return rhessystypes.FQPatchID(patchID=int(patchID), zoneID=int(zoneID), hillID=int(hillID))
    
    
    def _setupGrassScriptingEnvironment(self):
        """ @brief Set up GRASS environment for using GRASS scripting API from 
            Python (e.g. grass.script)
        """
        os.environ['GISBASE'] = self.grass_config.gisbase
        sys.path.append(os.path.join(self.grass_config.gisbase, 'etc', 'python'))
        import grass.script.setup as gsetup
        gsetup.init(self.grass_config.gisbase, \
                    self.grass_config.dbase, self.grass_config.location, \
                    self.grass_config.mapset)

        self.g = importlib.import_module('grass.script')
        return self.g
    
    def _setupGrassEnvironment(self):
        """ @brief Set up GRASS environment for using GRASS low-level API from 
            Python (e.g. grass.lib)
        """
        gisBase = self.grass_config.gisbase
        sys.path.append(os.path.join(gisBase, 'etc', 'python'))
        os.environ['LD_LIBRARY_PATH'] = os.path.join(gisBase, 'lib')
        os.environ['DYLD_LIBRARY_PATH'] = os.path.join(gisBase, 'lib')
        # Write grassrc
        os.environ['GISRC'] = self._initializeGrassrc()
        os.environ['GIS_LOCK'] = str(os.getpid())
        self.grass_lowlevel = importlib.import_module('grass.lib.gis')
        self.grass_lowlevel.G_gisinit('')
        return self.grass_lowlevel
    
    def _initializeGrassrc(self):
        grassRcFile = tempfile.NamedTemporaryFile(prefix='grassrc-', delete=False)
        grassRcContent = "GISDBASE: %s\nLOCATION_NAME: %s\nMAPSET: %s\n" % \
            (self.grass_config.dbase, self.grass_config.location, self.grass_config.mapset)
        grassRcFile.write(grassRcContent)
        return grassRcFile.name
    
    def _getValueForCell(self, input, row, col):
        mapset = self.grass_lowlevel.G_find_cell2(input, '')
        mapset = c_char_p(mapset).value
        data_type = self.grass_lowlevel.G_raster_map_type(input, mapset)
        if data_type == 0: 
            ptype = POINTER(c_int) 
        elif data_type == 1: 
            ptype = POINTER(c_float) 
        elif data_type == 2: 
            ptype = POINTER(c_double) 
        infd = self.grass_lowlevel.G_open_cell_old(input, mapset) 
        inrast = self.grass_lowlevel.G_allocate_raster_buf(data_type)     
        inrast = cast(c_void_p(inrast), ptype) 
        self.grass_lowlevel.G_get_raster_row(infd, inrast, row, data_type)
        value = inrast[col]
        self.grass_lowlevel.G_close_cell(infd)
        self.grass_lowlevel.G_free(inrast)
        
        return value
