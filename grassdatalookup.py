"""@package rhessysweb.grassdatalookup

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
from ctypes import *

import RHESSysWeb.types

GRASSConfig = namedtuple('GRASSConfig', ['gisbase', 'dbase', 'location', 'mapset'], verbose=False)


def getCoordinatesForFQPatchIDs(fqPatchIDs, grassConfig, patchMap, zoneMap, hillslopeMap):
    """ @brief Get the geographic coordinates for a list of patches identified by
        their fully qualified patch ID. The fully qualified patch ID is the combination 
        of the patchID, zoneID, and hillslopeID.
    
        @param List of rhessysweb.types.FQPatchID objects representing a fully qualified 
        patch ID
        @param grassConfig GRASSConfig specifying the GRASS mapset that contains 
        the patch, zone, and hillslope maps
        @param patchMap String representing the name of the patch map
        @param zoneMap String representing the name of the zone map 
        @param hillslopeMap String representing the name of the hillslope map
        
        @return List of rhessysweb.types.CoordinatePair objects
        
        @todo Handle non-grid patches, return the coordinates of their centroid
    """
    coords = list()
    
    # Set up GRASS environment
    _setupGrassEnvironment(grassConfig)
    from grass.lib import gis as grass
    grass.G_gisinit('')
    
    # Get the window so we can conver row,col to easting,northing
    window = grass.Cell_head()
    grass.G_get_window(byref(window))
    numRows = grass.G_window_rows()
    numCols = grass.G_window_cols()
    
    # Open patch map
    patch = grass.G_find_cell2(patchMap, '')
    patch = c_char_p(patch).value
    patchType = grass.G_raster_map_type(patchMap, patch)
    if patchType == 0: 
        ptype = POINTER(c_int) 
    elif patchType == 1: 
        ptype = POINTER(c_float) 
    elif patchType == 2: 
        ptype = POINTER(c_double) 
    patchFd = grass.G_open_cell_old(patchMap, patch) 
    patchRast = grass.G_allocate_raster_buf(patchType)     
    patchRast = cast(c_void_p(patchRast), ptype) 
    
    # Open zone map
    zone = grass.G_find_cell2(zoneMap, '')
    zone = c_char_p(zone).value
    zoneType = grass.G_raster_map_type(zoneMap, zone)
    if zoneType == 0: 
        ptype = POINTER(c_int) 
    elif zoneType == 1: 
        ptype = POINTER(c_float) 
    elif zoneType == 2: 
        ptype = POINTER(c_double) 
    zoneFd = grass.G_open_cell_old(zoneMap, zone) 
    zoneRast = grass.G_allocate_raster_buf(zoneType)     
    zoneRast = cast(c_void_p(zoneRast), ptype) 
    
    # Open hill map
    hill = grass.G_find_cell2(hillslopeMap, '')
    hill = c_char_p(hill).value
    hillType = grass.G_raster_map_type(hillslopeMap, hill)
    if hillType == 0: 
        ptype = POINTER(c_int) 
    elif hillType == 1: 
        ptype = POINTER(c_float) 
    elif hillType == 2: 
        ptype = POINTER(c_double) 
    hillFd = grass.G_open_cell_old(hillslopeMap, hill) 
    hillRast = grass.G_allocate_raster_buf(hillType)     
    hillRast = cast(c_void_p(hillRast), ptype) 
     
    for row in range(numRows):
        # Get current row for each dataset
        grass.G_get_raster_row(patchFd, patchRast, row, patchType)
        grass.G_get_raster_row(zoneFd, zoneRast, row, zoneType)
        grass.G_get_raster_row(hillFd, hillRast, row, hillType)
    
        for col in range(numCols):
            for fqPatchID in fqPatchIDs:
                if patchRast[col] == fqPatchID.patchID and \
                    zoneRast[col] == fqPatchID.zoneID and \
                    hillRast[col] == fqPatchID.hillID:
                    # Match found, get its coordinates
                    easting = grass.G_col_to_easting(col + 0.5, byref(window))
                    northing = grass.G_row_to_northing(row + 0.5, byref(window))
                    coords.append(RHESSysWeb.types.getCoordinatePair(easting, northing))
    
    # Clean up
    grass.G_close_cell(patchFd)
    grass.G_free(patchRast)
    grass.G_close_cell(zoneFd)
    grass.G_free(zoneRast)
    grass.G_close_cell(hillFd)
    grass.G_free(hillRast)
    
    os.environ['GIS_LOCK'] = ''
    os.unlink(os.environ['GISRC'])
    
    return coords


def getFQPatchIDForCoordinates(easting, northing, grassConfig, patchMap, zoneMap, hillslopeMap):
    """ @brief Get the fully qualified ID of the patch located at a coordinate pair.
        The fully qualified patch ID is the combination of the patchID, zoneID,
        and hillslopeID.
    
        @param easting Float represting the easting coordinate
        @param northing Float representing the northing coordinate
        @param grassConfig GRASSConfig specifying the GRASS mapset that contains 
        the patch, zone, and hillslope maps
        @param patchMap String representing the name of the patch map
        @param zoneMap String representing the name of the zone map 
        @param hillslopeMap String representing the name of the hillslope map
        
        @return Tuple (patchID, zoneID, hillID)
    """
    patchID = None
    zoneID = None
    hillID = None
    
    # Set up GRASS environment
    _setupGrassEnvironment(grassConfig)
    from grass.lib import gis as grass
    grass.G_gisinit('')
    
    # Translate coordinates to row, col
    window = grass.Cell_head()
    grass.G_get_window(byref(window))
    row = int( grass.G_northing_to_row(northing, byref(window)) )
    col = int( grass.G_easting_to_col(easting, byref(window)) )
    #print("row: %d, col: %d\n" % (row, col) )
    
    # Get number of rows
    numRows = grass.G_window_rows()
    numCols = grass.G_window_cols()
    #print("num rows: %d, num cols: %d\n" % (numRows, numCols) )
    
    # Get patch ID
    patchID = _getValueForCell(patchMap, row, col)
    #print("PatchID: %d\n" % (patchID,) )
    
    # Get zone ID
    zoneID = _getValueForCell(zoneMap, row, col)
    #print("ZoneID: %d\n" % (zoneID,) )
    
    # Get hillslope ID
    hillID = _getValueForCell(hillslopeMap, row, col)
    #print("HillID: %d\n" % (hillID,) )
    
    os.environ['GIS_LOCK'] = ''
    os.unlink(os.environ['GISRC'])
    
    return (patchID, zoneID, hillID)


def _setupGrassEnvironment(grassConfig):
    ## Set up GRASS environment
    gisBase = grassConfig.gisbase
    sys.path.append(os.path.join(gisBase, 'etc', 'python'))
    os.environ['LD_LIBRARY_PATH'] = os.path.join(gisBase, 'lib')
    os.environ['DYLD_LIBRARY_PATH'] = os.path.join(gisBase, 'lib')
    # Write grassrc
    os.environ['GISRC'] = _initializeGrassrc(grassConfig)
    os.environ['GIS_LOCK'] = str(os.getpid()) 

def _initializeGrassrc(grassConfig):
    grassRcFile = tempfile.NamedTemporaryFile(prefix='grassrc-', delete=False)
    grassRcContent = "GISDBASE: %s\nLOCATION_NAME: %s\nMAPSET: %s\n" % \
        (grassConfig.dbase, grassConfig.location, grassConfig.mapset)
    grassRcFile.write(grassRcContent)
    return grassRcFile.name

def _getValueForCell(input, row, col):
    from grass.lib import gis as grass
    mapset = grass.G_find_cell2(input, '')
    mapset = c_char_p(mapset).value
    data_type = grass.G_raster_map_type(input, mapset)
    if data_type == 0: 
        ptype = POINTER(c_int) 
    elif data_type == 1: 
        ptype = POINTER(c_float) 
    elif data_type == 2: 
        ptype = POINTER(c_double) 
    infd = grass.G_open_cell_old(input, mapset) 
    inrast = grass.G_allocate_raster_buf(data_type)     
    inrast = cast(c_void_p(inrast), ptype) 
    grass.G_get_raster_row(infd, inrast, row, data_type)
    value = inrast[col]
    grass.G_close_cell(infd)
    grass.G_free(inrast)
    
    return value