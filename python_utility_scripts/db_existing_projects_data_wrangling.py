# -*- coding: utf-8 -*-
# Copyright 2016 The Switch-Chile Authors. All rights reserved.
# Licensed under the Apache License, Version 2, which is in the LICENSE file.
# Operations, Control and Markets laboratory at Pontificia Universidad
# Católica de Chile.
"""

Fetches data for existing projects in the Chilean Interconected Systems and 
wrangles with it to upload a clean and updated edition to the database.

"""

import os, re, sys
import pandas as pd
from csv import writer
from pyproj import Proj, transform
from unidecode import unidecode

if sys.getdefaultencoding() != 'utf-8':
    # Character encoding may raise errors if set in ascii or other simple
    # encodings which do not support spanish characters.
    reload(sys)
    sys.setdefaultencoding('utf-8')

def limpiar(a):
    # Devuelvo un string limpio de carácteres anómalos, espacios y comas
    limpio = unidecode(a.replace(' ','_').replace('ó','o')).lower().replace(',','_')
    while limpio[0] == '_':
        limpio = limpio[1:]
    while limpio[-1] == '_':
        limpio = limpio[:-1]
    return limpio
    
###############################
# Uni conversion function
conversion = pd.read_excel('conversion.xls', sheetname= 0, parse_cols = 'A:E')


   
#conversion = pandas.read_excel('ConvUnid.xls', sheetname= 0, parse_cols = 'A:E')
    
def ConvUnid(a,b,c):
    #Entrego las unidades respectivas de combustibles según el archivo conversion.xls
    for i in conversion.index:
        #Si encuentro
        if conversion.ix[i,0] == a and conversion.ix[i,1] == c:
            #Y no es nulo
            if not pd.isnull(conversion.ix[i,4]):
                return [conversion.ix[i,2],conversion.ix[i,4],conversion.ix[i,3]]
    print('Factor de',a,c,'no encontrado')        
    return [a,b,c]    
 
###############################
# Minimum power functions  
   
detallesic = pd.read_excel('sic.xlsx', sheetname=0, skiprows = 3)




#Eliminamos los ultimos dos digitos si es que el último es número: Abanico 1 -> Abanico
for i in detallesic.index:
    if detallesic.ix[i,17][-1].isdigit():
        detallesic.ix[i,17] = detallesic.ix[i,17][:-2]
    
#Buscamos el minimo dependiendo del sistema y central
def Minimo(system, central):
    centsic = 17
    pminsic = 23
    if central[-1].isdigit():
        central = central[:-2]
    
    #No hay datos de potencias mínimas en el sing
    if system == 'SING':
        return 0
        
    if system == 'SIC':
        #Buscamos en la planilla SIC
        for i in detallesic.index:
            #Si la encontramos
            if central in limpiar(detallesic.ix[i,centsic]):
                #Cambiamos las ',' por '.' si es que es string
                minimo = detallesic.ix[i,pminsic]
                if isinstance(minimo,str):
                    minimo = minimo.replace(',','.')
                    if minimo == 'cero':
                        return 0
                if pd.isnull(minimo):
                    print('Minimo de',central,'es nan')
                    return 0
                    
                try:
                    return float(minimo)
                except:
                    pass 
                
                print('Minimo de',central,'no es reconocible:',minimo)
                return 0
                
    print('Minimo de', central,'no fue encontrado')       
    return 0

###############################
# Plant locations

#
#Asociar barras
#2 Input: archivo con subestaciones y archivo con diccionario de subestaciones para buscar
subestaciones = pd.read_csv('geo_substation.csv', header= None)
convsub = pd.read_excel('ConvSubest.xls', 0)
#Busco la subestación correspondiente a la central para ver si está asociada en el archivo de subestaciones
def BarraCent(barra):
    #Buscamos en el excel de subestaciones
    for i in subestaciones.index:
        if limpiar(subestaciones.ix[i,0]) == barra or barra in limpiar(subestaciones.ix[i,0]):
            return True
    #Si no está, buscamos en el excel de conversión
    for i in convsub.index:
        if limpiar(convsub.ix[i,0]) == barra or barra in limpiar(convsub.ix[i,0]):
            for j in subestaciones.index:
                if limpiar(convsub.ix[i,1]) == limpiar(subestaciones.ix[j,0]):
                    return True
    return False
    
    

