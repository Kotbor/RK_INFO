import xml.etree.ElementTree as ET
import configparser
import requests
import urllib3
import sys
import logging
from flask import Flask, render_template, request, url_for, jsonify

if getattr(sys, 'frozen', False):
    template_folder = os.path.join(sys._MEIPASS, 'templates')
    static_folder = os.path.join(sys._MEIPASS, 'static')
    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
else:
    app = Flask(__name__)

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

config = configparser.ConfigParser()
config.read('MenuServer.cfg')
XMLInterface = config['Settings']['XMLInterface']

host = XMLInterface

xml = '''<?xml version="1.0" encoding="utf-8"?>
<RK7Query>
	<RK7CMD CMD="GetRefData" RefName="MenuItems"/>
</RK7Query>'''

headers = {'Content-Type': 'application/xml', 'Accept-Encoding': 'identity'}
urllib3.disable_warnings()

try:
    MenuItem = requests.post(host, verify=False, data=xml, headers=headers, auth=('HTTP', '1')).text  # меню
except:
    print('No connection to R-Keeper XML server')
    sys.exit()

root = ET.fromstring(MenuItem)  # меню
allItems = root[0][0].findall('Item')
menuList = []
for item in allItems:
    if item.attrib['Status'] == 'rsActive':
        element = {'GUID': item.attrib['GUIDString'],
                   'Name': item.attrib['Name'],
                   'Ident': item.attrib['Ident']}

        menuList.append(element)


def storeGUID(guid):
    with open('guid.txt', 'w', encoding='utf-8') as file:
        file.write('%s' % guid)


def readGUID():
    with open('guid.txt', 'r', encoding='utf-8') as file:
        a = file.read()
    for item in menuList:
        if item['GUID'] == a:
            return item



@app.route('/')
def index():
    nowSelectedItem = readGUID()
    return render_template('index.html', menuList= menuList, nowSelectedItem= nowSelectedItem)


@app.route("/store" , methods= ['GET', 'POST'])
def store():
    if request.method == "POST":
        clicked = request.form['data']
        for item in menuList:
            if item['GUID'] == clicked:
                guid = item['GUID']
                storeGUID(guid)
                return jsonify ({'status': 'OK', 'data': item})


@app.route("/API/GetGuid")
def getGUID():
    guid = readGUID()['GUID']
    guid = guid.replace('{', '')
    guid = guid.replace('}', '')
    return guid

try:
    app.run(host='0.0.0.0',debug=False)
except:
    print ("Can't create web sever at localhost:5000")
    sys.exit()
