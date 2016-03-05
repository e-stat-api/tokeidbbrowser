# -*- coding:utf-8 -*-
#
# 統計ごとにどれくらいの表があるのか
#
# 2012.06.20 Form ではなくA を出力する版
# 2015.01.14 New API Server
# 2016.02.29 searchKind を付与
#

import os
import sys

from urllib2 import URLError, HTTPError
from xml.etree.ElementTree import fromstring, tostring


output = "tokeilisttable.html"

def printMsg(msg):
    sys.stdout.write(msg)
    sys.stdout.flush()

from lib.tokeidblib import TokeiDB

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print 'Usage: %s dbhost appid\n' % sys.argv[0]
        sys.exit(1)

    dbhost = sys.argv[1]
    appid = sys.argv[2]
    #urlprefix =  sys.argv[3]

    db = TokeiDB(dbhost=dbhost, appid=appid)

    with open('data/SeifuTokeiId.data', 'r') as fp:
        lines = fp.readlines()

    with open(output, "w") as fp:

        fp.write('''
<table class="table table-bordered table-striped table-condensed">
 <thead>
  <tr>
   <th style="width:20em;">政府統計名<br />(政府統計コード)</th>
   <th>調査年度(上段)/公開年度(下段) ()内は表数</th>
  </tr>
 </thead>
 <tbody>\n''')
        for line in lines:
            searchkind, lclass, sclass, code, name, org = line.split()
            #
            printMsg('Retrieving stats list with code (%s) ...' % code)
            for yeartype in ['surveyYears', 'openYears']:  # 調査年度, 公開年度
                # 
                if yeartype == 'surveyYears':
                    fp.write('  <tr><td rowspan="2">%s<br />(%s)</td><td>' % (name, code))
                else:
                    fp.write('  <tr><td>')
                for year in range(1990, 2017, 1):
                    printMsg(' %s,' % year)
                    params = {}
                    params[yeartype] = year
                    params['statsCode'] = code
                    params['searchKind'] = searchkind
                    db.buildQuery('getStatsList', params)
                    try:
                        db.execute()
                        xmlobj = db.xmlobject()
                        num_of_records = int(xmlobj.find('DATALIST_INF').find('NUMBER').text)
                        if 0 < num_of_records:
                            fp.write('''
    <a href="getStatsList?statsCode=%s&%s=%s&searchKind=%s">
    <button class="btn btn-success" style="float:left;margin:3px">%s(%d)</button>
                            </a>''' % (code, yeartype, year, searchkind, year, num_of_records))
                    except URLError, e:
                        printMsg('Exception(%s), abort.\n' % e)
                        sys.exit(1)
                    except HTTPError, e:
                        printMsg('Exception(%s), abort.\n' % e)
                        sys.exit(1)
                fp.write("&nbsp;</td></tr>\n")
            print ''
        fp.write("</tbody></table>\n")

#
# Local variables:
# mode: python
# end:
#
