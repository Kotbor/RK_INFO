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
##############logging#############
logging.basicConfig(filename='tables_info.log', level=logging.INFO)
logging.info('Start process in: ' + time.strftime('%H:%M:%S %d.%m.%y', time.localtime()))
print('')
############write_func############
def json_write(out):
    with open('table.json', 'a', encoding='utf-8') as file:
        file.write('%s\n' % out)
##########plans_in_cash###########
def CashPlansToSql():
    headers = {'Content-Type': 'application/xml', 'Accept-Encoding': 'identity'}
    urllib3.disable_warnings()
    ##########Читаем файл с XML запросом#########
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
    cashes = [x.attrib for x in root3.findall('RK7Reference')[0].findall('Items')[0].findall('Item')]
    all_tables = [x.attrib for x in root1.findall('RK7Reference')[0].findall('Items')[0].findall('Item')]
    all_halls = [x.attrib for x in root2.findall('RK7Reference')[0].findall('Items')[0].findall('Item')]
    clear = "DELETE FROM hall" #план зала у станции(отсюда берём id плана зала для связки с кассой)
    cursor.execute(clear)
    clear2 = "DELETE FROM hallplans" #все планы залов(отсюда берём код плана зала и имя)
    cursor.execute(clear2)
    clear3 = "DELETE FROM tables" #столы
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

# def RequestHallInCash(cod):
#     dishRequestByCode = "SELECT * FROM hall WHERE Status='rsActive' AND DefHallPlanID=?"
#     code = cod
#     cursor.execute(dishRequestByCode, [(str(code))]) # Запрашиваем все элементы блюда с определённым кодом
#     rownames = list(map(lambda x: x[0], cursor.description))
#     dishdetails = cursor.fetchone()
#     dish = dict(zip(rownames, dishdetails))
#     return dish

def RequestNameInHall(namehall):
    hall_ident = 1003563
    dishRequestByCode2 = ('''
                            SELECT h.NAME Name, t.NAME NameTable
                            FROM hall h
                            INNER JOIN hallplans hp ON h.DEFHALLPLANID = hp.Ident
                            INNER JOIN tables t ON h.DEFHALLPLANID = t.HALL
                            WHERE h.DEFHALLPLANID = ?''')
    cursor.execute(dishRequestByCode2,(str(hall_ident),))
    rownames = list(map(lambda x: x[0], cursor.description))
    dishdetails = cursor.fetchone()
    dish = dict(zip(rownames, dishdetails))
    return dish
# ----------------------------------- Main Loop --------------------------------------
CashPlansToSql()

nameinhall = 'Name'
#myHall = RequestHallInCash(cash_code_plans)
myHallPlans = RequestNameInHall(nameinhall)

print(myHallPlans)

#output = json.dumps(myHall, ensure_ascii=False, indent=1)
#json_write(output)
logging.info('End process in ' + time.strftime('%H:%M:%S %d.%m.%y', time.localtime()) + '\n')
