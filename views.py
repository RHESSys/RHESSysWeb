import json
from uuid import uuid4
from rhessystypes import FQPatchID
import flowtableio
import redis
from collections import OrderedDict
from django.http import HttpResponse
import cPickle
from mezzanine.pages.models import Page

def cache_patches_in_session(request, *args, **kwargs):
    flowtable = request.POST['flowtable']
    patch_id = int(request.POST['patch'])
    zone_id = int(request.POST['zone'])
    hill_id = int(request.POST['hill'])
    receivers = json.loads(request.POST['receivers'])

    print flowtable
    print patch_id
    print zone_id
    print hill_id
    print json.dumps(receivers, indent=4)


    fqpatch = FQPatchID(patch_id, zone_id, hill_id)

    if flowtable not in request.session:
        request.session[flowtable] = {}
    request.session[flowtable][fqpatch] = receivers
    return HttpResponse()


def save_flowtable(request, *args, **kwargs):
    flowtable = redis.Redis(db=15)
    flowtable_name = request.GET['flowtable']
    flowtable_new = "/tmp/" + uuid4().hex # request.POST['new_table']
    hashtable = flowtable_name + ".hash"
    N = flowtable.llen(flowtable_name)
    outflow = OrderedDict()
    for entry in flowtable.lrange(flowtable_name, 0, N):
        fqpatch = cPickle.loads(entry)

        if flowtable_name in request.session and fqpatch in request.session[flowtable_name]:
            outflow[fqpatch] = flowtableio.loadReceivers(request.session[flowtable_name])
        else:
            outflow[fqpatch] = flowtableio.loadReceivers(flowtable.hget(hashtable, entry))

    flowtableio.writeFlowtable(outflow, flowtable_new)
    rsp = HttpResponse(open(flowtable_new), mimetype='application/octet-stream')
    rsp['Content-Disposition'] = 'filename="flowtable.txt"'
    return rsp

def revert_flowtable(request, *args, **kwargs):
    flowtable = request.POST['flowtable']
    del request.session[flowtable]
    return HttpResponse()

def get_patch(request, *args, **kwargs):
    wherex = float(request.GET['x'])
    wherey = float(request.GET['y'])
    srs = request.GET['srs']
    from_table = request.GET['slug']
    p = Page.objects.get(slug=from_table)
    patch, hillslope, zone = p.dataresource.driver_instance.get_fqpatch(srs, wherex, wherey)
    return HttpResponse(json.dumps(dict(patchId=patch, hillId=hillslope, zoneId=zone)), mimetype='application/json')