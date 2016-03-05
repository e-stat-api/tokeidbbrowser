# -*- mode:python; encoding:utf-8 -*-
# -*- coding:utf-8 -*-
#
# Interface for TokeiDB Web API
#
#

import os
import logging
import urllib
import urllib2
from xml.etree import ElementTree

from ConfigParser import ConfigParser


########################################################################
#
# Tokei DB Web API Interface
#
########################################################################

class TokeiDBProxy(object):
    def __init__(self, logger=None):
        self.config = self.readConfig()
        self.query = None
        self.logger = logger
        if 'pxhost' in self.config and 0 < len(self.config['pxhost']):
            proxy = {'http':'http://%s:%s/' % (self.config['pxhost'], self.config['pxport'])}
            proxy_handler = urllib2.ProxyHandler(proxy)
            opener = urllib2.build_opener(proxy_handler)
            urllib2.install_opener(opener)

    def logInfo(self, msg):
        if self.logger is not None:
            self.logger.info(msg)
            
    def logError(self, msg):
        if self.logger is not None:
            self.logger.error(msg)

    def readConfig(self):
        """ read some parameters from tokeidb.conf. The location of statdb.conf is defined in tokeidb.wsgi. """
        config = ConfigParser()
        files = config.read([os.environ['TOKEIDB_CONFIG_FILE']])
        params = {}
        if config.has_section('db'):
            params['dbhost'] = config.get('db', 'dbhost')
            params['appid'] = config.get('db', 'appid')
        if config.has_section('proxy'):
            params['pxhost'] = config.get('proxy', 'host')
            params['pxport'] = config.get('proxy', 'port')
        return params

    def doQuery(self, dbcmd, params):
        self.logger.info('doQuery(%s)' % dbcmd)
        query = None
        query = "http://%s/rest/1.0/app/%s?appId=%s" % (self.config['dbhost'], dbcmd, self.config['appid'])
        if 0 < len(params):
            query += "&" + urllib.urlencode(params)
        xml = None
        self.query = query
        self.logInfo(query)
        res = None
        try:
            res = urllib2.urlopen(query, timeout=60)
        except urllib2.HTTPError, e:
            if hasattr(e, 'code'):
                self.logError('Error code: %s' % e.code)
            if hasattr(e, 'reason'):
                self.logError('Error reason: %s' % e.reason)
            self.logError(e.read())
        except urllib2.URLError, e:
            if hasattr(e, 'code'):
                self.logError('Error code: %s' % e.code)
            if hasattr(e, 'reason'):
                self.logError('Error reason: %s' % e.reason)
            self.logError(e.read())
        else:
            if res is not None:
                xml = res.read()
                res.close()
        return xml

########################################################################
#
# Tokei DB Web API Response Object
#
########################################################################

class TokeiDBResponse(object):
    """Representation of Stat DB Return Value"""
    def __init__(self, xmlstring):
        root = ElementTree.XML(xmlstring)
        self._root = root # passing to the derived class
        #
        self._result = {}
        for elm in root.find('RESULT').getchildren():
            self._result[elm.tag] = self._xmlelement2dic(elm)
        #
        self._parameter = {}
        for elm in root.find('PARAMETER').getchildren():
            self._parameter[elm.tag] = self._xmlelement2dic(elm)
        # Check the transaction status
        if 'STATUS' in self._result:
            status = int(self.result('STATUS')['TEXT'])
            # transaction succeed, but something wrong
            if status < 0 or 100 < status:
                raise ValueError
        else:
            # maybe invalid xmlstring
            raise ValueError
        #
        
    def result(self, key): return self._result[key]
    def parameter(self, key): return self._parameter[key]

    def _xmlelement2dic(self, elm):
        """
        >>> elm = ElementTree.XML('<STAT_NAME code="00200521">国勢調査</STAT_NAME>'
        >>> _xmlelement2dic(elm)
        {'TEXT': u'国勢調査', 'ATTR': { 'code': "00200521" }}
        """
        return {'TEXT': elm.text, 'ATTR': elm.attrib}

# Result of getStatsList

class TokeiDBResponseStatsList(TokeiDBResponse):
    def __init__(self, xmlstring):
        TokeiDBResponse.__init__(self, xmlstring)
        #
        root = self._root.find('DATALIST_INF')
        self._datalist_inf = {}
        self._datalist_inf['NUMBER'] = int(root.find('NUMBER').text)
        self._datalist_inf['LIST_INF'] = []
        for list_inf in root.findall('LIST_INF'):
            tmpdic = {}
            # id は LIST_INF の attribute だが、ここでは tag として扱う
            tmpdic['ID'] = {'TEXT': list_inf.attrib['id'] }
            for elm in list_inf.getchildren():
                tmpdic[elm.tag] = self._xmlelement2dic(elm)
            self._datalist_inf['LIST_INF'].append(tmpdic)
        self._root = None

    def datalist_inf(self, key): return self._datalist_inf[key]
    def number(self): return self._datalist_inf['NUMBER']

