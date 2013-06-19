SITE_APPS = ('RHESSysWeb',)
DEBUG = True

import os 
import sys

os.environ['GISBASE'] = GISBASE = '/usr/lib/grass64'
sys.path.append(os.path.join(GISBASE, 'etc','python')) 
