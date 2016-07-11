# -*- coding: utf-8 -*-
# Copyright 2016 The Switch-Chile Authors. All rights reserved.
# Licensed under the Apache License, Version 2, which is in the LICENSE file.
# Operations, Control and Markets laboratory at Pontificia Universidad
# Católica de Chile.
"""

Script to upload and refresh the geo_substation table in the swith_chile
OCM database. The only inputs needed are the connection parameters.

"""
from __future__ import print_function
import pandas as pd
import sys, os.path, psycopg2
from csv import writer, reader
from unidecode import unidecode
from pyproj import Proj, transform

if sys.version_info > (3, 0):
    import urllib.request as request
else:
    import urllib as request
    
if sys.getdefaultencoding() != 'utf-8':
    # Character encoding may raise errors if set in ascii or other simple
    # encodings which do not support spanish characters.
    reload(sys)
    sys.setdefaultencoding('utf-8')

def limpiar(st):
    # Returns a clean string without accents, spaces and commas
    return unidecode(st.replace(' ','_')).lower().replace(
                    ',','_').replace('(','').replace(')','').replace(
                    "'",'_').replace('s/e','').strip('_')

###############################
############# SIC #############

# Fetch spreadsheet if it doesn't exist
if not os.path.isfile('SE_SIC.xls'):
    try:
        url = 'http://infotecnica.cdec-sic.cl/instalaciones/?eid=0&type=33&download=true'
        request.urlretrieve(url, 'SE_SIC.xls')
        print ('Successfully downloaded SIC spreadsheet')
    except:
        sys.exit('An error ocurred while fetching the SIC substations spreadsheet')

# Format: northing-easting 
locations = {
    'lican': ['720623', '5499198', '18'],
    'tap_duqueco': [ '736615.8','5844254.2', '18'],
    'valdivia_sts': ['655200.55','5592977.05','18'],
    'banos_del_toro': [ '6698734', '400860', '19'],
    'pudahuel': [ '6300592', '339149', '19'],
    'agrosuper': [ '6844413', '296684', '19'],
    'algarrobo': [ '6812566', '306952', '19'],
    'la_coipa': [ '7032620', '473399', '19'],
    'principal_mina_navio': [ '6383009', '294084', '19'],
    'compresora_mina_navio': [ '6383009', '294084', '19'],
    'tap_maestranza': [ '6216765.15', '338473.17', '19'],
    'cerro_negro_norte': [ '6999184', '366743', '19'],
    'interconexion': [ '6153500', '343250', '19'],
    'tap_talinay': [ '6582627.06', '251549.74', '19'],
    'canal_melado': [ '6045250', '312663', '19'],
    'cuel': [ '717384.8', '5837306.2', '18'],
    'el_arrayan': [ '6610994', '240768', '19'],
    'don_goyo': [ '6610994', '240768', '19'],
    'planta_desaladora_y_bombeo_ndeg1': [ '7063396', '331136', '19'],
    'bombeo_2': [ '7063396', '331136', '19'],
    'eb2': [ '6973933', '357619', '19'],
    'lalackama': [ '7223318', '365891', '19'],
    'tap_lalackama': ['7223318', '365891', '19'],
    'tap_tal_tal': ['7223318', '365891', '19'],
    'chanares': [ '7081829', '398248', '19'],
    'pv_salvador': [ '7081829', '398248', '19'],
    'los_hierros_ii': [ '6031822', '312240', '19'],
    'picoiquen': [ '5813055', '690687', '18'],
    'javiera': [ '7089644', '379330', '19'],
    'seccionadora_lo_aguirre': [ '6298235', '323741', '19'],
    'pichil': [ '5492161', '668560', '18'],
    'nahuelbuta': [ '5828059', '712763', '18']
}

# Skip first 3 empty rows when building the Dataframe
df_SIC = pd.read_excel('SE_SIC.xls',0,skiprows=3)

db_name_col = pd.DataFrame(columns=['db_name'])
system_col = pd.DataFrame(columns=['system'])

