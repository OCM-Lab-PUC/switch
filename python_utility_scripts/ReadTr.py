# -*- coding: utf-8 -*-
# Operations, Control and Markets laboratory at Pontificia Universidad
# Católica de Chile. July 2016.

import pandas, os, re, datetime, sys
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

def SepararLineaSIC(a):
    #Algunos nombres separan 220 KV en vez de 220KV, hacemos este cambio para que queden igual
    a = a.replace('k','K').replace('v','V').replace(' KV','KV')
    try:
        #Divido por guion y obtengo primer elemento
        se1 = limpiar(a.split('-')[0])
        #Obtengo 220kv al eliminar el ultimo termino con espacio y se lo quito al string, luego divido por guion
        se2 = limpiar(a.replace(a.split(' ')[-1],'').split('-')[1])
        return [se1,se2]
    except:
        print('No es posible separar',a)
        return [limpiar(a),limpiar(a)]

def SepararLineaSIC2(a):
    a = a.replace('k','K').replace('v','V').replace(' KV','KV')
    try:
        #Divido por guion y obtengo primer elemento
        se1 = limpiar(a.split('-')[0])
        #Obtengo 220kv al eliminar el ultimo termino con espacio y se lo quito al string, luego divido por guion
        se2 = limpiar(' '.join(a.split('-')[1].split('KV')[0].split(' ')[:-1]))
        return [se1,se2]
    except:
        print('No es posible separar',a)
        return [limpiar(a),limpiar(a)]
        
def SepararLineaSING(a):
    try:
        a = a.split('kV ')[1]
        #Divido por guion y obtengo primer elemento
        se1 = limpiar(a.split('-')[0])
        #Obtengo 220kv al eliminar el ultimo termino con espacio y se lo quito al string, luego divido por guion
        se2 = limpiar(a.split('-')[1])
        return [se1,se2]
    except:
        print('No es posible separar',a)
        return [limpiar(a),limpiar(a)]


###############################
# Obtenemos los datos del SIC #
###############################


#Archivo de conversion de unidades a abrir
transmision = pandas.read_excel('capacidad_instalada_de_transmision.xlsx', sheetname= 'SIC', parse_cols = 'E:K', skiprows=6)
transmision.columns = ['SE','Tramo','dsa','Tension (KV)', 'N','Longitud (km)','Capacidad (MVA)']
#Obtenemos las columnas
#for i,j in enumerate(transmision.columns.values):
#    print(limpiar(j),'=',i)

linea = 0
tramo = 1
tension = 3
numerocircuitos = 4
longitud = 5
capacidad = 6

#Construimos un data frame de dos columnas, de subestaciones por linea
SE = pandas.DataFrame({'SE1' : [],'SE2' : [], 'SEalt1' : [],'SEalt2' : []})

for i in transmision.index:
    #Mientras leamos
    if pandas.isnull(transmision.ix[i,linea]):
        break
    subs = SepararLineaSIC2(transmision.ix[i,tramo])
    subs2 = SepararLineaSIC(transmision.ix[i,linea])
    #print(subs,subs2)
    fila = pandas.DataFrame([[subs[0],subs[1], subs2[0], subs2[1]]], columns=['SE1','SE2','SEalt1','SEalt2'])
    SE = SE.append(fila, ignore_index = True)
    
#Hacemos la nueva matriz con las subestaciones, voltaje y 
neotransmision = pandas.concat([pandas.Series(['sic' for i in range(i)], name = 'Sistema'),  SE.ix[:i,0], SE.ix[:i,1], SE.ix[:i,2], SE.ix[:i,3], transmision.ix[:i-1,3], transmision.iloc[:i,4], transmision.iloc[:i,5], transmision.iloc[:i,6]], names = None, axis = 1)


################################
# Obtenemos los datos del SING #
################################

#Leemos, eliminando las dos primeras lineas correspondientes al header (celdas agrupadas no se leen bien...)
transmision = pandas.read_excel('capacidad_instalada_de_transmision.xlsx', sheetname= 'SING', parse_cols = 'E:J', skiprows=6,header = None)
transmision = transmision[2:].reset_index(drop = True)
linea = 0
tension = 1
numerocircuitos = 2
longitud = 3
capacidad = 5


#Construimos un data frame de dos columnas, de subestaciones por linea
SE = pandas.DataFrame({'SE1' : [],'SE2' : [], 'SEalt1' : [],'SEalt2' : []})

for i in transmision.index:
    #Mientras leamos
    if pandas.isnull(transmision.ix[i,linea]):
        break
    
    subs = SepararLineaSING(transmision.ix[i,linea])
    fila = pandas.DataFrame([[subs[0],subs[1],subs[0],subs[1]]], columns=['SE1','SE2','SEalt1','SEalt2'])
    SE = SE.append(fila, ignore_index = True) 
    
    #Si no tiene limite, le asignamos la capacidad
    if transmision.ix[i,capacidad] == 'N/I' or pandas.isnull(transmision.ix[i,capacidad]):
        transmision.ix[i,capacidad] = transmision.ix[i,4]
    

    
#Hacemos la nueva matriz con las subestaciones, voltaje y 
neotransmision2 = pandas.concat([pandas.Series(['sing' for i in range(i)], name = 'Sistema'), SE.ix[:i,0], SE.ix[:i,1], SE.ix[:i,0], SE.ix[:i,1], transmision.ix[:i,tension], transmision.ix[:i,numerocircuitos], transmision.iloc[:i,longitud], transmision.iloc[:i,capacidad]], names = None, axis = 1)
neotransmision2 = neotransmision2[:-1]

#Renombramos columnas
neotransmision2.columns = ['Sistema','SE1','SE2','SEalt1','SEalt2','Tension (KV)', 'N','Longitud (km)','Capacidad (MVA)']

#Unimos ambas 
transmisionfinal = pandas.concat([neotransmision, neotransmision2])

#Convertimos filas a int
transmisionfinal[['Tension (KV)', 'N']] = transmisionfinal[['Tension (KV)', 'N']].astype(int)


#Imprimimos datos
transmisionfinal.to_csv('transmision.csv', index = None , float_format = '%.2f')

