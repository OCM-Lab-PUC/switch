# -*- coding: utf-8 -*-
# Operations, Control and Markets laboratory at Pontificia Universidad
# Católica de Chile. July 2016.
"""

Fetches data for existing projects in the Chilean Interconected Systems and 
wrangles with it to upload a clean and updated edition to the database.

"""

import pandas, os, re, datetime, sys
from pyproj import Proj, transform
from unidecode import unidecode

if sys.getdefaultencoding() != 'utf-8':
    # Character encoding may raise errors if set in ascii or other simple
    # encodings which do not support spanish characters.
    reload(sys)
    sys.setdefaultencoding('utf-8')

def limpiar(a):
    # Devuelvo un string limpio de carácteres anómalos, espacios y comas
    return unidecode(a.replace(' ','_').replace('ó','o')).lower().replace(',','_')

out = open('centrales.csv', 'w')
    
df = pandas.read_excel('Capacidad_Instalada.xlsx', sheetname=0, skiprows = 1)

#for i,j in enumerate(df.columns.values):
#   print(limpiar(j),'=',i)

sistema = 0
central = 4
fecha_puesta_en_servicio_central = 5
region = 6
fecha_puesta_en_servicio_unidad = 10
unidades = 11
tipo_de_energia = 13
potencia_neta = 15
punto_de_conexion = 19
combustible_1 = 20
consumo_especifico_1 = 21
unidad_consumo_especifico_1 = 22
combustible_2 = 23
consumo_especifico_2 = 24
unidad_consumo_especifico_2 = 25
combustible_3 = 26
consumo_especifico_3 = 27
unidad_consumo_especifico_3 = 28
este = 32
norte = 33
huso = 34

# Se usa para cuando solo queremos obtener las letras y '_'
letras = re.compile('[^a-zA-Z_]')

# Proyection engines to transform UTM coordinates into a single zone.
projection_UTM18S = Proj('+init=EPSG:32718')
projection_UTM19S = Proj('+init=EPSG:32719')

# Auxiliar set
conjunto = []
comb = [[20,21,22], [23,24,25], [26,27,28]]

# Abrimos el excel correspondiente
for sheet in ['SING','SIC']:
    df = pandas.read_excel('Capacidad_Instalada.xlsx', sheetname= sheet, skiprows = 1, parse_cols = 'B:AJ')
    
    for i in df.index:
        
        for j in comb:
            try:
                if df.ix[i,j[0]]+','+df.ix[i,j[2]] not in conjunto:
                    conjunto.append(df.ix[i,j[0]]+','+df.ix[i,j[2]])  
            except:
                pass
        #Terminamos si no encuentra el mismo sistema
        if df.ix[i,sistema] != df.ix[0,sistema]:
            break
    
        #print(df.ix[i,central])
        
        linea = ''
        
        #Añadimos el sistema
        linea += limpiar(df.ix[i,sistema])+','
        
        #Nombre central
        linea += limpiar(df.ix[i,central])+','
        
        #Tipo de energía
        linea += limpiar(df.ix[i,tipo_de_energia])+','
        
        #Número de unidades sólo está presente en el SIC
        if sheet == 'SIC':
            linea += str(df.ix[i,unidades])+','
        else:
            linea += '1,'
            
        #fecha de inicio central: Si existe le ponemos, sino ponemos 1 de junio
        if df.ix[i,fecha_puesta_en_servicio_central] != '-':
            linea += str(df.ix[i,fecha_puesta_en_servicio_central])+','
        else:
            linea += str(datetime.datetime(2016,6,1))+','
            
        #Potencia neta
        linea += str(df.ix[i,potencia_neta])+','
            
        
        #Añadimos la barra correspondiente, limpiando los caracteres, eliminando 'kv' y 'se'
        barra = letras.sub('',limpiar(df.ix[i,punto_de_conexion])).replace('kv','').replace('se','').replace('__','_')
        #Eliminamos '_' si es que están al inicio y al final
        if barra[0] == '_':
            barra = barra[1:]
        if barra[-1] == '_':
            barra = barra[:-1]
        
        linea += str(barra)+','
        
        # Coordinates must be in UTM WGS-84 format for Zone 18S.
        if df.ix[i, huso] == 19:
            coords = (str(coord) for coord in transform(projection_UTM19S,
                        projection_UTM18S, df.ix[i, este], df.ix[i, norte]))
        elif df.ix[i,huso] == 18:
            coords = (str(df.ix[i, este]), str(df.ix[i, norte]))
        else:
            coords = ('missing Easting', 'missing Northing')
        linea+=','.join(coords)+','
    
        #Combustibles...
    
        #
        #Factores sacados de
        #https://www.extension.iastate.edu/agdm/wholefarm/html/c6-87.html
        #http://www.delekenergy.co.il/?pg=calc&CategoryID=198
    
#        comb = [[21,22,23], [24,25,26], [27,28,29]]
#        for j in combustible:
#            if 'Petróleo Diesel' in j[0]:
#                if df.ix[i,j[2]] == '[m3/MWh]':
#                    df.ix[i,j[1]] = 0.0353 * df.ix[i,j[1]]
            
        if df.ix[i,combustible_1] not in conjunto:
            conjunto.append(df.ix[i,combustible_1])
    
        #Combustible 1
        if not pandas.isnull(df.ix[i,combustible_1]):
            linea += limpiar(df.ix[i,combustible_1])+','
        else:
            linea += ','
        
        #consumo_especifico_1 
        if not pandas.isnull(df.ix[i,consumo_especifico_1]):
            linea += str(df.ix[i,consumo_especifico_1])+','
        else:
            linea += ','
        
        #unidad_consumo_especifico_1 
        if not pandas.isnull(df.ix[i,unidad_consumo_especifico_1]):
            linea += df.ix[i,unidad_consumo_especifico_1].replace('[','').replace(']','')+','
        else:
            linea += ','
    
        
        #Lo mismo para 2 y 3
        
        #Combustible 2
        if not pandas.isnull(df.ix[i,combustible_2]):
            linea += limpiar(df.ix[i,combustible_2])+','
        else:
            linea += ','
        
        #consumo_especifico_2 
        if not pandas.isnull(df.ix[i,consumo_especifico_2]):
            linea += str(df.ix[i,consumo_especifico_2])+','
        else:
            linea += ','
        
        #unidad_consumo_especifico_2 
        if not pandas.isnull(df.ix[i,unidad_consumo_especifico_2]):
            linea += df.ix[i,unidad_consumo_especifico_2].replace('[','').replace(']','')+','
        else:
            linea += ','
    
        #Combustible 3
        if not pandas.isnull(df.ix[i,combustible_3]):
            linea += limpiar(df.ix[i,combustible_3])+','
        else:
            linea += ','
        
        #consumo_especifico_3 
        if not pandas.isnull(df.ix[i,consumo_especifico_3]):
            linea += str(df.ix[i,consumo_especifico_3])+','
        else:
            linea += ','
        
        #unidad_consumo_especifico_3 
        if not pandas.isnull(df.ix[i,unidad_consumo_especifico_3]):
            linea += df.ix[i,unidad_consumo_especifico_3].replace('[','').replace(']','')
        else:
            pass
        
            
        out.write(linea+'\n')


out.close()
