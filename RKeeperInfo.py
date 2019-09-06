# -*- coding: utf-8 -*-
import time
import json
import requests
import urllib3
import xml.etree.ElementTree as ET
import logging
from logging.handlers import RotatingFileHandler
import re
import socket
import sys
import uuid
import os
import socketio
from datetime import datetime
import configparser
import sqlite3


##############logging#############
#logging.basicConfig(filename='sender.log', level=logging.DEBUG) #настраиваем логирование
logging.getLogger("urllib3").setLevel(logging.WARNING) # Прогоняем debug сообщения от urllib

logger = logging.getLogger('my_logger')

handler = RotatingFileHandler('sender.log', maxBytes=2000, backupCount=10)
logger.addHandler(handler)


#-------------------------------------------- Config----------------------------------------------
config = configparser.ConfigParser()
config.read('VideoSender.cfg')
try:
    VideoServer = config['Settings']['VideoServer']
    ListenPort = config['Settings']['ListenPort']
    ListenIP = config['Settings']['ListenIP']
    XMLInterface = config['Settings']['XMLInterface']
    GUIDInterface = config['Settings']['GUIDInterface']
    LogLevel = int(config['Settings']['LogLevel'])
except Exception as e:
    logger.critical(str(e))
    logger.critical('Config file is missing or incorrect?')
# -----------------------------Получаем GUID от сервера и сохраняем его в cfg------------------------------
# Если не получится забрать guid - будет использоваться старое значение из cfg-----------------------------
try:
    guid = requests.get(GUIDInterface).text
    config['Settings']['GUID'] = guid
    with open('VideoSender.cfg', 'w') as configfile:
        config.write(configfile)
    print(guid)
except:
    logger.debug('No connection to GUID server')

if LogLevel == 1:
    logger.setLevel(logging.DEBUG)
elif LogLevel == 0:
    logger.setLevel(logging.CRITICAL)

ProductGUID = config['Settings']['guid'] # Забираем guid из cfg

sio = socketio.Client(logger=True)
firstConnection = True # При первом подключении передаём authobject
success = False # Отслеживаем успешный ответ




############Создание талиц############
def init(tablename, labels):
    db = sqlite3.connect('rk_item.db')  # обращение к базе sqlite
    cursor = db.cursor()
    full_labels = ''
    for x in labels:
        x += ' text,'
        full_labels += x
    querytext = ('''CREATE TABLE %s (%s)''') % (tablename, full_labels[:-1])
    cursor.execute(querytext)

##########указываем количество байт для чтения##########
def recvall():
    BUFF_SIZE = 2048  # 4 KiB
    data = b''
    sock.listen(10)
    conn, addr = sock.accept()
    while True:
        part = conn.recv(BUFF_SIZE)
        data += part
        length = len(part)
        if length < BUFF_SIZE:
            break
    return data
# ##########запись общей информации##########
# def json_write_w(out): #перезаписываем файл
#     with open('order_full.json', 'w', encoding="utf-8") as file:
#         file.write('%s\n' % out)
# ##########запись информации о заказе##########
# def json_write(out): #перезаписываем файл
#     with open('order.json', 'w', encoding='utf-8') as file:
#         file.write('%s\n' % out)