cdec_name_col = df_SIC.ix[:,8:9]
cdec_name_col.columns = ['cdec_name']

# In the CDEC-SIC spreadsheet, northing and easting are switched.
northing_col = df_SIC.ix[:,24:25]
northing_col.columns = ['northing']

easting_col = df_SIC.ix[:,23:24]
easting_col.columns = ['easting']

# Missing UTM zones are filled with 0, then transformed to ints.
huso_col = df_SIC.ix[:,25:26].fillna(value=0)
huso_col.columns = ['huso']
huso_col = huso_col.astype(int)

region_col = df_SIC.ix[:,11:12]
region_col.columns = ['region']

owner_name_col = df_SIC.ix[:,2:3]
owner_name_col.columns = ['owner_name']

owner_cdec_code_col = df_SIC.ix[:,1:2]
owner_cdec_code_col.columns = ['owner_cdec_code']

owner_substation_number_col = df_SIC.ix[:,6:7]
owner_substation_number_col.columns = ['owner_substation_number']

# la matriz tensiones almacena las 6 columnas 
# correspondientes a las tensiones 500,220,154,110,66,44,33 kV
tensiones = df_SIC.ix[:,16:23]

db_voltage=pd.DataFrame(columns=['db_voltage'])
db_voltage_aux=pd.DataFrame(columns=['db_voltage'])
prueba=pd.DataFrame(columns=['db_voltage'])
matriz_aux=pd.DataFrame(columns=['db_name', 'system', 'easting',
    'northing', 'region', 'cdec_name', 'owner_name','owner_cdec_code', 
    'owner_substation_number', 'huso'])

# db_voltage_aux y matriz_aux se utilixan 
# para almacenar las filas duplicadas y añadirlas después

for x in range (1, cdec_name_col.size+1):

    #se limpian los nombres para crear la columna db_name
    stringB=limpiar(cdec_name_col['cdec_name'][x-1:x].to_string(index=False))
    db_name_col.set_value(x-1, ['db_name'], stringB)
    system_col.set_value(x-1, ['system'], 'sic')

    #se cambian las comas por puntos decimales para latitud y longitud
    stringC=northing_col['northing'][x-1:x].to_string(index=False).replace(",",".")
    northing_col.set_value(x-1, ['northing'],stringC)

    stringD=easting_col['easting'][x-1:x].to_string(index=False).replace(",",".")
    easting_col.set_value(x-1, ['easting'],stringD)

    x += 1

#se juntan las matrices modificadas en una matriz
matriz = pd.concat([db_name_col, system_col, easting_col, northing_col,
    region_col, cdec_name_col, owner_name_col, owner_cdec_code_col,
    owner_substation_number_col, huso_col], axis=1)       
contador_aux=1

matriz_aux.set_value(0, ['db_name', 'system', 'easting', 'northing', 'region', 'cdec_name', 'owner_name','owner_cdec_code', 'owner_substation_number', 'huso'], [0,0,0,0,0,0,0,0,0,0])
db_voltage_aux.set_value(0, ['db_voltage'], 0)

#se recorre la matriz, se eliminan las filas sin tensión asignado 
#y se duplican las filas con más de una tensión, las copias se almacenan en 
#matriz_aux. En db_voltage y db_voltaje_aux se almacenan los voltajes correspondientes
row_iterator = matriz.iterrows()
for index, row in row_iterator:
    contador_voltaje=0
    contador_2=0
    aux= []
    for z in range (0,6):
        if tensiones.get_value(index,z,takeable=True) == 'si':
            contador_voltaje += 1
            if z==0:
                aux.append(500)
            elif z==1:
                aux.append(220)
            elif z==2:
                aux.append(154)
            elif z==3:
                aux.append(110)
            elif z==4:
                aux.append(66)
            elif z==5:
                aux.append(44)
            else:
                aux.append(33)
    if contador_voltaje==0:
        matriz=matriz.drop(index, axis=0)   
    while contador_voltaje>=1:
        contador_voltaje-=1
        if contador_voltaje>=1:
            matriz_aux=matriz_aux.append(matriz.loc[index])
            prueba.set_value(0, ['db_voltage'], aux[contador_2])
            db_voltage_aux=db_voltage_aux.append(prueba,ignore_index=True)
            contador_aux +=1
        else:
            db_voltage.set_value(index,['db_voltage'],aux[contador_2])
        contador_2 +=1

