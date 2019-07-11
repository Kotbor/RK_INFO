import time
import json
import requests
import urllib3
import xml.etree.ElementTree as ET
import logging
import sqlite3
import re

#########connect_hall.db########
conn = sqlite3.connect('rk_item.db')
cursor = conn.cursor()
##############logging#############
logging.basicConfig(filename='tables_info.log', level=logging.INFO)
logging.info('Start process in: ' + time.strftime('%H:%M:%S %d.%m.%y', time.localtime()))
print('')
############init############
#def init():
    # cursor.execute("""CREATE TABLE hall
    #                     (Ident text, ItemIdent text, SourceIdent text, GUIDString text, AssignChildsOnServer text, ActiveHierarchy text,
    #                      Name text, AltName text, Code text, MainParentIdent text, Status text, NetName text, Resolution text, Colors text,
    #                      RightLvl text, OSType text, STType text, DefHallPlanID text, FileManagerPath text, WaitDataSended text, AfterShiftClosure text,
    #                      SyncStatesFlags text, DataSendTimeout text, ReserveCashGroupID text, AutoSelfUpdate text, GraphicParameters text, CashGroup text)
    #                """)
    # cursor.execute("""CREATE TABLE hallplans
    #                     (Ident text, ItemIdent text, SourceIdent text, GUIDString text, AssignChildsOnServer text, ActiveHierarchy text, Code text,
    #                     Name text, AltName text, MainParentIdent text, Status text, VisualType_Image text, VisualType_BColor text, VisualType_TextColor text,
    #                     VisualType_Flags text, EditRight text, RightLvl text, ServingPosition text, Restaurant text, VisualType_TZColor text, ServedAtCashServer text)
    #                """)
    # cursor.execute("""CREATE TABLE tables
    #                     (Ident text,ItemIdent text,SourceIdent text,GUIDString text,AssignChildsOnServer text,ActiveHierarchy text,
    #                     Code text,Name text,MainParentIdent text,Status text,VisualType_Image text,VisualType_BColor text,
    #                     VisualType_TextColor text,VisualType_Flags text,ServingPosition text,TableGroup text,Hall text,RightLvl text,
    #                     DoserDevice text,HallPlanItemKind text,TableUseKind text,MaxGuests text,ButtonNum text,PagerMsgNum text,
    #                     DeviceFlags text,LogDevice text,Tariff text,MaxDeviceTime text,OnOffInterval text,Lane text,
    #                     UserAttribute1 text,UserAttribute2 text,UserAttribute3 text,ShutDownOnLimitExceeded text,
    #                     UseDeviceAsTable text,AllowReservation text)
    #                """)

############write_func############

##########функция записи в json##########
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
    xml_1 = xml1.read()
    xml_2 = xml2.read()
    xml_3 = xml3.read()
    xml1.close()
    xml2.close()
    xml3.close()
    host = 'https://192.168.0.188:16387/rk7api/v0/xmlinterface.xml'
    MenuItem1 = requests.post(host, verify=False, data=xml_1, headers=headers, auth=('HTTP', '1')).text
    MenuItem2 = requests.post(host, verify=False, data=xml_2, headers=headers, auth=('HTTP', '1')).text
    MenuItem3 = requests.post(host, verify=False, data=xml_3, headers=headers, auth=('HTTP', '1')).text
    root1 = ET.fromstring(MenuItem1)
    root2 = ET.fromstring(MenuItem2)
    root3 = ET.fromstring(MenuItem3)
    global cashes, all_tables, all_halls
    cashes = [x.attrib for x in root3.findall('RK7Reference')[0].findall('Items')[0].findall('Item')] #все кассы(тут берём инфу по станции, её ID  и ID плана зала)
    all_tables = [x.attrib for x in root1.findall('RK7Reference')[0].findall('Items')[0].findall('Item')] #все столы(тут имя стола, его Guid и ID плана зала)
    all_halls = [x.attrib for x in root2.findall('RK7Reference')[0].findall('Items')[0].findall('Item')] #все планы залов(ID)
    clear = "DELETE FROM hall"
    cursor.execute(clear)
    clear2 = "DELETE FROM hallplans"
    cursor.execute(clear2)
    clear3 = "DELETE FROM tables"
    cursor.execute(clear3)
    conn.commit()
    for attrib in cashes:
        toSql = str(list(attrib.values())) # Преобразуем список значений словаря в строку - так надо для записи в SQL
        toSql = re.sub(r'\[|\]','',toSql) # Убираем все дурацкие символы, которые не любит SQL
        cursor.execute('''INSERT INTO hall VALUES ('''+ toSql + ''' )''')
    for attrib in all_halls:
        toSql = str(list(attrib.values())) # Преобразуем список значений словаря в строку - так надо для записи в SQL
        toSql = re.sub(r'\[|\]','',toSql) # Убираем все дурацкие символы, которые не любит SQL
        cursor.execute('''INSERT INTO hallplans VALUES ('''+ toSql + ''' )''')
    for attrib in all_tables:
        toSql = str(list(attrib.values())) # Преобразуем список значений словаря в строку - так надо для записи в SQL
        toSql = re.sub(r'\[|\]','',toSql) # Убираем все дурацкие символы, которые не любит SQL
        cursor.execute('''INSERT INTO tables VALUES ('''+ toSql + ''' )''')
    conn.commit()

##############получаем план зала, столы и guid#################
def RequestNameInHall():
    hall_ident = 1003563
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
# ----------------------------------- Main Loop --------------------------------------
CashPlansToSql()
myHallPlans = RequestNameInHall()
output = json.dumps(myHallPlans, ensure_ascii=False, indent=1)
json_write(output)
logging.info('End process in ' + time.strftime('%H:%M:%S %d.%m.%y', time.localtime()) + '\n')