##########Читаем файл с XML запросом#########
def CashPlansToSql():
    try:
        headers = {'Content-Type': 'application/xml', 'Accept-Encoding': 'identity'}
        urllib3.disable_warnings() #отключаем ошибку orllib3
        xml_1 = '''<?xml version="1.0" encoding="windows-1251"?>
    <RK7Query>
    <RK7CMD CMD="GetRefData" RefName="TABLES"/>
    </RK7Query>''' #столы
        xml_2 = '''<?xml version="1.0" encoding="windows-1251"?>
    <RK7Query>
    <RK7CMD CMD="GetRefData" RefName="HALLPLANS"/>
    </RK7Query>''' #перечень планов зала и столы
        xml_3 = '''<?xml version="1.0" encoding="windows-1251"?>
    <RK7Query>
    <RK7CMD CMD="GetRefData" RefName="CASHES"/>
    </RK7Query>''' #имя кассы и план зала по умолчанию
        xml_4 = '''<?xml version="1.0" encoding="utf-8"?>
    <RK7Query>
        <RK7CMD CMD="GetRefData" RefName="MenuItems"/>
    </RK7Query>''' #меню
        xml_5 = '''<?xml version="1.0" encoding="utf-8"?>
    <RK7Query>
        <RK7CMD CMD="GetRefData" RefName="PRICES"/>
    </RK7Query>''' #цены
        host = XMLInterface
        MenuItem1 = requests.post(host, verify=False, data=xml_1, headers=headers, auth=('HTTP', '1')).text #столы
        MenuItem2 = requests.post(host, verify=False, data=xml_2, headers=headers, auth=('HTTP', '1')).text #перечень планов зала и столы
        MenuItem3 = requests.post(host, verify=False, data=xml_3, headers=headers, auth=('HTTP', '1')).text #имя кассы и план зала по умолчанию
        MenuItem4 = requests.post(host, verify=False, data=xml_4, headers=headers, auth=('HTTP', '1')).text #меню
        MenuItem5 = requests.post(host, verify=False, data=xml_5, headers=headers, auth=('HTTP', '1')).text #цены
        root1 = ET.fromstring(MenuItem1) #столы
        root2 = ET.fromstring(MenuItem2) #перечень планов зала и столы
        root3 = ET.fromstring(MenuItem3) #имя кассы и план зала по умолчанию
        root4 = ET.fromstring(MenuItem4) #меню
        root5 = ET.fromstring(MenuItem5) #цены
        global cashes, all_tables, all_halls, itemsAttribs, prices
        itemsAttribs = [x.attrib for x in root4.findall('RK7Reference')[0].findall('Items')[0].findall('Item')] #элементы меню
        cashes = [x.attrib for x in root3.findall('RK7Reference')[0].findall('Items')[0].findall('Item')] #все кассы(тут берём инфу по станции, её ID  и ID плана зала)
        all_tables = [x.attrib for x in root1.findall('RK7Reference')[0].findall('Items')[0].findall('Item')] #все столы(тут имя стола, его Guid и ID плана зала)
        all_halls = [x.attrib for x in root2.findall('RK7Reference')[0].findall('Items')[0].findall('Item')] #все планы залов(ID)
        prices = [x.attrib for x in root5.findall('RK7Reference')[0].findall('Items')[0].findall('Item')] #все цены

        #########connect_hall.db########
        if os.path.exists('rk_item.db'):  # проверяем наличие rk_item.db, если нет базы, то создаём
            pass
        else:
            new_item = list([x for x in itemsAttribs[0]])
            init('menuitems', new_item)
            new_item = list([x for x in cashes[0]])
            init('hall', new_item)
            new_item = list([x for x in all_tables[0]])
            init('tables', new_item)
            new_item = list([x for x in all_halls[0]])
            init('hallplans', new_item)
            new_item = list([x for x in prices[0]])
            init('prices', new_item)

        db = sqlite3.connect('rk_item.db')  # обращение к базе sqlite
        cursor = db.cursor()
        clear = "DELETE FROM hall" #очищаем таблицу с планами зала и столами
        cursor.execute(clear)
        clear2 = "DELETE FROM hallplans" #очищаем таблицу с названием кассы и планом зала по умолчанию
        cursor.execute(clear2)
        clear3 = "DELETE FROM tables" #очищаем таблицу со столами
        cursor.execute(clear3)
        clear4 = "DELETE FROM menuitems" #очищаем таблицу с меню
        cursor.execute(clear4)
        clear5 = "DELETE FROM prices" #очищаем таблицу с ценами
        cursor.execute(clear5)
        db.commit()
        for attrib in cashes:
            toSql = str(list(attrib.values()))# Преобразуем список значений словаря в строку - так надо для записи в SQL
            toSql = re.sub(r'\[|\]','',toSql)# Убираем все дурацкие символы, которые не любит SQL
            cursor.execute('''INSERT INTO hall VALUES ('''+ toSql + ''' )''')# Пишем в SQL
        for attrib in all_halls:
            toSql = str(list(attrib.values()))
            toSql = re.sub(r'\[|\]','',toSql)
            cursor.execute('''INSERT INTO hallplans VALUES ('''+ toSql + ''' )''')
        for attrib in all_tables:
            toSql = str(list(attrib.values()))
            toSql = re.sub(r'\[|\]','',toSql)
            cursor.execute('''INSERT INTO tables VALUES ('''+ toSql + ''' )''')
        for attrib in itemsAttribs:
            toSql = str(list(attrib.values()))
            toSql = re.sub(r'\[|\]', '', toSql)
            cursor.execute('''INSERT INTO menuitems VALUES (''' + toSql + ''' )''')
        for attrib in prices:
            if list(attrib.values())[6] == '1025352' and list(attrib.values())[5] == 'psDish': #price type
                toSql = str(list(attrib.values()))
                toSql = re.sub(r'\[|\]', '', toSql)
                cursor.execute('''INSERT INTO prices VALUES (''' + toSql + ''' )''')
        db.commit()
    except Exception as e:
        logger.critical('Failed to get cashplans to sql')
        logger.critical(e)