#se añade la columna de voltajes a la matriz en la posición correspondiente al formato de la BD
matriz.insert(1, 'db_voltage', db_voltage)

#se modifica el índice de la matriz auxiliar y se insertan los voltajes correspondientes
matriz_aux['indice']=range(0,len(matriz_aux))
matriz_aux=matriz_aux.set_index('indice')
matriz_aux.insert(1,'db_voltage',db_voltage_aux)
matriz_aux = matriz_aux[matriz_aux.db_name != 0]
db_voltage_aux.reindex(index=range(0,len(matriz_aux)))

#Se juntan la matriz y matriz auxiliar para obtner todos los datos de SIC
matriz1 = pd.concat([matriz,matriz_aux])
matriz['indice']=range(0,len(matriz))
matriz = matriz.set_index('indice')

with open('substations_sic.csv','w') as outfile:
    matriz.to_csv(outfile, sep=',', header=False, index=False, 
        encoding='utf-8')

###############################
############# SING #############

# Fetch spreadsheet if it doesn't exist
if not os.path.isfile('SE_SING.xls'):
    try:
        url = 'http://cdec2.cdec-sing.cl/pls/portal/cdec.pck_pag_web_pub.get_file?p_file=SSEE_Coordenadas_UTM30052011.xls'
        request.urlretrieve(url, 'SE_SING.xls')
        print ('Successfully downloaded SIC spreadsheet')
    except:
        sys.exit('An error ocurred while fetching the SIC substations spreadsheet')

def empty_name(cell_value):
    if cell_value != cell_value:
        # If its nan, return empty string
        return ''
    else:
        return cell_value

# Get dictionary with all sheets as Dataframes
df_SING = pd.read_excel('SE_SING.xls', sheetname=None, 
    skiprows=1)
all_sheets = []
for key in df_SING:
    # Drop columns which are not of interest
    df_SING[key].fillna('', inplace=True)
    col1 = 'Entrada en Operación'.decode('utf-8')
    col2 = 'Propietario'
    if col1 in df_SING[key].columns.values:
        df_SING[key] = df_SING[key].drop(col1, axis=1)
    if col2 in df_SING[key].columns.values:
        df_SING[key] = df_SING[key].drop(col2, axis=1)
    all_sheets.append(map(list, df_SING[key].values))
all_stations = []
# In all_rows, every substation excel row will be stored as a list
for sheet in all_sheets:
    for row in sheet:
        all_stations.append(row)

# Coordinate projection engines
projection_UTM18S = Proj('+init=EPSG:32718')
projection_UTM19S = Proj('+init=EPSG:32719')
projection_PSAD56 = Proj('+init=EPSG:24879')

# CSV columns
name = 0
voltage = 1
easting = 2
northing = 3
datum = 4
zone = 5
original_name = 6

