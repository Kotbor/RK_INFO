import time
import json
import requests
import urllib3
import xml.etree.ElementTree as ET
import logging
import sqlite3
import re
import socket
import sys

#########connect_hall.db########
conn = sqlite3.connect('rk_item.db')
cursor = conn.cursor()
##############logging#############
logging.basicConfig(filename='tables_info.log', level=logging.INFO)
logging.info('Start programm in: ' + time.strftime('%H:%M:%S %d.%m.%y', time.localtime()))
print('')
############init############
# def init():
#     cursor.execute("""CREATE TABLE hall
#                         (Ident text, ItemIdent text, SourceIdent text, GUIDString text, AssignChildsOnServer text, ActiveHierarchy text,
#                          Name text, AltName text, Code text, MainParentIdent text, Status text, NetName text, Resolution text, Colors text,
#                          RightLvl text, OSType text, STType text, DefHallPlanID text, FileManagerPath text, WaitDataSended text, AfterShiftClosure text,
#                          SyncStatesFlags text, DataSendTimeout text, ReserveCashGroupID text, AutoSelfUpdate text, GraphicParameters text, CashGroup text)
#                    """)
#     cursor.execute("""CREATE TABLE hallplans
#                         (Ident text, ItemIdent text, SourceIdent text, GUIDString text, AssignChildsOnServer text, ActiveHierarchy text, Code text,
#                         Name text, AltName text, MainParentIdent text, Status text, VisualType_Image text, VisualType_BColor text, VisualType_TextColor text,
#                         VisualType_Flags text, EditRight text, RightLvl text, ServingPosition text, Restaurant text, VisualType_TZColor text, ServedAtCashServer text)
#                    """)
#     cursor.execute("""CREATE TABLE tables
#                         (Ident text,ItemIdent text,SourceIdent text,GUIDString text,AssignChildsOnServer text,ActiveHierarchy text,
#                         Code text,Name text,MainParentIdent text,Status text,VisualType_Image text,VisualType_BColor text,
#                         VisualType_TextColor text,VisualType_Flags text,ServingPosition text,TableGroup text,Hall text,RightLvl text,
#                         DoserDevice text,HallPlanItemKind text,TableUseKind text,MaxGuests text,ButtonNum text,PagerMsgNum text,
#                         DeviceFlags text,LogDevice text,Tariff text,MaxDeviceTime text,OnOffInterval text,Lane text,
#                         UserAttribute1 text,UserAttribute2 text,UserAttribute3 text,ShutDownOnLimitExceeded text,
#                         UseDeviceAsTable text,AllowReservation text)
#                    """)
#     cursor.execute("""CREATE TABLE menuitems
#                       (Ident text, ItemIdent text, SourceIdent text, GUIDString text, AssignChildsOnServer text,
#                        ActiveHierarchy text, Code text, Name text, AltName text, MainParentIdent text, Status text,
#                        VisualType_Image text, VisualType_BColor text, VisualType_TextColor text, VisualType_Flags text,
#                        SalesTerms_Flag text, SalesTerms_StartSale text, SalesTerms_StopSale text, RightLvl text,
#                        AvailabilitySchedule text, UseStartSale text, UseStopSale text, TaxDishType text,
#                        FutureTaxDishType text, Parent text, ExtCode text, ShortName text, AltShortName text,
#                        PortionWeight text, PortionName text, AltPortion text, Kurs text, QntDecDigits text,
#                        ModiScheme text, ComboScheme text, ModiWeight text, CookMins text, Comment text,
#                        Instruct text, Flags text, TaraWeight text, ConfirmQnt text, MInterface text,
#                        MinRestQnt text, BarCodes text, PriceMode text, OpenPrice text, DontPack text,
#                        ChangeQntOnce text, AllowPurchasing text, UseRestControl text, UseConfirmQnt text,
#                        CategPath text, SaleObjectType text, ComboJoinMode text, ComboSplitMode text, AddLineMode text,
#                        ChangeToCombo text, GuestsDishRating text, RateType text, MinimumTarifTime text, MaximumTarifTime text,
#                        IgnoredTarifTime text, MinTarifAmount text, MaxTarifAmount text, RoundTime text, TariffRoundRule text,
#                        MoneyRoundRule text, DefTarifTimeLimit text, ComboDiscount text, LargeImagePath text,
#                        HighLevelGroup1 text, HighLevelGroup2 text, HighLevelGroup3 text, HighLevelGroup4 text,
#                        BarCodesText text, BarcodesFullInfo text, ItemKind text)
#                    """)

