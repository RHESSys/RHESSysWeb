# coding: utf-8

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
import grass 
import grass.script as g
import grass.script.setup as gsetup

gsetup.init(gisBase, grassDbase, metadata['grass_location'], metadata['grass_mapset'])

g.run_command('g.region', **{ 'n' : 4350605, 'w' : 349133, 'e' : 349659.5, 's' : 4350196 })
g.run_command('r.out.tiff', flags='t', input='lulc_5m_roof', output='/tmp/out.tif')
g.read_command('g.proj', flags='j')
