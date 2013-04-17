import importlib
from django.conf import settings

class GrassSession(object):
    def __init__(self, dbase, location, mapset):
        self.g = importlib.import_module('grass.script')
        self._gsetup = importlib.import_module('grass.script.setup')
        self._gsetup.init(settings.GISBASE, dbase, location, mapset)

    def __enter__(self):
        return self.g

    def __exit__(self, exc_type, exc_val, exc_tb):
        return True

if __name__=='__main__':
    with GrassSession('/home/ga/ga_cms/src/DR5/GRASSData', "DR5", "taehee") as g:
        g.run_command('g.region', **{ 'n' : 4350605, 'w' : 349133, 'e' : 349659.5, 's' : 4350196 })
        g.run_command('r.out.tiff', flags='t', input='lulc_5m_roof', output='/tmp/out.tif')
        g.read_command('g.proj', flags='j')