############write_func############

##########функция записи в json##########

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


def json_write_w(out):
    with open('zakaz.json', 'w', encoding="utf-8") as file:
        file.write('%s\n' % out)

def json_write(out):
    with open('tables.json', 'a', encoding='utf-8') as file:
        file.write('%s\n' % out)

##########Читаем файл с XML запросом#########
def CashPlansToSql():
    headers = {'Content-Type': 'application/xml', 'Accept-Encoding': 'identity'}
    urllib3.disable_warnings()
    xml1 = open('tables.xml', 'r')
    xml2 = open('halls.xml', 'r')
    xml3 = open('cashes.xml', 'r')
    xml4 = open('items.xml', 'r')
    xml_1 = xml1.read()
    xml_2 = xml2.read()
    xml_3 = xml3.read()
    xml_4 = xml4.read()
    xml1.close()
    xml2.close()
    xml3.close()
    xml4.close()
    host = 'https://192.168.0.188:16387/rk7api/v0/xmlinterface.xml'
    MenuItem1 = requests.post(host, verify=False, data=xml_1, headers=headers, auth=('HTTP', '1')).text
    MenuItem2 = requests.post(host, verify=False, data=xml_2, headers=headers, auth=('HTTP', '1')).text
    MenuItem3 = requests.post(host, verify=False, data=xml_3, headers=headers, auth=('HTTP', '1')).text
    MenuItem4 = requests.post(host, verify=False, data=xml_4, headers=headers, auth=('HTTP', '1')).text
    root1 = ET.fromstring(MenuItem1)
    root2 = ET.fromstring(MenuItem2)
    root3 = ET.fromstring(MenuItem3)
    root4 = ET.fromstring(MenuItem4)
    global cashes, all_tables, all_halls, itemsAttribs
    itemsAttribs = [x.attrib for x in root4.findall('RK7Reference')[0].findall('Items')[0].findall('Item')] #элементы меню
    cashes = [x.attrib for x in root3.findall('RK7Reference')[0].findall('Items')[0].findall('Item')] #все кассы(тут берём инфу по станции, её ID  и ID плана зала)
    all_tables = [x.attrib for x in root1.findall('RK7Reference')[0].findall('Items')[0].findall('Item')] #все столы(тут имя стола, его Guid и ID плана зала)
    all_halls = [x.attrib for x in root2.findall('RK7Reference')[0].findall('Items')[0].findall('Item')] #все планы залов(ID)
    clear = "DELETE FROM hall"
    cursor.execute(clear)
    clear2 = "DELETE FROM hallplans"
    cursor.execute(clear2)
    clear3 = "DELETE FROM tables"
    cursor.execute(clear3)
    clear4 = "DELETE FROM menuitems"
    cursor.execute(clear4)
    conn.commit()
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
        conn.commit()
    conn.commit()

##############получаем план зала, столы и guid#################
def RequestNameInHall(hall_ident):
    logging.info('Start func ' + ' RequestNameInHall ' + time.strftime('%H:%M:%S %d.%m.%y', time.localtime()) + '\n')
    dishRequestByCode2 = ('''
                            SELECT t.NAME NAME, t.GUIDString GUID, hp.Name HALL_NAME 
                            FROM hall h
                            INNER JOIN hallplans hp ON h.DEFHALLPLANID = hp.Ident
                            INNER JOIN tables t ON h.DEFHALLPLANID = t.HALL
                            WHERE h.DEFHALLPLANID = ?''')
    cursor.execute(dishRequestByCode2,(str(hall_ident),))
    dishdetails = cursor.fetchall()
    global plans
    plans = []
    for x in dishdetails:
        plans.append({'Number': x[0], 'Id': x[1]})
    for y in dishdetails:
        hall = {'Name': y[2]}
        hall['Tables'] = plans
        return hall
    logging.info('End func ' + ' RequestNameInHall ' + time.strftime('%H:%M:%S %d.%m.%y', time.localtime()) + '\n')

