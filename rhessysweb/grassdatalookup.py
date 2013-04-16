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
from collections import namedtuple

GRASSMapset = namedtuple('GRASSMapset', ['dbase', 'location', 'mapset'], verbose=False)

def getFQPatchIDForCoordinates(easting, northing, grassMapset, patchMap, zoneMap, hillslopeMap):
    """ @brief Get the fully qualified ID of the patch located at a coordinate pair.
        The fully qualified patch ID is the combination of the patchID, zoneID,
        and hillslopeID.
    
        @param easting Float represting the easting coordinate
        @param northing Float representing the northing coordinate
        @param grassMapset GRASSMapset specifying the GRASS mapset that contains 
        the patch, zone, and hillslope maps
        @param patchMap String representing the name of the patch map
        @param zoneMap String representing the name of the zone map 
        @param hillslopeMap String representing the name of the hillslope map
    """
    patchID = None
    zoneID = None
    hillID = None
    
    return (patchID, zoneID, hillID)