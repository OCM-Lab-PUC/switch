# -*- coding: utf-8 -*-
# Copyright 2016 The Switch-Chile Authors. All rights reserved.
# Licensed under the Apache License, Version 2, which is in the LICENSE file.
# Operations, Control and Markets laboratory at Pontificia Universidad
# Católica de Chile.
"""

Cleans substation names for transmission lines and uploads inputs into
the database.

"""
import pandas, os, re, datetime, sys, psycopg2, numpy
from csv import reader
from unidecode import unidecode
from getpass import getpass

if sys.getdefaultencoding() != 'utf-8':
    # Character encoding may raise errors if set in ascii or other simple
    # encodings which do not support spanish characters.
    reload(sys)
    sys.setdefaultencoding('utf-8')

def limpiar(a):
    # Devuelvo un string limpio de carácteres anómalos, espacios y comas
    limpio = unidecode(a.replace(' ','_').replace('ó','o')).lower().replace(',','_').strip('_')
    return limpio
    
# Limpiamos el nombre de cosas para que queden en nuestro formato, borrando, dividiendo por los caracteres correspondientes
def Reciclar(a):
    a = limpiar(a)
    cortes = ['.circuito', '._circuito', ':', 'tap', ':_', '_i']
    for corte in cortes:
        if corte in a:
            # Obtener la segunda parte si es tap
            if not a.split(corte)[0]:
                a = limpiar(a.split(corte)[1])
            else:
                a = limpiar(a.split(corte)[0])
    return a

# Incluimos 2 posibles nombres y nos retorna si está en la lista y el nombre que tiene
def BuscarCorrecto(a1,a2,List):
    if Reciclar(a1) in List:
        return True, Reciclar(a1)
    if Reciclar(a2) in List:
        return True, Reciclar(a2) 
    if a1 in List:
        return True, a1
    if a2 in List:
        return True, a2   
    return False,''
    
def BuscarCorrectos(a1,a2,List):
    Encuentro = []
    if (Reciclar(a1) in List) and Reciclar(a1) not in Encuentro:
        Encuentro.append(Reciclar(a1))
    if Reciclar(a2) in List and Reciclar(a2) not in Encuentro:
        Encuentro.append(Reciclar(a2))
    if a1 in List and a1 not in Encuentro:
        Encuentro.append(a1)
    if a2 in List and a2 not in Encuentro:
        Encuentro.append(a2)   
    return Encuentro
    
# Traducimos a partir del nombre
def Traduce(a):
    for i in conversor.index:
        if conversor.ix[i,2] == a or conversor.ix[i,3] == a:
            return conversor.ix[i,0] 
    return a    
    
    
#Sacamos distancias para comparar
def Distancia(p1,p2):
    return numpy.power(p1[0]-p2[0],2) + numpy.power(p1[1]-p2[1],2)

# Abrimos los archivos, tener en cuenta si la primera linea es header o no
transmision = pandas.read_csv('transmision.csv', index_col=False)
centrales = pandas.read_csv('centrales.csv', index_col=False, header = None)
demandasic = pandas.read_csv('demandasic.csv', index_col=False)
demandasing = pandas.read_csv('demandasing.csv', index_col=False)
subestacionessic = pandas.read_csv('substations_sic.csv', header = None, index_col=False)
subestacionessing = pandas.read_csv('substations_sing.csv', header = None, index_col=False)
subestacionesplant = pandas.read_csv('substations_plants.csv', header = None, index_col=False)

conversor = pandas.read_excel('ConvSubest.xls', sheetname = 0, index_col=False)
similares = pandas.read_excel('Similares.xlsx', sheetname = 0, index_col=False)



# Creamos la lista de subestaciones total, añadiendo las del diccionario
All = []
Coordenadas = {}
subsSIC = []
subsSING = []

#Obtengo todas las centrales en una lista llamada All
#Correspondientemente, se asocian las coordenadas de cada una en el diccionario Coordenadas
#Las SE "reemplazo" del archivo de Conversion se les asocia la coordenada de la reemplazada

