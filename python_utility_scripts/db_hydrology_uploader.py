# -*- coding: utf-8 -*-
from __future__ import division
# Copyright 2016 The Switch-Chile Authors. All rights reserved.
# Licensed under the Apache License, Version 2, which is in the LICENSE file.
# Operations, Control and Markets laboratory at Pontificia Universidad
# Católica de Chile.

"""



"""

import psycopg2, datetime, sys
from getpass import getpass
from csv import reader
from unidecode import unidecode
from datetime import date, timedelta

def clean_name(a):
    clean = unidecode(a.replace(' ','_')).lower().replace(',','_').replace('.','').replace('(','_').replace(')','_').replace(
        '__','_').strip('_')
    return clean

username = 'bmaluenda'
passw = getpass('Enter database password for user %s' % username)

try:
    # Remember to enter and/or modify connection parameters accordingly to your
    # setup
    con = psycopg2.connect(database='switch_chile', user=username, 
                            host='localhost', port='5915',
                            password=passw)
    print "Connection to database established..."
except:
    sys.exit("Error connecting to the switch_chile database...")
"""
hyd = []
with open('afluentes_procesados.csv', 'r') as f:
        read = reader(f)
        read.next()
        for row in read:
            hyd.append(row)

# CAREFUL: Hydrologies go from April to March
hyd_up = []
days_of_year = []
# Choose a non-leap year
delta = date(2015,4,1) - date(2014,4,1)
for day in range(delta.days):
    days_of_year.append(date(2014,4,1) + timedelta(days=day))
for row in hyd:
    for day in days_of_year:
        if day.month >= 4:
            first_col_of_month = 3 + (day.month - 4) * 4
        else:
            first_col_of_month = 39 + (day.month - 1) * 4
        
        # Assign flow according to position in month
        if day.month != 12:
            days_in_month = (date(2014, day.month + 1, 1) - date(2014,day.month,1)).days
        else:
            days_in_month = 31    
            
        if day.day / days_in_month <= 0.25:
            i = 0
        elif day.day / days_in_month > 0.25 and day.day / days_in_month <= 0.5:
            i = 1
        elif day.day / days_in_month > 0.5 and day.day / days_in_month <= 0.75:
            i = 2
        else:
            i = 3
        
        flow = row[first_col_of_month + i]
        
        hyd_up.append([row[0],row[2],clean_name(row[1]), flow, row[0]+'-'+str(day.month)+'-'+str(day.day)])

hyd_ror = []
with open('hidrologias_faltantes.csv', 'r') as f:
        read = reader(f)
        read.next()
        for row in read:
            hyd_ror.append(row)

# CAREFUL: Hydrologies are monthly. Only upload 1 day.
hyd_ror_up = []
months_of_year = []
for i in range(12):
    months_of_year.append(date(2014,i+1,1))
for row in hyd_ror:
    for date in months_of_year:
        flow = row[2 + date.month]
        hyd_ror_up.append([row[0],row[2],clean_name(row[1]),flow,row[0]+'-'+str(date.month)+'-01'])


cur = con.cursor()


try:
    values_str = ','.join(cur.mogrify("(%s,%s,%s,%s,%s)", hyd) for hyd in hyd_up)
    query_str = "INSERT INTO chile_new.hydrologies (hyd_year, hyd_num, flow_name, flow, year_month_day) VALUES"+values_str+";"
    cur.execute(query_str)
    con.commit()
    print "Inserted hydrologies!"
except psycopg2.DatabaseError, e:
    if con:
        con.rollback()
    print 'Error %s' % e    

try:
    values_str = ','.join(cur.mogrify("(%s,%s,%s,%s,%s)", hyd_ror) for hyd_ror in hyd_ror_up)
    query_str = "INSERT INTO chile_new.hydrologies (hyd_year, hyd_num, flow_name, inflow, year_month_day) VALUES"+values_str+";"
    cur.execute(query_str)
    con.commit()
    print "Inserted hydrologies!"
except psycopg2.DatabaseError, e:
    if con:
        con.rollback()
    print 'Error %s' % e  

"""
hyd_ang = []
with open('hidrologias_pasada.csv', 'r') as f:
        read = reader(f)
        hyd_ang.append(next(read))
        #for row in read:
        #    hyd_ang.append(row)

# CAREFUL: Hydrology is monthly. Only upload 1 day.
hyd_ang_up = []
months_of_year = []
for i in range(12):
    months_of_year.append(date(2014,i+1,1))
for row in hyd_ang:
    for date in months_of_year:
        flow = row[2 + date.month]
        hyd_ang_up.append([row[0],row[2],clean_name(row[1]),flow,row[0]+'-'+str(date.month)+'-01'])
        

cur = con.cursor()
try:
    values_str = ','.join(cur.mogrify("(%s,%s,%s,%s,%s)", hyd_ang) for hyd_ang in hyd_ang_up)
    query_str = "INSERT INTO chile_new.hydrologies (hyd_year, hyd_num, flow_name, inflow, year_month_day) VALUES"+values_str+";"
    cur.execute(query_str)
    con.commit()
    print "Inserted hydrologies!"
except psycopg2.DatabaseError, e:
    if con:
        con.rollback()
    print 'Error %s' % e  
"""    
    
    
    

hyd_ang_weekly = []
with open('hidrologia_angostura.csv', 'r') as f:
        read = reader(f)
        read.next()
        for row in read:
            hyd_ang_weekly.append(row)
# CAREFUL: Hydrology is weekly and is averaged to upload only 1 datus monthly.
hyd_ang_up = []
months_of_year = []
hyd_ang_monthly = []
for i in range(12):
    months_of_year.append(date(2014,i+1,1))
    
for nrow,row in enumerate(hyd_ang_weekly):
    for col in range(3):
        if len(hyd_ang_monthly) == 0:
            hyd_ang_monthly.append([row[col]])
        else:
            hyd_ang_monthly[nrow].append(row[col])
    for m in range(12):
        hyd_ang_monthly[nrow].append((float(row[3+m*4])+float(row[4+m*4])+float(row[5+m*4])+float(row[6+m*4]))/4)
    
for row in hyd_ang_monthly:
    for date in months_of_year:
        flow = row[2 + date.month]
        hyd_ang_up.append([row[0],row[2],clean_name(row[1]),flow,row[0]+'-'+str(date.month)+'-01'])
try:
    values_str = ','.join(cur.mogrify("(%s,%s,%s,%s,%s)", hyd_ang) for hyd_ang in hyd_ang_up)
    query_str = "INSERT INTO chile_new.hydrologies (hyd_year, hyd_num, flow_name, inflow, year_month_day) VALUES"+values_str+";"
    cur.execute(query_str)
    con.commit()
    print "Inserted hydrologies!"
except psycopg2.DatabaseError, e:
    if con:
        con.rollback()
    print 'Error %s' % e  
"""
if cur:
    cur.close()
if con:
    con.close()