##############получаем план зала, столы и guid#################
def RequestNameInHall(hall_ident):
    try:
        db = sqlite3.connect('rk_item.db')  # обращение к базе sqlite
        cursor = db.cursor()
        dishRequestByCode2 = ("""SELECT t.NAME NAME, t.GUIDString GUID, hp.Name HALL_NAME 
                                FROM hall h
                                INNER JOIN hallplans hp ON h.DEFHALLPLANID = hp.Ident
                                INNER JOIN tables t ON h.DEFHALLPLANID = t.HALL
                                WHERE h.DEFHALLPLANID = ?""")
        cursor.execute(dishRequestByCode2,(str(hall_ident),))
        dishdetails = cursor.fetchall()
        global plans
        plans = []
        for x in dishdetails:
            plans.append({'Number': x[0], 'Id': re.sub(r'\{|\}','',x[1])})
        for y in dishdetails: # ToDO Зачем здесь итерация?
            hall = {'Name': y[2]} # ToDO hall перезапишется последним значением из итерации
            hall['Tables'] = plans
            return hall
    except Exception as e:
        logger.critical('Failed to Request Name from Hall')
        logger.critical(e)


########получаем всё меню#######
def RequestAllMenu():
    try:
        db = sqlite3.connect('rk_item.db')  # обращение к базе sqlite
        cursor = db.cursor()
        products = []
        logger.info('Start func ' + ' RequestAllMenu ' + time.strftime('%H:%M:%S %d.%m.%y', time.localtime()) + '\n')
        dishRequestByCode = ("""SELECT m.Ident, m.GUIDString, m.Code, m.Name, p.Value as Price
                                FROM menuitems m
                                INNER JOIN prices p ON m.ItemIdent = p.ObjectID
                                WHERE m.Status='rsActive'""")
        cursor.execute(dishRequestByCode)  # Запрашиваем все элементы блюда с определённым кодом
        logger.info('End func ' + ' RequestMenu ' + time.strftime('%H:%M:%S %d.%m.%y', time.localtime()) + '\n')
        dishdetails = cursor.fetchall()
        for item in dishdetails:
            price = str(int(item[4]) / 100) #приводим в правильный вид цену
            products.append({'Price': price, 'Type': 'Dish', 'Name': item[3], 'Code': item[2], 'Id': re.sub(r'\{|\}','',item[1])})
        return products
    except Exception as e:
        logger.critical('Failed to RequestAllMenu')
        logger.critical(e)
##############конвертируем текущий формат даты#############
def DtimeConvert():
    JavaDtime = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f+03:00')
    return JavaDtime
##############конвертируем заданны формат даты#############
def OrdertimeConvert(dtime):
    OrderDtime = (datetime.strptime(dtime, '%d.%m.%Y %H:%M:%S')).strftime('%Y-%m-%dT%H:%M:%S.%f+03:00')
    return OrderDtime
###########получаем информацию о планах зала, столах и меню##########
def info_station():
    try:
        id_hall = child.attrib['HallPlanID']
        myHallPlans = RequestNameInHall(id_hall)
        menuItems = RequestAllMenu()
        output = {
            "IsCashServer": True,
            "IsBackup": False,
            "Password": "randomString",
            "TerminalName": child.attrib['StationName'],
            "TerminalGroup": {
                "Name": child.attrib['StationName'],
                "MaxCourseNumber": 4,
                "Id": re.sub(r'\{|\}', '', child.attrib['StationGuid'])
            },
            "Sections": [myHallPlans]
        }
        menu = {'Groups': '', 'ProductCategories': '', 'Products': [menuItems]}
        output['Menu'] = menu
        info = output
        output = json.dumps(output, ensure_ascii=False, indent=1)
        #json_write_w(output)
        return info
    except Exception as e:
        logger.critical('Failed to get InfoStation')
        logger.critical(e)