for i in subestacionessic.index:
    if subestacionessic.ix[i,0] not in All:
        All.append(subestacionessic.ix[i,0])
        Coordenadas[subestacionessic.ix[i,0]] = [subestacionessic.ix[i,3],subestacionessic.ix[i,4]]
        
    if subestacionessic.ix[i,0] not in subsSIC:
        subsSIC.append(subestacionessic.ix[i,0])
        

for i in subestacionessing.index:
    if subestacionessing.ix[i,0] not in All:
        All.append(subestacionessing.ix[i,0])
        Coordenadas[subestacionessing.ix[i,0]] = [subestacionessing.ix[i,3],subestacionessing.ix[i,4]]
        
    if subestacionessing.ix[i,0] not in subsSING:
        subsSING.append(subestacionessing.ix[i,0])

for i in subestacionesplant.index:
    if subestacionesplant.ix[i,0] not in All:
        All.append(subestacionesplant.ix[i,0])
        Coordenadas[subestacionesplant.ix[i,0]] = [subestacionesplant.ix[i,3],subestacionesplant.ix[i,4]]
        
    if (subestacionesplant.ix[i,0] not in subsSIC) and (subestacionesplant.ix[i,2] == 'sic'):
        subsSIC.append(subestacionesplant.ix[i,0])
        
    if (subestacionesplant.ix[i,0] not in subsSING) and (subestacionesplant.ix[i,2] == 'sing'):
        subsSING.append(subestacionesplant.ix[i,0])
        
        
for i in conversor.index:
    if (conversor['Demanda'][i] not in All) and not (pandas.isnull(conversor['Demanda'][i] )):
        All.append(conversor['Demanda'][i])
        Coordenadas[conversor['Demanda'][i]] = Coordenadas[conversor['SE'][i]] 
        
    if (conversor['Linea'][i] not in All) and not (pandas.isnull(conversor['Linea'][i] )):
        All.append(conversor['Linea'][i])
        Coordenadas[conversor['Linea'][i]] = Coordenadas[conversor['SE'][i]] 



#Lista de subestaciones que tienen nombre similar
ListaSimilar = []
ListaSimilares = {}

for j in similares.index:
    #Si no está, lo añadimos a una lista y diccionario
    if similares.ix[j,0] not in ListaSimilar:
        ListaSimilar.append(similares.ix[j,0])
        ListaSimilares[similares.ix[j,0]] = [similares.ix[j,0], similares.ix[j,1]]
    
    else:
        #Si ya está, añadimos el término que falta
        ListaSimilares[similares.ix[j,0]].append(similares.ix[j,1])
        

#Obtenemos las subestaciones de centrales, demandasic y demandasing que faltan

# CentEmpty = []
# for i in centrales.index:
#     subestacion = centrales.ix[i,7]
#     if subestacion in All:
#         pass
#         #print(subestacion,'está')
#     else:
#         if subestacion not in CentEmpty:
#             print(i)
#             CentEmpty.append(subestacion)
                        
#for i in demandasic.index:
#    subestacion = demandasic['SE'][i]
#    if subestacion in All:
#        pass
#    else:
#        if subestacion not in CentEmpty:
#            CentEmpty.append(subestacion)
#            
#for i in demandasing.index:
#    subestacion = demandasing[' barra'][i]
#    if subestacion in All:
#        pass
#    else:
#        if subestacion not in CentEmpty:
#            CentEmpty.append(subestacion)

###############################
######## TRANSMISION ##########
###############################

# Obtenemos las subestaciones de transmision que faltan
CentEmpty2 = []
VoltEmpty2 = []

NeoTransmision = pandas.DataFrame({'Sistema' : [], 'SE1' : [],'SE2' : [], 'Tension' : [],'Longitud' : [], 'Capacidad' : []})