out = open('centrales.csv', 'w')
    
# Not all projects have coordinates in the main CNE file. Some are present
# in the hydro power plant spreadsheet.
df_hydro = pd.read_excel('Centrales_Hidro.xlsx')
df_hydro['nombre']=df_hydro['nombre'].map(lambda name: limpiar(name))

# Each list has plant name, Easting, Northing and UTM zone.
locations = [
    ['conejo_solar', '382994.65','7179364','19'],
    ['carilafquen', '281349', '5693183', '19'],
    ['el_molle', '253996', '6335965', '19'],
    ['las_araucarias', '340242', '6310766', '19'],
    ['malalcahuello', '283631', '5689411', '19'],
    ['mch_dosal', '336570', '6038143', '19'],
    ['molinera_villarrica', '739004', '5648107', '18'],
    ['pampa_solar_norte','379886', '7174683', '19'],
    ['parque_eolico_la_esperanza', '717384', '5835235', '18'],
    ['parque_eolico_renaico','713505','5821781', '18'],
    ['parque_fotovoltaico_lagunilla', '297545', '6623494', '19'],
    ['raso_power', '738940', '6080034', '18'],
    ['salmofood_i', '600940', '5296061', '18'],
    ['salmofood_ii', '600940', '5296061', '18'],
    ['solar_la_silla', '331024', '6762397', '19']
]

# Proyection engines to transform UTM coordinates into a single zone: 18S.
projection_UTM18S = Proj('+init=EPSG:32718')
projection_UTM19S = Proj('+init=EPSG:32719')

for row in locations:
    if row[3] == '19':
        row[1], row[2] = (str(coord) for coord in transform(projection_UTM19S,
                        projection_UTM18S, row[1], row[2]))

# Some plants are tiny distributed generators (under 300 kW) and I haven't
# been able to find them. Skip them and don't even write them to the CSV.
skip_list = [
    'panguipulli',
    'solar_hornitos',
    'pmgd_pica_pilot',
    'tamm'
]

###############################
# CSV columns

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

# Auxiliar set
conjunto = []
comb = [[20,21,22], [23,24,25], [26,27,28]]

# Initialize writer
out = open('centrales.csv', 'w')
csv_writer = writer(out, delimiter = ',')



# Guardamos en un set las centrales con barra huacha
huacho = []

