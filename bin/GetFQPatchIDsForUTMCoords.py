#!/usr/bin/env python
"""@package GetFQPatchIDsForUTMCoords.py

@brief Get fully qualified RHESSys patch ID (see rhessystypes.FQPatchID) for
       a list of coordinates from RHESSeys patch, zone, hillsope raster maps
       stored in a GRASS mapset.  Coordinates are assumed to be WGS84 and will
       transformed to the coordinate system of the GRASS mapset.

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
    * Neither the name of the University of North Carolina at Chapel
      Hill nor the names of its contributors may be used to endorse or
      promote products derived from this software without specific
      prior written permission.

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

Usage
@code
GetFQPatchIDsForUTMCoords.py -g <GRASSData> -l <location> -m <mapset> -p <patchmap> -z <zonemap> -i <hillslope> -c <coordinate file>
@endcode
"""
import os
import sys
import errno

from osgeo import osr

import rhessystypes
from grassdatalookup import getSpatialReferenceForGRASSDataset
from grassdatalookup import getFQPatchIDForCoordinates
from grassdatalookup import GRASSConfig

SEP = ','

if sys.hexversion < 0x02700000:
    # Pre Python 2.7
    from optparse import OptionParser
    parser = OptionParser(usage='Read fully qualified RHESSys patch IDs (combination of patchID, zoneID, and hillID) for a list of UTM coordinates')
    parser.add_option('-g', '--grassdbase', dest='grassdbase',
                        help='The path to the GRASS database')
    parser.add_option('-l', '--location', dest='location', 
                        help='The location of GRASS mapset')
    parser.add_option('-m', '--mapset', dest='mapset', 
                        help='The GRASS mapset')
    parser.add_option('-p', '--patchmap', dest='patchmap', 
                        help='The name of the GRASS raster to use for the patch map')
    parser.add_option('-z', '--zonemap', dest='zonemap', 
                        help='The name of the GRASS raster to use for the zone map')
    parser.add_option('-i', '--hillmap', dest='hillmap', 
                        help='The name of the GRASS raster to use for the hill map')
    parser.add_option('-c', '--coordinates', dest='coordinates', 
                        help='The path to comma separated file containing easting,northing coordinates in UTM18N NAD83 spatial reference system.  Will skip the first line in the file.')
    (args, args_args) = parser.parse_args()
else:
    # Python 2.7 or later
    import argparse
    parser = argparse.ArgumentParser(description='Read fully qualified RHESSys patch IDs (combination of patchID, zoneID, and hillID) for a list of UTM coordinates')
    parser.add_argument('-g', '--grassdbase', dest='grassdbase', required=True,
                        help='The path to the GRASS database')
    parser.add_argument('-l', '--location', dest='location', required=True,
                        help='The location of GRASS mapset')
    parser.add_argument('-m', '--mapset', dest='mapset', required=True,
                        help='The GRASS mapset')
    parser.add_argument('-p', '--patchmap', dest='patchmap', required=True,
                        help='The name of the GRASS raster to use for the patch map')
    parser.add_argument('-z', '--zonemap', dest='zonemap', required=True,
                        help='The name of the GRASS raster to use for the zone map')
    parser.add_argument('-h', '--hillmap', dest='hillmap', required=True,
                        help='The name of the GRASS raster to use for the hill map')
    parser.add_argument('-c', '--coordinates', dest='coordinates', required=True,
                        help='The path to comma separated file containing easting,northing coordinates in UTM18N NAD83 spatial reference system.  Will skip the first line in the file.')
    args = parser.parse_args()

if not os.access(args.coordinates, os.R_OK):
    raise IOError(errno.EACCES, "Unable to read coordinate file %d" % \
                  (args.coordinates,) )

gisbase = os.environ['GISBASE']

if not os.access(args.grassdbase, os.R_OK):
    raise IOError(errno.EACCES, "Unable to read grassdbase path %d" % \
                  (args.grassdbase,) )
grassdbase = os.path.abspath(args.grassdbase)

grassConfig = GRASSConfig(gisbase=gisbase, dbase=grassdbase, location=args.location, mapset=args.mapset)

t_srs = getSpatialReferenceForGRASSDataset(grassConfig)
s_srs = osr.SpatialReference()
s_srs.ImportFromEPSG(4326)
crx = osr.CoordinateTransformation(s_srs, t_srs)

sys.stdout.write("lat%slon%seasting%snorthing%spatchID%szoneID%shillID\n" % (SEP, SEP, SEP, SEP, SEP, SEP) )
f = open(args.coordinates, 'r')
f.next() # skip first line
for line in f:
    line = line.strip()
    values = line.split(',')
    lat = float(values[0])
    lon = float(values[1])
    # Transform coordinates from WGS84 to the coordinate system of the
    # GRASS mapset
    (x, y, z) = crx.TransformPoint( lon, lat )

    # Lookup patchID for transformed coordinates
    coord = rhessystypes.getCoordinatePair(x, y)
    id = getFQPatchIDForCoordinates(coord, grassConfig,
                                    args.patchmap, args.zonemap, args.hillmap)
    
    sys.stdout.write("%f%s%f%s%f%s%f%s%d%s%d%s%d\n" % (lat, SEP, lon, SEP, coord.easting, SEP, coord.northing, SEP, id.patchID, SEP, id.zoneID, SEP, id.hillID) )


