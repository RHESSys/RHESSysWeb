import os
import sys

metadata = {
    "grass_dbase" : "/home/ga/ga_cms/src/DR5/GRASSData",
    "grass_location" : "DR5",
    "grass_mapset" : "taehee",
}

grassDbase = metadata['grass_dbase']
os.environ['GISBASE'] = gisBase = "/usr/lib/grass64"
sys.path.append(os.path.join(gisBase, "etc", "python"))
import grass.script as grass
import grass.script.setup as gsetup
gsetup.init(gisBase, grassDbase, metadata['grass_location'], metadata['grass_mapset'])
