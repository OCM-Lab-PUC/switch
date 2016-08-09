# -*- coding: utf-8 -*-
# Copyright 2016 The Switch-Chile Authors. All rights reserved.
# Licensed under the Apache License, Version 2, which is in the LICENSE file.
# Operations, Control and Markets laboratory at Pontificia Universidad
# Católica de Chile.

"""

Creates a yearly profile for different renewable sources with hourly
resolution.

"""

import psycopg2, datetime, sys
from getpass import getpass

current_timestamp = datetime.datetime(2014,1,1,0,0)
delta = datetime.timedelta(hours = 1)

solar_profile = []
wind_profile = []
hydroror_profile = []
#Create simple profiles
while current_timestamp < datetime.datetime(2015,1,1,0,0):
    # Simple solar profile
    if current_timestamp.hour in [20,21,22,23,0,1,2,3,4,5,6,7]:
        solar_factor = 0
    elif current_timestamp.hour in [8,9,10,16,17,18,19]:
        solar_factor = 0.4
    else:
        solar_factor = 0.8
    
    # Wind blows only at night
    if current_timestamp.hour in [20,21,22,23,0,1,2,3,4,5,6,7]:
        wind_factor = 0.8
    else:
        wind_factor = 0.2
        
    # Hydro ror generates more in winter
    if current_timestamp.month in [11,12,0,1,2,3]:
        hydroror_factor = 0.5
    else:
        hydroror_factor = 1
    
    solar_profile.append(['PV',current_timestamp,solar_factor,99999])
    wind_profile.append(['Wind',current_timestamp,wind_factor,999999])
    hydroror_profile.append(['Hydro_RoR',current_timestamp,hydroror_factor,9999999])
    
    current_timestamp += delta
    

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
    
cur = con.cursor()

solar_str = ','.join(cur.mogrify("(%s,%s,%s,%s)", tuple(row)) for row in solar_profile)
wind_str = ','.join(cur.mogrify("(%s,%s,%s,%s)", tuple(row)) for row in wind_profile)
hydroror_str = ','.join(cur.mogrify("(%s,%s,%s,%s)", tuple(row)) for row in hydroror_profile)

# Clean existing factors
try:
    query = "DELETE FROM chile_new.variable_capacity_factors_existing WHERE project_name = 'PV' OR project_name = 'Wind' OR project_name = 'Hydro_RoR';"
    cur.execute(query)
    con.commit()
    print "Deleted existing profiles"
except psycopg2.DatabaseError, e:
    if con:
        con.rollback()
    print 'Error %s' % e 

try:
    query = "INSERT INTO chile_new.variable_capacity_factors_existing VALUES "+solar_str+";"
    cur.execute(query)
    con.commit()
    print "Query for inserting solar profile has been successful"
except psycopg2.DatabaseError, e:
    if con:
        con.rollback()
    print 'Error %s' % e 
try:
    query = "INSERT INTO chile_new.variable_capacity_factors_existing VALUES "+wind_str+";"
    cur.execute(query)
    con.commit()
    print "Query for inserting wind profile has been successful"
except psycopg2.DatabaseError, e:
    if con:
        con.rollback()
    print 'Error %s' % e  
try:
    query = "INSERT INTO chile_new.variable_capacity_factors_existing VALUES "+hydroror_str+";"
    cur.execute(query)
    con.commit()
    print "Query for inserting hydro ror profile has been successful"
except psycopg2.DatabaseError, e:
    if con:
        con.rollback()
    print 'Error %s' % e     

if cur:
    cur.close()
if con:
    con.close()


