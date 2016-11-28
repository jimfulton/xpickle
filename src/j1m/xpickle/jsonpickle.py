import binascii
import json
import datetime
from cStringIO import StringIO

from . import base

class Persistent(object):

    def __init__(self, id):
        if isinstance(id, Get):
            id = id.v

        if isinstance(id, (str, Bytes)):
            id = binascii.b2a_hex(str(id))
        else:
            assert (len(id) == 2 and
                    isinstance(id[0], (Bytes, str)) and
                    isinstance(id[1], Global))
            id = binascii.b2a_hex(str(id[0])), id[1].name
        self.id = id

    def json_reduce(self):
        return {'::': 'persistent', 'id': self.id}

class Global(object):

    def __init__(self, module, name):
        self.name = module + '.' + name

    def json_reduce(self):
        return {'::': 'global', 'name': self.name}

class Instance(object):

    id = None

    def __init__(self, global_, args):
        self.class_name = global_.name
        self.args = args

    def __setstate__(self, state):
        self.state = state

    def json_reduce(self):
        try:
            state = self.state
        except AttributeError:
            state = {}

        if not isinstance(state, dict):
            state = dict(state=state)

        state['::'] = self.class_name
        if self.args:
            state['__class_args__'] = self.args
        if self.id is not None:
            state['__ref_id__'] = self.args

        return state

class Bytes(object):

    def __init__(self, data):
        self.data = data

    def __str__(self):
        return self.data

    def json_reduce(self):
        return {'::': 'hex', 'hex': binascii.b2a_hex(self.data)}

class Get(object):

    def __init__(self, id, v):
        self.id = id
        self.v = v

    def __str__(self):
        return str(self.v)

    def __unicode__(self):
        return unicode(self.v)

    def json_reduce(self):
        return {'::': 'ref', 'id': self.id}

class Put(Get):

    got = False

    def extend(self, seq):
        self.v.extend(seq)

    def __setstate__(self, state):
        self.v.__setstate__(state)

    def __setitem__(self, k, v):
        k = unicode(k)
        self.v[k] = v

    def append(self, i):
        self.v.append(i)

    def json_reduce(self):
        v = self.v
        if self.got:
            if isinstance(v, Instance):
                v.id = self.id
            else:
                v = {'::': 'shared', 'id': self.id, 'value': v}
        return v


dt_classes = {'datetime.datetime': datetime.datetime,
              'datetime.date': datetime.date,
              }

def dt(class_name, args):
    return dt_classes[class_name](str(args[0])).isoformat()

special_classes = {
    'datetime.datetime': dt,
    'datetime.date': dt,
    }

basic_types = float, int, long, str, unicode, tuple, Global, Bytes

def default(ob):
    return ob.json_reduce()

class JsonUnpickler(base.XUnpickler):

    _x_Persistent = Persistent
    _x_Global = Global
    _x_Instance = Instance

    def _x_Put(self, id, v):
        if isinstance(v, basic_types):
            return v
        else:
            return Put(id, v)

    def _x_Get(self, id, v):
        if isinstance(v, basic_types):
            return v
        else:
            v.got = True
            return Get(id, v.v)

    def _x_String(self, v):
        try:
            v.decode('ascii')
        except UnicodeDecodeError:
            return Bytes(v)
        else:
            return v

    def _x_Instance(self, global_, args):
        if isinstance(global_, (Get, Put)):
            global_ = global_.v
        name = getattr(global_, 'name', global_)
        if name in special_classes:
            return special_classes[name](name, args)

        return Instance(global_, args)

    def _x_load(self, data):
        return json.dumps(data, default=default)

def record(pickle):
    unpickler = JsonUnpickler(StringIO(pickle))
    return unpickler.load(), unpickler.load()