for i in transmision.index:
    #Sacamos los nombres
    SE1 = transmision['SE1'][i]
    SE2 = transmision['SE2'][i]
    SEalt1 = transmision['SEalt1'][i]
    SEalt2 = transmision['SEalt2'][i]
    
    #Vemos si está, y si usa SE1 o SEalt1 o una version limpia de estos de nombre
    BC1 = BuscarCorrecto(SE1, SEalt1, All)
        
        
    #Variable para saber si es que esta
    esta = 1

    if BC1[0]:
        pass
    #Si no está, se añade a la lista de vacios (si es que no está en esta ya)
    else:
        esta = 0
        if SEalt1 not in CentEmpty2:
            CentEmpty2.append(SEalt1)
            VoltEmpty2.append([transmision['Tension (KV)'][i],transmision['Sistema'][i]])
    
    BC2 = BuscarCorrecto(SE2, SEalt2, All)
    
    
        
        
    
    if BC2[0]:
        pass
    else:
        esta = 0
        if SEalt2 not in CentEmpty2:
            esta = 0
            CentEmpty2.append(SEalt2)
            VoltEmpty2.append([transmision['Tension (KV)'][i],transmision['Sistema'][i]])
            
    
    #####################
    ####Similares########
    #####################    
    
    
    #Reviso si los nombres encontrados están en la lista de potenciales similar, siempre cuando existan ambos
    if (BC1[1] in ListaSimilar or BC2[1] in ListaSimilar) and BC1[0] and BC2[0]:
        
        #Añado los nombres similares a una lista
        if BC1[1] in ListaSimilar:
            ConjuntoBC1 = ListaSimilares[BC1[1]]
        #Si no tiene nombres similares, solo queda el mismo nombre
        else:
            ConjuntoBC1 = [BC1[1]]
            
        if BC2[1] in ListaSimilar:
            ConjuntoBC2 = ListaSimilares[BC2[1]]
        else:
            ConjuntoBC2 = [BC2[1]]
            
        #Propongo un candidato de minimo, tomando los primeros
        Minimo = [ConjuntoBC1[0], ConjuntoBC2[0]]
        Dminimo = Distancia(Coordenadas[ConjuntoBC1[0]], Coordenadas[ConjuntoBC2[0]]) 
        
        for A1 in ConjuntoBC1:
            for A2 in ConjuntoBC2:
                if Distancia(Coordenadas[A1], Coordenadas[A2]) < Dminimo:
                    Minimo = [A1, A2]
                    Dminimo = Distancia(Coordenadas[A1], Coordenadas[A2])
        
        #Si al menos uno de ellos cambia, reemplazamos
        if BC1[1] != Minimo[0] or BC2[1] != Minimo[1]:
            #print(BC1[1],',',BC2[1],'=>',Minimo[0],',',Minimo[1])
            BC1 = [BC1[0], Minimo[0]]
            BC2 = [BC2[0], Minimo[1]]
            
    #####################
            
            

    #Si esta, la añadimos a la nueva transmision
    if esta == 1:
        #Añadimos las fila correspondiente
        fila = pandas.DataFrame([[transmision['Sistema'][i], Traduce(BC1[1]),
                                Traduce(BC2[1]), transmision['Tension (KV)'][i],
                                transmision['Longitud (km)'][i],transmision['Capacidad (MVA)'][i]]],
                                columns=['Sistema', 'SE1', 'SE2', 'Tension','Longitud', 'Capacidad'])

        NeoTransmision = NeoTransmision.append(fila)
        
        #Si hay 2 lineas, las añadimos de nuevo
        if transmision['N'][i] == 2:
            NeoTransmision = NeoTransmision.append(fila)

# Guardar las subestaciones del archivo de transmision que no tienen
# una subestacion definida en nuestra BD. Debiesen ser solo puntos
# de consumo para los que su demanda ya fue referida a alguna otra
# subestacion que sí existe.
with open('substations_without_lines.txt', 'w') as f:
    for i, sub in enumerate(CentEmpty2):
        f.write('%s %s\n' % (sub, VoltEmpty2[i][0]))

