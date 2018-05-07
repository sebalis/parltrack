#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import logging
import os

import config
import model

from datetime import datetime
from logging import Formatter, FileHandler
from sys import version_info

from flask import Flask, render_template, request

if version_info[0] == 3:
    unicode = str

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
app.config.from_object('config')


#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/dumps')
def dumps():
    return render_template('dumps.html')


@app.route('/meps')
def meps():
    date = getDate()
    return render_template('meps.html', date=date)


@app.route('/dossiers')
def dossiers():
    return render_template('dossiers.html')


# Error handlers.

@app.errorhandler(500)
def internal_error(error):
    #db_session.rollback()
    return render_template('errors/500.html'), 500


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.template_filter()
def asdate(value):
    if isinstance(value, int):
        value=datetime.fromtimestamp(value)
    if type(value) not in [str, unicode]:
        return value.strftime('%Y/%m/%d')
    return value.split(' ')[0]


@app.template_filter()
def asdiff(obj): # should have a new and old item
    de=diff_match_patch.diff_match_patch()
    diffs=de.diff_main(' '.join (obj.get('old','')),' '.join (obj.get('new','')))
    de.diff_cleanupSemantic(diffs)
    return de.diff_prettyHtml(diffs)


@app.template_filter()
def asPE(obj): # should have a new and old item
    return urllib.unquote(obj).split('+')[2]


@app.template_filter()
def asmep(value):
    if value in mepcache:
        mep=mepcache[value]
    else:
        db = connect_db()
        if isinstance(value, int):
            mep=db.ep_meps2.find_one({'UserID': value}, {'changes': False})
        else:
            mep=db.ep_meps2.find_one({'_id': value}, {'changes': False})
        #if not mep:
        #    mep=db.ep_meps.find_one({'_id': value}, {'changes': False})
        if not mep:
            return value
        mepcache[value]=mep
    return u'<a href="/mep/%s">%s</a>' % (mep['Name']['full'],mep['Name']['full'])


@app.template_filter()
def asdossier(value):
    db = connect_db()
    doc=db.dossiers2.find_one({'procedure.reference': value})
    if not doc:
        return value
    return (u'<a href="/dossier/%s">%s</a> %s' %
            (doc['procedure']['reference'],
             doc['procedure']['reference'],
             doc['procedure']['title']))


@app.template_filter()
def isodate(value):
    if type(value)==type(datetime(1,1,1)):
        return value.isoformat()
    return datetime.strptime(value,'%Y-%m-%d').isoformat()


@app.template_filter()
def group_icon(value):
    if not value: return ''
    if type(value)==type(list()): value=value[0]
    if value=='NA': value='NI'
    return "static/images/%s.gif" % value.lower().replace('/','_')


@app.template_filter()
def protect_email(email_address):
    character_set = '+-.0123456789@ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz'
    char_list = list(character_set)
    shuffle(char_list)

    key = ''.join(char_list)

    cipher_text = ''
    id = 'e' + str(randrange(1,999999999))

    for a in email_address:
        cipher_text += key[ character_set.find(a) ]

    script = 'var a="'+key+'";var b=a.split("").sort().join("");var c="'+cipher_text+'";var d="";'
    script += 'for(var e=0;e<c.length;e++)d+=b.charAt(a.indexOf(c.charAt(e)));'
    script += 'document.getElementById("'+id+'").innerHTML="<a href=\\"mailto:"+d+"\\">"+d+"</a>"'


    script = "eval(\""+ script.replace("\\","\\\\").replace('"','\\"') + "\")"
    script = '<script type="text/javascript">/*<![CDATA[*/'+script+'/*]]>*/</script>'

    return '<span id="'+ id + '">[javascript protected email address]</span>'+ script


def getDate():
    date=datetime.now()
    if request.args.get('date'):
        try:
            date=datetime.strptime(request.args['date'], "%d/%m/%Y")
        except ValueError:
            try:
                date=datetime.strptime(request.args['date'], "%Y-%m-%d")
            except ValueError:
                date=datetime.strptime(request.args['date'], "%Y/%m/%d")
    return date


if not config.DEBUG:
    app.logger.setLevel(logging.INFO)

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

if __name__ == '__main__':
    app.run(port=config.WEBSERVER_PORT)
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
