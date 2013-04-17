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

GRASSConfig = namedtuple('GRASSConfig', ['gisbase', 'dbase', 'location', 'mapset'], verbose=False)

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
    """
    patchID = None
    zoneID = None
    hillID = None
    
    ## Set up GRASS environment
    gisBase = grassConfig.gisbase
    sys.path.append(os.path.join(gisBase, 'etc', 'python'))
    os.environ['LD_LIBRARY_PATH'] = os.path.join(gisBase, 'lib')
    os.environ['DYLD_LIBRARY_PATH'] = os.path.join(gisBase, 'lib')
    # Write grassrc
    os.environ['GISRC'] = _initializeGrassrc(grassConfig)
    os.environ['GIS_LOCK'] = str(os.getpid())  
    from grass.lib import gis as grass
    grass.G_gisinit('')
    
    window = grass.Cell_head()
    grass.G_get_window(byref(window))
    
    # Translate coordinates to row, col
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