# -----------------------------события для SocketIO-----------------------------------
@sio.event
def connect():
    logger.debug('connection established')
    global firstConnection
    if firstConnection == True:
        authObject['IsCashServer'] = True
        firstConnection = False
    else:
        authObject['IsCashServer'] = 'False'
        authObject['TerminalName'] = "R-Keeper_pos"

@sio.event
def authenticated(data):
    global connected
    logger.debug('R-Keeper backup server Plugin authenticated', data)
    connected = True

@sio.event
def responseOrder(data):
    global success
    logger.debug('responseOrder', data)
    success = True

@sio.event
def auth_confirmation(data):
    logger.debug('auth_confirmation', data)

@sio.event
def authentication_error(data):
    logger.debug('authentication_error', data)

@sio.event
def disconnect():
    logger.debug('R-Keeper has been disconnected')
    '''
    global connected
    connected = False
    trying = 5
    while connected == False:
        trying -= 1
        sio.connect(VideoServer)
        sio.emit('authentication', authObject)
        sio.sleep(4)
        if trying ==0: # Leaving after trying limit
            logger.debug("Can't reconnect to SIO")
            connected = True
    '''
def sendOrder(contents): # Sending order every 5 seconds, while "responceOrder" received
    global success
    success = False
    contents = json.loads(contents)
    count = 0
    while success == False:
        count +=1
        try:
            sio.emit('posOrder', contents)
            logger.debug('posOrder sent to sio, try №%s' % count)
            sio.sleep(5)
        except:
            logger.debug('Failed to emit posOrder')
        finally:
            if count>=5:
                success=True

        #success = True
# ----------------------------------- Main Loop --------------------------------------
try:
    sock = socket.socket()
    sock.bind((ListenIP, int(ListenPort)))  # Слушаем нужный порт, указанный в конфиге
    logger.info('Сервер запущен')
except:
    logger.debug("WARNING! Something already stolen this Cash_Port, choose another one. Exiting!")
    logger.critical('Не могу запустить сервер')
    sys.exit()

try:
    CashPlansToSql()
except:
    logger.critical("No connection to R-Keeper XML")
    sys.exit()
