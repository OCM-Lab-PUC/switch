"""
Script to upload and refresh the geo_substation table in the swith_chile
OCM database. The only inputs needed are the connection parameters.

"""

import urllib.request, urllib.parse, urllib.error
import pandas as pd
import matplotlib.pyplot as plt
import numpy.random as np
import sys
import matplotlib
import string
import psycopg2
import csv

"////////// SIC /////////////////"

#se descarga y guarda el excel
url = 'http://infotecnica.cdec-sic.cl/instalaciones/?eid=0&type=33&download=true'
urllib.request.urlretrieve(url, "SE.xls")

#lectura del excel y guarda las columnas relevantes en dataframes 
tabla_completa = pd.read_excel('SE.xls',0,skiprows=3)

db_name_col = pd.DataFrame(columns=['db_name'])
system_col = pd.DataFrame(columns=['system'])

#pd.read_excel('SE.xls',0,parse_cols=[8])
cdec_name_col = tabla_completa.ix[:,8:9]
cdec_name_col.columns = ['cdec_name']

latitude_col = tabla_completa.ix[:,23:24]
latitude_col.columns = ['latitude']

longitude_col = tabla_completa.ix[:,24:25]
longitude_col.columns = ['longitude']

#el huso se importaba como double, se pasa a string
huso_col = tabla_completa.ix[:,25:26]
huso_col.columns = ['huso']
huso_col = huso_col.fillna(0)
huso_col = huso_col.astype(int)

region_col = tabla_completa.ix[:,11:12]
region_col.columns = ['region']

owner_name_col = tabla_completa.ix[:,2:3]
owner_name_col.columns = ['owner_name']

owner_cdec_code_col = tabla_completa.ix[:,1:2]
owner_cdec_code_col.columns = ['owner_cdec_code']

owner_substation_number_col = tabla_completa.ix[:,6:7]
owner_substation_number_col.columns = ['owner_substation_number']

#la matriz tensiones almacena las 6 columnas correspondientes a las tensiones 500,220,154,110,66,44,33 kV
tensiones = tabla_completa.ix[:,16:23]

db_voltage=pd.DataFrame(columns=['db_voltage'])
db_voltage_aux=pd.DataFrame(columns=['db_voltage'])
prueba=pd.DataFrame(columns=['db_voltage'])
matriz_aux=pd.DataFrame(columns=['db_name', 'system', 'latitude', 'longitude', 'region', 'cdec_name', 'owner_name','owner_cdec_code', 'owner_substation_number', 'huso'])

#db_voltage_aux y matriz_aux se utilixan para almacenar las filas duplicadas y añadirlas después


for x in range (1, cdec_name_col.size+1):

	#se limpian los nombres para crear la columna db_name
	stringA=cdec_name_col['cdec_name'][x-1:x].to_string(index=False)
	stringB=stringA.replace("S/E","").replace(" ","_").replace("(","").replace(")","").replace("_","",1).replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u").lower();
	db_name_col.set_value(x-1, ['db_name'], stringB)
	system_col.set_value(x-1, ['system'], 'sic')

	#se cambian las comas por puntos decimales para latitud y longitud
	stringC=latitude_col['latitude'][x-1:x].to_string(index=False).replace(",",".")
	latitude_col.set_value(x-1, ['latitude'],stringC)

	stringD=longitude_col['longitude'][x-1:x].to_string(index=False).replace(",",".")
	longitude_col.set_value(x-1, ['longitude'],stringD)

	x += 1

#se juntan las matrices modificadas en una matriz
matriz = pd.concat([db_name_col, system_col, latitude_col, longitude_col, region_col, cdec_name_col, owner_name_col, owner_cdec_code_col ,owner_substation_number_col, huso_col], axis=1)		
contador_aux=1

matriz_aux.set_value(0, ['db_name', 'system', 'latitude', 'longitude', 'region', 'cdec_name', 'owner_name','owner_cdec_code', 'owner_substation_number', 'huso'], [0,0,0,0,0,0,0,0,0,0])
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
matriz = pd.concat([matriz,matriz_aux])
matriz['indice']=range(0,len(matriz))
matriz=matriz.set_index('indice')


"//////////////////////////// SING //////////////////////////////////"

url_sing = 'http://cdec2.cdec-sing.cl/pls/portal/cdec.pck_pag_web_pub.get_file?p_file=SSEE_Coordenadas_UTM30052011.xls'
urllib.request.urlretrieve(url_sing, "SE_sing.xls")

