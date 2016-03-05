# -*- coding:utf-8 -*-
#
# Interface for TokeiDB Web API
#

import datetime
import re
import os
from ConfigParser import ConfigParser
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from logging import FileHandler, Formatter, INFO, WARNING, ERROR, CRITICAL
from lib import TokeiDBProxy, TokeiDBResponseStatsList, TokeiDBResponseMetaInfo, TokeiDBResponseStatsData

app = Flask(__name__)
app.config.from_object(__name__)

########################################################################
#
# log configuration
#
########################################################################

config = ConfigParser()
files = config.read([os.environ['TOKEIDB_CONFIG_FILE']])

if config.has_section('log'):
    logfile = config.get('log', 'logfile')
    loglevel = config.get('log', 'loglevel')

    loghandler = FileHandler(logfile, encoding='utf-8')
    loghandler.setFormatter(Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    app.logger.addHandler(loghandler)
    if loglevel == 'INFO':
        app.logger.setLevel(INFO)
    elif loglevel == 'WARNING':
        app.logger.setLevel(WARNING)
    elif loglevel == 'ERROR':
        app.logger.setLevel(ERROR)
    else:
        app.logger.setLevel(CRITICAL)
    app.logger.info('started')

########################################################################
#
# top page
#
########################################################################

@app.route('/')
def index():
    return render_template('getStatsListWithTableForm.html')

@app.route('/getStatsListWithTableForm')
def showGetStatsListWithTableForm():
    return render_template('getStatsListWithTableForm.html')

########################################################################
#
# very simple form validaton.
#
########################################################################

def checkFormVariable(request, key, regexp, required=False):
    retval = False
    if request.args.get(key):
        val = request.args.get(key)
        if re.match(regexp, val):
            retval = True
        else:
            retval = False
    else:
        if required:
            retval = False
        else:
            retval = True
    return retval

########################################################################
#
# getStatsList
#
########################################################################

@app.route('/getStatsList', methods=['GET'])
def showStatsList():
    #
    is_valid = True
    params = {}
    for cond in [ {'key': 'statsCode', 'regexp': '^\d{8}$', 'required': True},
                  {'key': 'surveyYears', 'regexp': '^$|^\d{4}$|^\d{6}$|^\d{6}-\d{6}$', 'required': False},
                  {'key': 'openYears', 'regexp': '^$|^\d{4}$|^\d{6}$|^\d{6}-\d{6}$', 'required': False},
                  {'key': 'searchKind', 'regexp': '^$|^\d{1}$', 'required': False} ] :
        if checkFormVariable(request, cond['key'], cond['regexp'], cond['required']):
            if request.args.get(cond['key']) is not None:
                params[cond['key']] = request.args.get(cond['key'])
        else:
            app.logger.info('invalid key found.');
            is_valid = False
            break
    #        
    if is_valid:
        dbproxy = TokeiDBProxy(app.logger)
        try:
            xml = dbproxy.doQuery('getStatsList', params)
        except Exception, e:
            app.logger.error('doQuery() failed, %s' % e)
            flash('database transaction failed.')
            return abort(500)
        if xml:
            try:
                res = TokeiDBResponseStatsList(xml)
            except ValueError:
                flash('database return value was wrong.')
                return abort(500)
            result = {}
            result['STATUS'] = int(res.result('STATUS')['TEXT'])
            result['ERROR_MSG'] = res.result('ERROR_MSG')['TEXT']
            result['NUMBER'] = res.datalist_inf('NUMBER')
            result['LIST_INF'] = res.datalist_inf('LIST_INF')
        else:
            res = None
            result = None
        return render_template('getStatsList.html', result=result)
    else:
        app.logger.info('validation error.')
        flash('validation error.')
        return abort(500)

########################################################################
#
# getMetaInfo
#
########################################################################

@app.route('/getMetaInfo', methods=['GET'])
def showMetaInfo():
    #
    is_valid = True
    params = {}
    for cond in [ {'key': 'statsDataId', 'regexp': '^\w{8,14}$', 'required': True} ]:
        if checkFormVariable(request, cond['key'], cond['regexp'], cond['required']):
            params[cond['key']] = request.args.get(cond['key'])
        else:
            app.logger.info('invalid key found.');
            is_valid = False
            break
    #        
    if is_valid:
        dbproxy = TokeiDBProxy(app.logger)
        try:
            xml = dbproxy.doQuery('getMetaInfo', params)
        except:
            app.logger.error('doQuery() failed.')
            flash('database transaction failed.')
            return abort(500)
        if xml:
            try:
                res = TokeiDBResponseMetaInfo(xml)
            except:
                flash('database return value was wrong.')
                return abort(500)
            result = {}
            result['STATUS'] = int(res.result('STATUS')['TEXT'])
            result['ERROR_MSG'] = res.result('ERROR_MSG')['TEXT']
            result['TABLE_INF'] = res.metadata_inf('TABLE_INF')
            result['CLASS_INF'] = res.metadata_inf('CLASS_INF')
        else:
            res = None
            result = None
        return render_template('getMetaInfo.html', result=result)
    else:
        app.logger.info('validation error.')
        flash('validation error.')
        return abort(500)

########################################################################
#
# getMetaInfo
#
########################################################################

def searchClassNameByCode(class_inf, id, code):
    for clsobj in class_inf:
        if clsobj['id'] == id:
            for cls in clsobj['CLASS']:
                if cls['code'] == code:
                    # some CLASS record does not have 'name' attribute.
                    if 'name' in cls:
                        return cls['name']
                    else:
                        return ''
    return 'Not Found'

@app.route('/getStatsData', methods=['GET'])
def showStatsData():
    #
    params = {}
    #
    lv_re = '^$|^\w{1,12}$|^\w{1,12}-\w{1,12}$|^\-\w{1,12}$|^\w{1,12}\-$'
    cd_re = '^$|^\w{1,12}$'
    #
    for cond in [ {'key': 'statsDataId', 'regexp': '^\w{10,12}$', 'required': True},
                  #
                  {'key': 'lvHyo', 'regexp': lv_re, 'required': False},
                  {'key': 'cdHyo', 'regexp': cd_re, 'required': False},
                  {'key': 'cdHyoFrom', 'regexp': cd_re, 'required': False},
                  #
                  {'key': 'lvTime', 'regexp': lv_re, 'required': False},
                  {'key': 'cdTime', 'regexp': cd_re, 'required': False},
                  {'key': 'cdTimeFrom', 'regexp': cd_re, 'required': False},
                  #
                  {'key': 'lvArea', 'regexp': lv_re, 'required': False},
                  {'key': 'cdArea', 'regexp': cd_re, 'required': False},
                  {'key': 'cdAreaFrom', 'regexp': cd_re, 'required': False},
                  #
                  {'key': 'lvCat01', 'regexp': lv_re, 'required': False},
                  {'key': 'cdCat01', 'regexp': cd_re, 'required': False},
                  {'key': 'cdCat01From', 'regexp': cd_re, 'required': False},
                  #
                  {'key': 'lvCat02', 'regexp': lv_re, 'required': False},
                  {'key': 'cdCat02', 'regexp': cd_re, 'required': False},
                  {'key': 'cdCat02From', 'regexp': cd_re, 'required': False},
                  #
                  {'key': 'lvCat03', 'regexp': lv_re, 'required': False},
                  {'key': 'cdCat03', 'regexp': cd_re, 'required': False},
                  {'key': 'cdCat03From', 'regexp': cd_re, 'required': False},
                  #
                  {'key': 'lvCat04', 'regexp': lv_re, 'required': False},
                  {'key': 'cdCat04', 'regexp': cd_re, 'required': False},
                  {'key': 'cdCat04From', 'regexp': cd_re, 'required': False},
                  #
                  {'key': 'lvCat05', 'regexp': lv_re, 'required': False},
                  {'key': 'cdCat05', 'regexp': cd_re, 'required': False},
                  {'key': 'cdCat05From', 'regexp': cd_re, 'required': False},
                  #
                  {'key': 'lvCat06', 'regexp': lv_re, 'required': False},
                  {'key': 'cdCat06', 'regexp': cd_re, 'required': False},
                  {'key': 'cdCat06From', 'regexp': cd_re, 'required': False},
                  #
                  {'key': 'lvCat07', 'regexp': lv_re, 'required': False},
                  {'key': 'cdCat07', 'regexp': cd_re, 'required': False},
                  {'key': 'cdCat07From', 'regexp': cd_re, 'required': False},
                  #
                  {'key': 'lvCat08', 'regexp': lv_re, 'required': False},
                  {'key': 'cdCat08', 'regexp': cd_re, 'required': False},
                  {'key': 'cdCat08From', 'regexp': cd_re, 'required': False},
                  #
                  {'key': 'lvCat09', 'regexp': lv_re, 'required': False},
                  {'key': 'cdCat09', 'regexp': cd_re, 'required': False},
                  {'key': 'cdCat09From', 'regexp': cd_re, 'required': False},
                  #
                  {'key': 'lvCat10', 'regexp': lv_re, 'required': False},
                  {'key': 'cdCat10', 'regexp': cd_re, 'required': False},
                  {'key': 'cdCat10From', 'regexp': cd_re, 'required': False},
                  #
                  {'key': 'lvCat11', 'regexp': lv_re, 'required': False},
                  {'key': 'cdCat11', 'regexp': cd_re, 'required': False},
                  {'key': 'cdCat11From', 'regexp': cd_re, 'required': False},
                  #
                  {'key': 'lvCat12', 'regexp': lv_re, 'required': False},
                  {'key': 'cdCat12', 'regexp': cd_re, 'required': False},
                  {'key': 'cdCat12From', 'regexp': cd_re, 'required': False},
                  #
                  {'key': 'lvCat13', 'regexp': lv_re, 'required': False},
                  {'key': 'cdCat13', 'regexp': cd_re, 'required': False},
                  {'key': 'cdCat13From', 'regexp': cd_re, 'required': False},
                  #
                  {'key': 'lvCat14', 'regexp': lv_re, 'required': False},
                  {'key': 'cdCat14', 'regexp': cd_re, 'required': False},
                  {'key': 'cdCat14From', 'regexp': cd_re, 'required': False},
                  #
                  {'key': 'lvCat15', 'regexp': lv_re, 'required': False},
                  {'key': 'cdCat15', 'regexp': cd_re, 'required': False},
                  {'key': 'cdCat15From', 'regexp': cd_re, 'required': False} ]:
    #
        if request.args.get(cond['key']):
            params[cond['key']] = request.args.get(cond['key'])
    #
    dbproxy = TokeiDBProxy(app.logger)
    #
    try:
        # stime = datetime.datetime.now()
        xml = dbproxy.doQuery('getStatsData', params)
        # ftime = datetime.datetime.now()
        # app.logger.info('(statsData) db query  execution time was %s' % (ftime - stime))
    except:
        app.logger.error('doQuery() failed.')
        flash('database transaction failed.')
        return abort(500)

    if xml:
        # このサービスでデータを全て表示する必要はないので上限を 200 にする。
        limit = 200
        try:
            # stime = datetime.datetime.now()
            res = TokeiDBResponseStatsData(xml, limit)
            # ftime = datetime.datetime.now()
            # app.logger.info('(statsData) parse xml execution time was %s' % (ftime - stime))
        except ValueError:
            flash('database return value was wrong.')
            return abort(500)
        result = {}
        result['STATUS'] = int(res.result('STATUS')['TEXT'])
        result['NUMBER'] = int(res.statistical_data('TABLE_INF')['TOTAL_NUMBER']['TEXT'])
        result['ERROR_MSG'] = res.result('ERROR_MSG')['TEXT']
        result['TABLE_INF'] = res.statistical_data('TABLE_INF')
        result['CLASS_INF'] = res.statistical_data('CLASS_INF')
        #
        # VALUE 要素の attributes を CLASS 中の言葉に置き換える
        # 
        # <CLASS_OBJ id="Hyo" name="表章項目">
        #   <CLASS code="001" name="売上高（収入額）" unit="百万円"/>
        #
        # <DATA_INF>
        #   <VALUE hyo="001" bun01="00000" area="00000" time="2009000000" unit="百万円">290,535,703</VALUE>
        #
        # この場合、{'hyo': '001',' hyo_name': '売上高（収入額）'} に変換される。
        #
        result['DATA_INF'] = []
        data_inf = res.statistical_data('DATA_INF')
        if 'VALUE' in data_inf:
            for value in data_inf['VALUE']:
                tmpdic = {'TEXT': value['TEXT']}
                category = ''
                for key, val in value['ATTR'].iteritems():
                    clsname = searchClassNameByCode(res.statistical_data('CLASS_INF'), key, val)
                    app.logger.info('clsname is %s for key(%s), val(%s)' % (clsname, key, val))
                    # pack Cat?? into one data
                    if key[0:3] == 'cat':
                        category +=  clsname+ ', '
                    else:
                        tmpdic.update({key: value['ATTR'][key]})
                        tmpdic.update({key + '_name': clsname})
                tmpdic.update({'category': category})
                result['DATA_INF'].append(tmpdic)
    else:
        result = None
        
    return render_template('getStatsData.html', result=result, limit=limit)

########################################################################
#
# error handler
#
########################################################################

@app.errorhandler(403)
def internal_error_403(error):
    return render_template('error.html', errormsg='403 Forbidden')

@app.errorhandler(404)
def internal_error_404(error):
    return render_template('error.html', errormsg='404 Not Found')

@app.errorhandler(500)
def internal_error_500(error):
    return render_template('error.html', errormsg='500 Internal Server Error')

if __name__ == '__main__':
    
    app.run()

#
# end of code
#
