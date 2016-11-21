##############################################################################
#
# Copyright (c) Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
from cStringIO import StringIO
import datetime
import json
import pickle
from pprint import pprint
import unittest
import ZODB
from ZODB.utils import z64, p64, maxtid


class initful(object):

    def __init__(self, *args):
        self.args = args

    def __reduce__(self):
        return self.__class__, self.args, self.__dict__

class JsonUnpicklerTests(unittest.TestCase):

    def test_basics(self):
        db = ZODB.DB(None)
        conn = db.open()
        root = conn.root

        root.numbers = 0, 123456789, 1 << 70, 1234.56789
        root.time = datetime.datetime(2001, 2, 3, 4, 5, 6, 7)
        root.date = datetime.datetime(2001, 2, 3)
        root.delta = datetime.timedelta(1, 2, 3)
        root.name = u'root'
        root.data = b'\xff'
        root.list = [1, 2, 3, root.name, root.numbers]
        root.list.append(root.list)
        root.first = conn.root().__class__()
        conn.transaction_manager.commit()

        p, _, _ = db.storage.loadBefore(z64, maxtid)
        from ..jsonpickle import JsonUnpickler
        unpickler = JsonUnpickler(StringIO(p))
        self.assertEqual(
            json.loads(unpickler.load()),
            {"name": "persistent.mapping.PersistentMapping", "::": "global"})
        self.assertEqual(
            json.loads(unpickler.load()),
            {u'data':
              {u'data': {u'::': u'hex', u'hex': u'ff'},
               u'date': u'2001-02-03T00:00:00',
               u'delta': {u'::': u'datetime.timedelta',
                          u'__class_args__': [1, 2, 3]},
               u'first': {u'::': u'persistent',
                          u'id': [u'0000000000000001',
                                  u'persistent.mapping.PersistentMapping']},
               u'list': {u'::': u'shared',
                         u'id': u'12',
                         u'value': [1,
                                    2,
                                    3,
                                    u'root',
                                    {u'::': u'shared',
                                     u'id': u'13',
                                     u'value': [0,
                                                123456789,
                                                1180591620717411303424L,
                                                1234.56789]},
                                    {u'::': u'ref', u'id': u'12'}]},
               u'name': u'root',
               u'numbers': {u'::': u'ref', u'id': u'13'},
               u'time': u'2001-02-03T04:05:06.000007'}}
            )
        db.close()

def test_suite():
    return unittest.makeSuite(JsonUnpicklerTests)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