# Result of getMetaInfo

class TokeiDBResponseMetaInfo(TokeiDBResponse):
    """
      <CLASS_OBJ id="Bun01" name="曜日">
        <CLASS code="002" name="平日" level="1"/>
        <CLASS code="009" name="土曜日" level="1"/>
        <CLASS code="016" name="日曜日" level="1"/>
      </CLASS_OBJ>

      {'id': 'Bun01', 'name': '曜日', 'CLASS': [{'code': '002', 'name': '平日' 'level': '1'}, .. }]}
    """
    def __init__(self, xmlstring):
        TokeiDBResponse.__init__(self, xmlstring)
        #
        root = self._root.find('METADATA_INF')
        self._metadata_inf = {}
        #
        table_inf = root.find('TABLE_INF')
        tmpdic = {}
        tmpdic['ID'] = {'TEXT': table_inf.attrib['id'] }
        for elm in table_inf.getchildren():
            tmpdic[elm.tag] = self._xmlelement2dic(elm)
        self._metadata_inf['TABLE_INF'] = tmpdic
        #
        self._metadata_inf['CLASS_INF'] = []
        for class_obj in root.find('CLASS_INF').findall('CLASS_OBJ'):
            tmpdic = {}
            tmpdic.update({'id': class_obj.attrib['id']})
            tmpdic.update({'name': class_obj.attrib['name']})
            tmplst = []
            for cls in class_obj.findall('CLASS'):
                tmpdic2 = {}
                for k, v in cls.attrib.iteritems():
                    tmpdic2.update({k: v})
                tmplst.append(tmpdic2)
            tmpdic.update({'CLASS': tmplst})
            self._metadata_inf['CLASS_INF'].append(tmpdic)
        #
        self._root = None

    def metadata_inf(self, key): return self._metadata_inf[key]

# Result of getStatsData

class TokeiDBResponseStatsData(TokeiDBResponse):
    def __init__(self, xmlstring, limit=0):
        #
        # limit means the upper limit of counting VALUE.
        # if limit is 0, count all VALUE
        #
        TokeiDBResponse.__init__(self, xmlstring)
        root = self._root.find('STATISTICAL_DATA')
        self._statistical_data = {}
        #
        table_inf = root.find('TABLE_INF')
        tmpdic = {}
        tmpdic['ID'] = {'TEXT': table_inf.attrib['id'] }
        for elm in table_inf.getchildren():
            tmpdic[elm.tag] = self._xmlelement2dic(elm)
        self._statistical_data['TABLE_INF'] = tmpdic
        #
        self._statistical_data['CLASS_INF'] = []
        for class_obj in root.find('CLASS_INF').findall('CLASS_OBJ'):
            tmpdic = {}
            tmpdic.update({'id': class_obj.attrib['id']})
            tmpdic.update({'name': class_obj.attrib['name']})
            tmplst = []
            for cls in class_obj.findall('CLASS'):
                tmpdic2 = {}
                for k, v in cls.attrib.iteritems():
                    tmpdic2.update({k: v})
                tmplst.append(tmpdic2)
            tmpdic.update({'CLASS': tmplst})
            self._statistical_data['CLASS_INF'].append(tmpdic)
         #
        self._statistical_data['DATA_INF'] = {}
        tmplst = []
        # illegal data, maybe nothing found.
        if root.find('DATA_INF') is None:
            return
        for note in root.find('DATA_INF').findall('NOTE'):
            tmplst.append(self._xmlelement2dic(note))
        self._statistical_data['DATA_INF'].update({'NOTE': tmplst})
        tmplst = []
        count = 0
        for value in root.find('DATA_INF').findall('VALUE'):
            tmplst.append(self._xmlelement2dic(value))
            count += 1
            if limit != 0 and limit< count:
                break
        self._statistical_data['DATA_INF'].update({'VALUE': tmplst})
        #
        self._root = None

    def statistical_data(self, key): return self._statistical_data[key]

#
# end of code
#

