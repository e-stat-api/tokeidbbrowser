#
#
#
#
#

import os
import sys
from urllib import urlencode
from urllib2 import urlopen, Request, URLError, HTTPError
from xml.etree.ElementTree import fromstring, tostring


def mkDataDir(path):
    if not os.path.isdir(path):
        os.mkdir(path)

class TokeiDB:
    """
    A Simple Tokei Database Interface
    """

    def __init__(self, dbhost=None, appid=None):
        self._dbhost = dbhost
        self._appid = appid
        self._method = None
        self._req = None
        self._xml = None
        self._status = False

    def status(self): return self._status
    def xmlobject(self): return self._xml
    def xmlstring(self): return tostring(self._xml, encoding='utf-8')

    def buildQuery(self, dbcmd, params, method='GET'):
        self._method = method
        url = 'http://%s/rest/1.0/app/%s?' % (self._dbhost, dbcmd)
        urlparams = {'appId': self._appid}
        urlparams.update(params)
        if method is 'GET':
            self._req = url + urlencode(urlparams)
        elif method is 'POST':
            self._req = Request(url, urlparams)

    def execute(self):
        res = None; fp = None; xml = None
        fp = urlopen(self._req)
        res = fp.read()
        if res:
            self._xml = fromstring(res)
            if self._xml is not None:
                self._status = True
        if fp:
            fp.close()
        return self._status
            
if __name__ == '__main__':
    from pprint import pprint
    tokeidb = TokeiDB('db.example.com', 'user01', 'pass01')
    tokeidb.buildQuery('dbcmd', {'a': 'a', 'b': 'b', 'c': 'c'})
    pprint(tokeidb._req)
    