# Abrimos el excel correspondiente
for sheet in ['SING','SIC']:
    df = pd.read_excel('Capacidad_Instalada.xlsx', sheetname= sheet, skiprows = 1, parse_cols = 'B:AJ')
    
    for i in df.index:
        #Terminamos si la central no tiene sistema (fin de excel)
        if df.ix[i,sistema] != df.ix[0,sistema]:
            break

        #Empezamos un string de linea en el que añadiremos las cosas para luego imprimir
        linea = ''
        
        for j in comb:
            try:
                if df.ix[i,j[0]]+','+df.ix[i,j[2]] not in conjunto:
                    conjunto.append(df.ix[i,j[0]]+','+df.ix[i,j[2]])  
            except:
                pass
        
        # Done reading when no more rows are available
        if pd.isnull(df.ix[i,sistema]):
            break
       
        # Plant/project name
        name = limpiar(df.ix[i,central])
        
        # Skip this plant if it corresponds to tiny distributed generation
        # which don't have coordinates yet.
        if name in skip_list:
            continue
            
        
        system = limpiar(df.ix[i,sistema])
                
        energy_source = limpiar(df.ix[i,tipo_de_energia])
        
        if sheet == 'SIC':
            # Plants are grouped by units only in the SIC sheet
            units = str(df.ix[i,unidades])
        else:
            units = '1'
            
        if df.ix[i,fecha_puesta_en_servicio_central] != '-':
            date = str(df.ix[i,fecha_puesta_en_servicio_central])
        else:
            # If date is not specified, June 1st is written. Projects without
            # start dates are usually in testing phase and soon to begin
            # regular operations.
            date = '2016-06-01 00:00:00'
            
        net_power = str(df.ix[i,potencia_neta])
        
        min_power = str(Minimo(sheet,
            limpiar(df.ix[i,central].replace('U',''))))
        
        # Bus bar names must be cleaned, removing the 'SE' prefix and the
        # kV units. Underscores are ordered and cleaned as well.
        busbar = letras.sub('',limpiar(df.ix[i,punto_de_conexion])).replace('kv','').replace('se','').replace('__','_').strip('_')
        
        # Coordinates must be in UTM WGS-84 format for Zone 18S.
        if df.ix[i, huso] == 19:
            # Transform projection from zone 19 to 18.
            coords = tuple(str(coord) for coord in transform(projection_UTM19S,
                        projection_UTM18S, df.ix[i, este], df.ix[i, norte]))

        #Potencia minima, usamos la función para buscar en el excel correspondiente
        linea += str(Minimo(sheet ,limpiar(df.ix[i,central].replace('U',''))))+','
            
        #Añadimos la barra correspondiente, limpiando los caracteres, eliminando 'kv' y 'se'
        barra = letras.sub('',limpiar(df.ix[i,punto_de_conexion])).replace('kv','').replace('se','').replace('__','_')
        
        #Eliminamos '_' si es que están al inicio y al final
        if barra[0] == '_':
            barra = barra[1:]
        if barra[-1] == '_':
            barra = barra[:-1]
        
        print(df.ix[i,central],'barra',BarraCent(barra))
        if not BarraCent(barra):
            huacho.append(barra)
            
        linea += str(barra)+','
        
        # Coordinates must be in UTM WGS-84 format for Zone 18S.
        if df.ix[i, huso] == 19:
            coords = (str(coord) for coord in transform(projection_UTM19S,
                            projection_UTM18S, df.ix[i, este], df.ix[i, norte]))
                            
        elif df.ix[i,huso] == 18:
            coords = (str(df.ix[i, este]), str(df.ix[i, norte]))
        else:
            # Try to find the plant in the hydro spreadsheet.
            hydro_plant = df_hydro[df_hydro.nombre 
                == limpiar(df.ix[i,central])]
            if not hydro_plant.empty:
                row_index = hydro_plant.index[0]
                coords = (hydro_plant['Coordenada Este'][row_index].replace(
                        ',','.'), 
                    hydro_plant['Coordenada Norte'][row_index].replace(
                        ',','.'))
            # If not found, use manually inputted location.
            else:
                for location in locations:
                    if location[0] == limpiar(df.ix[i,central]):
                        coords = (location[1], location[2])
 
        #Iteramos sobre los 3 tipos de combustibles posibles, 
        # de las columnas correspondientes
        #Llamando a la función que los convierte
        #Si no encuentra, la función retorna los mismos valores
        #Si no hay valores, se omiten
        factors = []    
        for j in [[20,21,22], [23,24,25], [26,27,28]]:
            if not pd.isnull(df.ix[i,j[0]]) and not pd.isnull( df.ix[i,j[1]]) and df.ix[i,j[1]] != 'Sin Información' and df.ix[i,j[1]] != 'SIn Información':
                Factor = ConvUnid(df.ix[i,j[0]], df.ix[i,j[1]], df.ix[i,j[2]])
                factors.append((limpiar(str(Factor[0])), 
                    str(df.ix[i,j[1]]*Factor[1]), str(Factor[2])))
            else:
                factors.append(('','',''))                
        
        csv_writer.writerow([system, name, energy_source, units, date,
         net_power, min_power, busbar, coords[0], coords[1], factors[0][0], 
            factors[0][1], factors[0][2], factors[1][0], factors[1][1],
            factors[1][2], factors[2][0], factors[2][1], factors[2][2]])    

            
        #print(linea+'\n')


out.close()
