import requests
import urllib3
import xml.etree.ElementTree as ET
import logging
import sqlite3
import re

logging.basicConfig(filename="cash.log", level=logging.DEBUG)
conn = sqlite3.connect("menu.db")
cursor = conn.cursor()
''' Всё, что закомментировано ниже запускается один раз, если нет файла menu.db только для того чтобы его создать '''
# cursor.execute("""CREATE TABLE menuitems
#                   (Ident text, ItemIdent text, SourceIdent text, GUIDString text, AssignChildsOnServer text,
#                    ActiveHierarchy text, Code text, Name text, AltName text, MainParentIdent text, Status text,
#                    VisualType_Image text, VisualType_BColor text, VisualType_TextColor text, VisualType_Flags text,
#                    SalesTerms_Flag text, SalesTerms_StartSale text, SalesTerms_StopSale text, RightLvl text,
#                    AvailabilitySchedule text, UseStartSale text, UseStopSale text, TaxDishType text,
#                    FutureTaxDishType text, Parent text, ExtCode text, ShortName text, AltShortName text,
#                    PortionWeight text, PortionName text, AltPortion text, Kurs text, QntDecDigits text,
#                    ModiScheme text, ComboScheme text, ModiWeight text, CookMins text, Comment text,
#                    Instruct text, Flags text, TaraWeight text, ConfirmQnt text, MInterface text,
#                    MinRestQnt text, BarCodes text, PriceMode text, OpenPrice text, DontPack text,
#                    ChangeQntOnce text, AllowPurchasing text, UseRestControl text, UseConfirmQnt text,
#                    CategPath text, SaleObjectType text, ComboJoinMode text, ComboSplitMode text, AddLineMode text,
#                    ChangeToCombo text, GuestsDishRating text, RateType text, MinimumTarifTime text, MaximumTarifTime text,
#                    IgnoredTarifTime text, MinTarifAmount text, MaxTarifAmount text, RoundTime text, TariffRoundRule text,
#                    MoneyRoundRule text, DefTarifTimeLimit text, ComboDiscount text, LargeImagePath text,
#                    HighLevelGroup1 text, HighLevelGroup2 text, HighLevelGroup3 text, HighLevelGroup4 text,
#                    BarCodesText text, BarcodesFullInfo text, ItemKind text)
#                """)


def MenuToSql():
    headers = {'Content-Type': 'application/xml', 'Accept-Encoding': 'identity'}
    urllib3.disable_warnings()
    xml1 = open('items.xml', 'r') # Читаем файл с XML запросом
    xml = xml1.read()
    xml1.close()
    host = 'https://192.168.0.188:16387/rk7api/v0/xmlinterface.xml'
    MenuItem = requests.post(host, verify=False, data=xml, headers=headers, auth=('HTTP', '1')).text
    root = ET.fromstring(MenuItem)
    Items_all = root.findall('RK7Reference')[0].findall('Items')[0].findall('Item')
    itemsAttribs = [x.attrib for x in Items_all] # Получаем словари с элементами меню из xml аттрибутов
    clear = "DELETE FROM menuitems"  # Очищаем всё содержмиое sql базы с меню, чтобы загрузить свежее.
    cursor.execute(clear)
    conn.commit()
    for attrib in itemsAttribs:
        toSql = str(list(attrib.values())) # Преобразуем список значений словаря в строку - так надо для записи в SQL
        toSql = re.sub(r'\[|\]','',toSql) # Убираем все дурацкие символы, которые не любит SQL
        cursor.execute('''INSERT INTO menuitems VALUES ('''+ toSql + ''' )''') # Пишем поэлементно меню в SQL
    conn.commit()


def RequestMenu(cod):
    dishRequestByCode = "SELECT * FROM menuitems WHERE Status='rsActive' AND Code=?"
    code = cod
    cursor.execute(dishRequestByCode, [(str(code))]) # Запрашиваем все элементы блюда с определённым кодом
    rownames = list(map(lambda x: x[0], cursor.description))
    dishdetails = cursor.fetchone()
    dish = dict(zip(rownames,dishdetails))
    return dish

# ----------------------------------- Main Loop --------------------------------------

MenuToSql() # Сперва грузим меню
myDish = RequestMenu(50) # Запрашиваем из загруженного меню элемент с указанным кодом
print(myDish['Name'], myDish['GUIDString'])