tabla_completa_sing = pd.read_excel('SE_sing.xls',sheetname=None,skiprows=1)


tabla_completa_sing_df = pd.DataFrame(columns=['Nombre','Niveles de Tensión (kV)','Entrada en Operación','Coordenada Este', 'Coordenada Norte','Datum','Huso'])
tabla_completa_sing_df=tabla_completa_sing_df.from_dict(tabla_completa_sing, orient='index', dtype=None)



# db_name_sing_col = pd.DataFrame(columns=['db_name'])
# system_sing_col = pd.DataFrame(columns=['system'])

# cdec_name_sing_col = tabla_completa_sing.ix[:,0:1]
# cdec_name_sing_col.columns = ['cdec_name']

# latitude_sing_col = tabla_completa_sing.ix[:,5:6]
# latitude_sing_col.columns = ['latitude']

# longitude_sing_col = tabla_completa_sing.ix[:,4:5]
# longitude_sing_col.columns = ['longitude']

# region_sing_col=pd.DataFrame(columns=['region'])

# owner_name_sing_col = tabla_completa_sing.ix[:,1:2]
# owner_name_sing_col.columns = ['owner_name']

# owner_cdec_code_sing_col =pd.DataFrame(columns=['owner_cdec_code'])


# owner_substation_number_sing_col= pd.DataFrame(columns=['owner_substation_number'])

# huso_sing_col = tabla_completa_sing.ix[:,7:8]
# huso_sing_col.columns = ['huso']
# huso_sing_col = huso_sing_col.astype(int)

# for x in range (1, cdec_name_sing_col_col.size+1):
# 	stringA=cdec_name_sing_col['cdec_name'][x-1:x].to_string(index=False)
# 	stringB=stringA.replace(" ","_").replace("(","").replace(")","").replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u").lower();
# 	db_name_sing_col.set_value(x-1, ['db_name'], stringB)

# 	system_sing_col.set_value(x-1, ['system'], 'sing')
# 	region_sing_col.set_value(x-1, ['region'], 'NA')
# 	owner_cdec_code_sing_col.set_value(x-1, ['owner_cdec_code'], 'NA')
# 	owner_substation_number_sing_col.set_value(x-1, ['owner_substation_number'], 'NA')

# 	stringC=latitude_sing_col['latitude'][x-1:x].to_string(index=False).replace(",",".")
# 	latitude_sing_col.set_value(x-1, ['latitude'],stringC)

# 	stringD=longitude_sing_col['longitude'][x-1:x].to_string(index=False).replace(",",".")
# 	longitude_sing_col.set_value(x-1, ['longitude'],stringD)

# 	x += 1


# matriz_sing = pd.concat([db_name_sing_col, system_sing_col, latitude_sing_col, longitude_sing_col, region_sing_col, cdec_name_sing_col, owner_name_sing_col, owner_cdec_code_sing_col ,owner_substation_number_sing_col, huso_sing_col], axis=1)		

#print(matriz_sing)

"/////////////////////////// UPLOAD TO DB ///////////////////////////"

#se pasa la matriz a csv sin fila ni columna de índices
matriz.to_csv('geo_substation_csv', header=False, index=False, index_label=False)

#se conecta con el servidor
try:
    # Remember to enter and/or modify connection parameters accordingly to your
    # setup
    con = psycopg2.connect(database='switch_chile', user='caravena', 
                            host='localhost', port='5915',
                            password=)
    print ("Connection to database established...")
    sys.stdout.flush()
except:
    sys.exit("Error connecting to the switch_chile database...")

#se lee el CSV y se almacena la información como tupla
with open('geo_substation_csv', 'r') as f:
    reader = csv.reader(f)
    your_list = tuple(reader)

cur = con.cursor()

#se eliminan los datos anteriores disponibles en la base de datos
try:
	query1 = "DELETE FROM chile_new.geo_substations"
	cur.execute(query1)
	print("table erased")
except:
	print("Error erasing")


#se carga la nueva matriz a la base de datos
try:
    query = "INSERT INTO chile_new.geo_substations (db_name, db_voltage, system, latitude, longitude, region, cdec_name, owner_name,owner_cdec_code, owner_substation_number, huso) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    cur.executemany(query, your_list)
    con.commit()
    print ("Query for population of timeseries id %s has been successful")
    sys.stdout.flush()
except psycopg2.DatabaseError as e:
    if con:
        con.rollback()
    print (e)

if cur:
    cur.close()
if con:
    con.close()