empty = 0
for index, station in enumerate(all_stations):
    # Tensions are not inputted in two cases: when the company is listing
    # all coordinates in the station's terrain or when all the voltage levels
    # are specified in the first row of the station. In both cases, rows w/o
    # voltage values should be removed.

    # Some substations correspond to the same location with different
    # voltage levels, so names must be filled.
    if not station[name]:
        # Fetch the previous name if an empty value is found
        station[name] = all_stations[index-1][name]
        station[easting] = all_stations[index-1][easting]
        station[northing] = all_stations[index-1][northing]
        station[datum] = all_stations[index-1][datum]
        station[zone] = all_stations[index-1][zone]
    # Put the original name at the end of the list and save a clean copy
    station.append(station[name])
    station[name] = limpiar(station[name])

    
    # In these previous cases, voltages are defined as a string in the 
    # first row of the station. Parse these voltages and distribute them:
    if isinstance(station[voltage], basestring):
        voltages = station[voltage].split('/')
        voltages = [v.strip() for v in voltages]
        for i, v in enumerate(voltages):
            all_stations[index+i][voltage] = v
    
    # Some substations have coordinates for all structures in a station
    # Keep only 1 pair of coords per voltage
    if not station[voltage]:
        empty+=1
    
    # If the station has no defined Datum, then it is wgs84, zone 19.
    # (Determined by manual inspection)
    if not station[datum] or station[datum] == 'K':
        station[datum] = 'WGS84'
    if not station[zone]:
        station[zone] = 19
    # Also, transform floats to strings
    if not isinstance(station[datum], basestring):
        station[datum] = 'WGS84'
    # Some coordinates are mixed up (northing should always be greater
    # than easting for zone 19 and the SING)
    if station[easting] > station[northing]:
        station[easting], station[northing] = station[northing], station[easting]
        
    # Only one substation doesn't have coordinates:
    if station[name] == 'muelle':
        station[easting] = '368548'
        station[northing] = '7486686'
        station[datum] = 'WGS84'
        station[zone] = 19
    
    # Transform PSAD56 coordinates into WGS84    
    if '84' not in station[datum]:
        station[easting], station[northing] = (str(coord) 
            for coord in transform(
                projection_PSAD56, projection_UTM18S, 
                float(station[easting]), float(station[northing])))
        station[zone] = '18'
# Loop through the list removing repeated stations
while empty > 0:
    for st in all_stations:
        if not st[voltage]:
            all_stations.remove(st)
            empty-=1
            break

with open('substations_sing.csv', 'w') as out:
    csv_writer = writer(out, delimiter = ',')
    for station in all_stations:
        csv_writer.writerow([station[name], station[voltage], 'sing',
            station[easting], station[northing], '', station[original_name],
            '', '', '', station[zone]])

##############################
####### UPLOAD TO DB #########

# Both csv's must be read into a big list of lists
subs_for_db = []
with open('substations_sic.csv', 'r') as f:
    read = reader(f)
    for row in read:
        subs_for_db.append(row)
with open('substations_sing.csv', 'r') as f:
    read = reader(f)
    for row in read:
        subs_for_db.append(row)

# Proyection engines to transform UTM coordinates into a single zone: 18S.
# Substations which are missing location are given manually inputted values.
for station in subs_for_db:
    if station[-1] == '0':
        # Easting
        station[3] = locations[station[0]][1]
        # Northing
        station[4] = locations[station[0]][0]
        # Zone
        station[-1] = locations[station[0]][2]
    # Project all coordinates to UTM zone 18S.
    if station[-1] == '19':
        station[3], station[4] = (str(coord) for coord in transform(
            projection_UTM19S, projection_UTM18S, 
            station[3], station[4]))
        station[-1] = '18'
with open('testing.csv', 'w') as out:
    csv_writer = writer(out, delimiter = ',')
    for station in subs_for_db:
        csv_writer.writerow(station)
"""
##############
# DB Conection
try:
    # Remember to enter and/or modify connection parameters accordingly to your
    # setup
    con = psycopg2.connect(database='switch_chile', user='caravena', 
                            host='localhost', port='5915',
                            password='')
    print ("Connection to database established...")
except:
    sys.exit("Error connecting to the switch_chile database...")



cur = con.cursor()

#se eliminan los datos anteriores disponibles en la base de datos
try:
    query1 = "DELETE FROM chile_new.geo_substations"
    cur.execute(query1)
    print("Table erased")
except psycopg2.DatabaseError as e:
    if con:
        con.rollback()
    print(e)

#se carga la nueva matriz a la base de datos
try:
    query = "INSERT INTO chile_new.geo_substations (db_name, db_voltage, system, northing, easting, region, cdec_name, owner_name,owner_cdec_code, owner_substation_number, huso) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    cur.executemany(query, your_list)
    con.commit()
    print ("Query for population of timeseries id %s has been successful")
except psycopg2.DatabaseError as e:
    if con:
        con.rollback()
    print(e)

if cur:
    cur.close()
if con:
    con.close()






"""