def RequestMenu(cod):
    logging.info('Start func ' + ' RequestMenu ' + time.strftime('%H:%M:%S %d.%m.%y', time.localtime()) + '\n')
    dishRequestByCode = "SELECT * FROM menuitems WHERE Status='rsActive' AND Code=?"
    code = cod
    cursor.execute(dishRequestByCode, [(str(code))]) # Запрашиваем все элементы блюда с определённым кодом
    rownames = list(map(lambda x: x[0], cursor.description))
    dishdetails = cursor.fetchone()
    dish = dict(zip(rownames, dishdetails))
    logging.info('End func ' + ' RequestMenu ' + time.strftime('%H:%M:%S %d.%m.%y', time.localtime()) + '\n')
    return dish

# ----------------------------------- Main Loop --------------------------------------
try:
    sock = socket.socket()
    sock.bind(('192.168.0.186', 16385))  # Слушаем на всех интерфейсах нужный порт, указанный в конфиге
    print('Соединение установлено')
except:
    logging.debug("WARNING! Something already stolen this Cash_Port, choose another one. Exiting!")
    print('Ошибка соединения')
    sys.exit()

id_hall = 1003563
myHallPlans = RequestNameInHall(id_hall)
output = json.dumps(myHallPlans, ensure_ascii=False, indent=1)
json_write_w(output)

while True:
        data = '<body>\n'
        dat2 = recvall()
        dat2 = dat2.decode()
        data += str(dat2)
        data += '\n</body>'
        root = ET.fromstring(data)
        logging.debug(data)
        for child in root:
            inside = child.attrib

        if child.tag == 'StoreCheck':  #Сохранение заказа
            logging.info('Start func ' + child.tag + time.strftime('%H:%M:%S %d.%m.%y', time.localtime()) + '\n')
            Table = child.attrib['Table']
            all_dishes = [x.attrib for x in child.find('CheckLines').findall('CheckLine')]
            Dish = []
            for Name in all_dishes:
                Dish.append({'CodeDish': Name['Code'], 'NameDish': Name['Name'], 'PriceDish': Name['Price']})
                for N in itemsAttribs:
                    if Name['Code'] == N['Code']:
                        myItem = RequestMenu(Name['Code'])
                        myItem = (myItem['GUIDString'])
                        Dish.append({'Guid': myItem})

            output = json.dumps(Dish, ensure_ascii=False, indent=1)
            json_write_w(output)
            logging.info('End func ' + child.tag + time.strftime('%H:%M:%S %d.%m.%y', time.localtime()) + '\n')

        if child.tag == 'OpenOrder':  #вход в заказ
            logging.info('Start func ' + child.tag + time.strftime('%H:%M:%S %d.%m.%y', time.localtime()) + '\n')
            Tag = child.tag
            Time = child.attrib['Time']
            Name = child[0].attrib['Name']
            output = {
                'Operation': Tag,
                'Time': Time,
                'Name': Name}
            output = json.dumps(output, ensure_ascii=False, indent=1)
            json_write_w(output)
            logging.info('End func ' + child.tag + time.strftime('%H:%M:%S %d.%m.%y', time.localtime()) + '\n')

        if child.tag == 'CloseCheck':  #оплата заказа
            logging.info('Start func ' + child.tag + time.strftime('%H:%M:%S %d.%m.%y', time.localtime()) + '\n')
            Tag = child.tag
            Time = child[0].attrib['Time']
            Summa = child.attrib['Sum']
            Table = child.attrib['Table']
            PersName = child[0][0].attrib['Name']
            output = {
                'Operation': Tag,
                'Time': Time,
                'Table': Table,
                'Sum': Summa,
                'Name': PersName
            }
            output = json.dumps(output, ensure_ascii=False, indent=1)
            json_write_w(output)
            logging.info('End func ' + child.tag + time.strftime('%H:%M:%S %d.%m.%y', time.localtime()) + '\n')

#init()
#
# code_dish = 50
# CashPlansToSql()
#
# myItem = RequestMenu(code_dish)
# myItem = (myItem['Name'], myItem['GUIDString'])
# print(myItem, '\n', myHallPlans)
# output = json.dumps(myItem, ensure_ascii=False, indent=1)
# json_write(output)
# output = json.dumps(myHallPlans, ensure_ascii=False, indent=1)
# json_write(output)

logging.info('End programm in: ' + time.strftime('%H:%M:%S %d.%m.%y', time.localtime()) + '\n')