# Generamos el nuevo csv con las lineas definidas segun subestaciones
# que existen en nuestra BD
NeoTransmision.to_csv('NeoTransmision.csv', index = None, float_format = '%.2f', cols=['Sistema', 'SE1', 'SE2', 'Tension','Longitud', 'Capacidad'])


##############################
####### UPLOAD TO DB #########

lines_for_db = []
with open('NeoTransmision.csv', 'r') as f:
    read = reader(f)
    # Read headers, because order is changing by some weird reason
    headers = read.next()
    system_index = headers.index('Sistema')
    capacity_index = headers.index('Capacidad')
    for row in read:
        lines_for_db.append(row)
for row in lines_for_db:
    # Remove system
    row.pop(system_index)
    # If no capacity info, set to 0
    if row[capacity_index] == 'S/I':
        row[capacity_index] = 0
        
##############
# DB Conection

username = 'bmaluenda'
passw = getpass('Enter database password for user %s' % username)

try:
    # Remember to enter and/or modify connection parameters accordingly to your
    # setup
    con = psycopg2.connect(database='switch_chile', user=username, 
                            host='localhost', port='5915',
                            password=passw)
    print ("Connection to database established...")
except:
    sys.exit("Error connecting to the switch_chile database...")

cur = con.cursor()

keep_going = True

# Clean database
try:
    cleaning = "DELETE FROM chile_new.geo_transmission_lines"
    cur.execute(cleaning)
    print("Table erased")
except psycopg2.DatabaseError as e:
    if con:
        con.rollback()
    print(e)
    keep_going = False

if keep_going:
    # Load new data
    try:
        values_str = ','.join(cur.mogrify("(%s,%s,%s,%s,%s)",
            line) for line in lines_for_db)
        query_str = "INSERT INTO chile_new.geo_transmission_lines (capacity_mw_cdec,length_km_cdec,substation_1, substation_2, db_voltage) VALUES "+values_str+";"
        cur.execute(query_str)
        con.commit()
        print ("New transmission line data has been uploaded to the DB.")
    except psycopg2.DatabaseError as e:
        if con:
            con.rollback()
        print(e)
        keep_going = False

if keep_going:        
    # Remove duplicate lines
    try:
        query_str = "DELETE FROM chile_new.geo_transmission_lines WHERE transmission_line_id IN (SELECT transmission_line_id FROM (SELECT transmission_line_id, ROW_NUMBER() OVER (partition BY db_voltage, capacity_mw_cdec, substation_1, substation_2 ORDER BY transmission_line_id) AS rnum FROM chile_new.geo_transmission_lines) t WHERE t.rnum > 1);"
        cur.execute(query_str)
        con.commit()
        print ("Transmission line duplicates have been cleaned.")
    except psycopg2.DatabaseError as e:
        if con:
            con.rollback()
        print(e)
        
    # Update geometry columns with new coordinates
    try:
        query_str = "UPDATE chile_new.geo_transmission_lines as Tx SET geom_s1 = s1.geom FROM chile_new.geo_substations AS s1 WHERE Tx.substation_1 = s1.db_name"
        cur.execute(query_str)
        con.commit()
        print ("Updated geometry column for substation 1 with new data.")
    except psycopg2.DatabaseError as e:
        if con:
            con.rollback()
        print(e)
    try:    
        query_str = "UPDATE chile_new.geo_transmission_lines as Tx SET geom_s2 = s2.geom FROM chile_new.geo_substations AS s2 WHERE Tx.substation_2 = s2.db_name"
        cur.execute(query_str)
        con.commit()
        print ("Updated geometry column for substation 2 with new data.")
    except psycopg2.DatabaseError as e:
        if con:
            con.rollback()
        print(e)
    try:    
        query_str = "UPDATE chile_new.geo_transmission_lines SET geom = ST_MAKELINE(geom_s1,geom_s2)"
        cur.execute(query_str)
        con.commit()
        print ("Updated geometry column for the transmission lines with new data.")
    except psycopg2.DatabaseError as e:
        if con:
            con.rollback()
        print(e)
    
if cur:
    cur.close()
if con:
    con.close()