status = False #используется для того чтобы каждый раз не переписывать order_full при login
logger.info('MainLoop Started.')
while True:
    data = '<body>\n'
    dat2 = recvall()
    dat2 = dat2.decode()
    data += str(dat2)
    data += '\n</body>'
    try:
        root = ET.fromstring(data)
    except:
        root = ''
    logger.debug('=======================Raw data begin========================')
    logger.debug(data)
    logger.debug('=======================Raw data end==========================')
    for child in root:
        inside = child.attrib
        if child.tag == 'LogIn':  # Login посылается всего один раз. Передаются планы залов, столы и меню
            if status == False:
                authObject = info_station()# Получаем authObject
                sio.connect(VideoServer)
                sio.emit('authentication', authObject)
                status = True
                logger.debug('Starting connection to SIO')
        if child.tag == 'NewOrder':
            StatusOrder = "New"
        else:
            StatusOrder = "Open"
        if child.tag == 'ScreenCheck':
            try:
                all_items = root[0].findall('CheckLines')[0].findall('CheckLine')
                Waiter = {
                    'Name': child.attrib['WaiterName'],
                    'Id': re.sub(r'\{|\}', '', child.attrib['WaiterGuid'])
                }
                Tables = []
                Table = {
                    'Number': child.attrib['TableName'],
                    'Id': re.sub(r'\{|\}', '', child.attrib['TableGuid'])
                }
                Tables.append(Table)
                Products = []
                for x in all_items:
                    Amount = x.attrib['Qnt']
                    if Amount == '0.00':
                        Deleted = True
                    else:
                        Deleted = False
                    Product = {
                        'Id': str(uuid.uuid4()),
                        'ProductId': re.sub(r'\{|\}', '', x.attrib['Guid']),
                        'Name': x.attrib['Name'],
                        'Price': float(x.attrib['Price']),
                        'ResultSum': float(child.attrib['FullSum']),  # todo исправить
                        'Amount': float(x.attrib['Qnt']),
                        "Comment": "",
                        'Deleted': Deleted,
                        "DeletionMethod": None,
                        'PrintTime': DtimeConvert(),
                        "ServeTime": None,
                        "Modifiers": []
                    }
                    if re.sub(r'\{|\}', '', x.attrib['Guid']) == ProductGUID:
                        Products.append(Product)
                Guests = []
                guests = {
                    'Id': str(uuid.uuid4()),
                    'Name': child.attrib['GuestName'],
                    'Products': Products
                }
                Guests.append(guests)
                Order = {
                    'Id': re.sub(r'\{|\}', '', child.attrib['OrderGuid']),
                    "OrderTypeId": None,
                    "Status": StatusOrder,
                    'ResultSum': float(child.attrib['FullSum']),
                    'FullSum': float(child.attrib['FullSum']),
                    'OpenTime': OrdertimeConvert(child.attrib['OpenTime']),
                    "BillTime": None,
                    "CloseTime": None,
                    'Number': datetime.today().timestamp(),
                    'Waiter': Waiter,
                    "Cashier": None,
                    'Tables': Tables,
                    "IsBanquetOrder": False,
                    'Guests': Guests,
                    "PaymentItems": []
                }
                randomOrder = {
                    'Type': "PrintedProductsChanged",
                    'Order': Order,
                    "Idempotency_key": None
                }
                if Product['Deleted'] == True: #если полностью удалён
                    output = json.dumps(randomOrder, ensure_ascii=False, indent=1)
                    #json_write(output)
                    orderObject = output
                    sendOrder(orderObject)
            except Exception as e:
                logger.critical('Failed parsing ScreenCheck')
                logger.critical(e)

        if child.tag == 'StoreCheck':  # Сохранение заказа
            try:
                output = json.dumps(randomOrder, ensure_ascii=False, indent=1)
                #json_write(output)
                orderObject = output
                sendOrder(orderObject)
                ##############################
                all_items = root[0].findall('CheckLines')[0].findall('CheckLine')
                Waiter = {
                    'Name': child.attrib['WaiterName'],
                    'Id': re.sub(r'\{|\}', '', child.attrib['WaiterGuid'])
                }
                Tables = []
                Table = {
                    'Number': child.attrib['TableName'],
                    'Id': re.sub(r'\{|\}', '', child.attrib['TableGuid'])
                }
                Tables.append(Table)
                Products = []
                for x in all_items:
                    Amount = x.attrib['Qnt']
                    if Amount == '0.00':
                        Deleted = True
                    else:
                        Deleted = False
                    Product = {
                        'Id': str(uuid.uuid4()),
                        'ProductId': re.sub(r'\{|\}', '', x.attrib['Guid']),
                        'Name': x.attrib['Name'],
                        'Price': float(x.attrib['Price']),
                        'ResultSum': float(child.attrib['FullSum']),  # todo исправить
                        'Amount': float(x.attrib['Qnt']),
                        "Comment": "",
                        'Deleted': Deleted,
                        "DeletionMethod": None,
                        'PrintTime': DtimeConvert(),
                        "ServeTime": None,
                        "Modifiers": []
                    }
                    if re.sub(r'\{|\}', '', x.attrib['Guid']) == ProductGUID:
                        Products.append(Product)
                Guests = []
                guests = {
                    'Id': str(uuid.uuid4()),
                    'Name': child.attrib['GuestName'],
                    'Products': Products
                }
                Guests.append(guests)
                Order = {
                    'Id': re.sub(r'\{|\}', '', child.attrib['OrderGuid']),
                    "OrderTypeId": None,
                    "Status": StatusOrder,
                    'ResultSum': float(child.attrib['FullSum']),
                    'FullSum': float(child.attrib['FullSum']),
                    'OpenTime': OrdertimeConvert(child.attrib['OpenTime']),
                    "BillTime": None,
                    "CloseTime": None,
                    'Number': datetime.today().timestamp(),
                    'Waiter': Waiter,
                    "Cashier": None,
                    'Tables': Tables,
                    "IsBanquetOrder": False,
                    'Guests': Guests,
                    "PaymentItems": []
                }
                randomOrder2 = {
                    'Type': "PrintedProductsChanged",
                    'Order': Order,
                    "Idempotency_key": None
                }
                if randomOrder['Order']['Tables'][0]['Number'] != randomOrder2['Order']['Tables'][0]['Number']: #сверяем столы по Id
                    output = json.dumps(randomOrder2, ensure_ascii=False, indent=1)
                    #json_write(output)
                    orderObject = output
                    try:
                        logger.debug('========================OrderObject Begin==================')
                        logger.debug(str(orderObject))
                        logger.debug('========================OrderObject End====================')
                    except:
                        logger.debug("Can't write orderObject")
                    sendOrder(orderObject)
            except Exception as e:
                logger.critical('Failed parsing StoreCheck')
                logger.critical(e)