if __name__ == '__main__':

    import unittest

    class TokeiDBResponseTest(unittest.TestCase):

        def setUp(self):
            """read tesdata"""
            self.statslistxml = None
            with open('testdata/statslist.xml', 'r') as fp:
                self.statslistxml = fp.read()
                
            self.metainfoxml = None
            with open('testdata/metainfo.xml', 'r') as fp:
                self.metainfoxml = fp.read()

            self.statsdataxml = None
            with open('testdata/statsdata.xml', 'r') as fp:
                self.statsdataxml = fp.read()

        def testGetStatsList(self):
            res = TokeiDBResponseStatsList(self.statslistxml)
            #
            tmp = res.result('STAT')
            self.assertEqual(tmp['TEXT'], '0')
            tmp = res.result('DATE')
            self.assertEqual(tmp['TEXT'], '2011-11-11T18:01:16.329+09:00')
            #
            tmp = res.datalist_inf('NUMBER')
            self.assertEqual(tmp, 10)
            #
            tmp = res.datalist_inf('LIST_INF')[0]
            self.assertEqual(tmp['ID']['TEXT'], 'T00005001')
            self.assertEqual(tmp['STAT_NAME']['TEXT'], u'国勢調査')
            self.assertEqual(tmp['STAT_NAME']['ATTR']['code'], '00200521')

        def testGetMetaInfo(self):
            res = TokeiDBResponseMetaInfo(self.metainfoxml)
            #
            tmp = res.result('STATUS')
            self.assertEqual(tmp['TEXT'], '0')
            tmp = res.result('DATE')
            self.assertEqual(tmp['TEXT'], '2011-11-15T10:09:26.902+09:00')
            #
            tmp = res.metadata_inf('TABLE_INF')
            self.assertEqual(tmp['ID']['TEXT'], '0003002433')
            self.assertEqual(tmp['STAT_NAME']['TEXT'], u'社会生活基本調査')
            self.assertEqual(tmp['STAT_NAME']['ATTR']['code'], '00200533')
            self.assertEqual(tmp['STATISTICS_NAME']['TEXT'], u'平成18年社会生活基本調査 調査票Aに基づく結果 ・・・')
            #
            tmp = res.metadata_inf('CLASS_INF')[0]
            self.assertEqual(tmp['id'], 'Hyo')
            self.assertEqual(tmp['name'], u'表章項目')
            self.assertEqual(tmp['CLASS'][0]['code'], '008')
            self.assertEqual(tmp['CLASS'][0]['name'], u'行動者数')
            self.assertEqual(tmp['CLASS'][0]['unit'], u'千人')
            #
            tmp = res.metadata_inf('CLASS_INF')[1]
            self.assertEqual(tmp['id'], 'Bun01')
            self.assertEqual(tmp['name'], u'曜日')
            self.assertEqual(tmp['CLASS'][0]['code'], '002')
            self.assertEqual(tmp['CLASS'][0]['name'], u'平日')
            self.assertEqual(tmp['CLASS'][0]['level'], u'1')
            self.assertEqual(tmp['CLASS'][1]['code'], '009')
            self.assertEqual(tmp['CLASS'][1]['name'], u'土曜日')
            self.assertEqual(tmp['CLASS'][1]['level'], u'1')
            self.assertEqual(tmp['CLASS'][2]['code'], '016')
            self.assertEqual(tmp['CLASS'][2]['name'], u'日曜日')
            self.assertEqual(tmp['CLASS'][2]['level'], u'1')
        #
        def testGetStatsData(self):
            res = TokeiDBResponseStatsData(self.statsdataxml)
            #
            tmp = res.result('STATUS')
            self.assertEqual(tmp['TEXT'], '0')
            tmp = res.result('DATE')
            self.assertEqual(tmp['TEXT'], '2012-02-11T20:48:50.988+09:00')
            #
            tmp = res.statistical_data('TABLE_INF')
            self.assertEqual(tmp['ID']['TEXT'], '0003033222')
            self.assertEqual(tmp['STAT_NAME']['TEXT'], u'サービス産業動向調査')
            self.assertEqual(tmp['STAT_NAME']['ATTR']['code'], '00200544')
            self.assertEqual(tmp['STATISTICS_NAME']['TEXT'], u'サービス産業動向調査')
            self.assertEqual(tmp['TITLE']['TEXT'], u'産業（表章分類）別売上高（収入額）および事業従事者数')
            #
            tmp = res.statistical_data('CLASS_INF')[0]
            self.assertEqual(tmp['id'], 'Hyo')
            self.assertEqual(tmp['name'], u'表章項目')
            self.assertEqual(tmp['CLASS'][0]['code'], '001')
            self.assertEqual(tmp['CLASS'][0]['name'], u'売上高（収入額）')
            self.assertEqual(tmp['CLASS'][0]['unit'], u'百万円')
            #
            tmp = res.statistical_data('DATA_INF')
            self.assertEqual(tmp['NOTE'][0]['TEXT'], u'短縮したもの')
            self.assertEqual(tmp['VALUE'][0]['TEXT'], '290,535,703')
            self.assertEqual(tmp['VALUE'][0]['ATTR']['hyo'], '001')
            self.assertEqual(tmp['VALUE'][0]['ATTR']['bun01'], '00000')

        def testTokeiDBProxy(self):
            os.environ['TOKEIDB_CONFIG_FILE'] = '/var/www/tokeidb/etc/tokeidb.conf'
            dbproxy = TokeiDBProxy()
            xml = dbproxy.doQuery('getStatsList', {'statsCode': '00200573', 'openYears': '2011'})
            if xml:
                res = TokeiDBResponseStatsList(xml)
                print 'We got %d data.' % res.number()
            else:
                print 'We got no data.'

    unittest.main()

