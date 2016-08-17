# -*- coding: utf-8 -*-
from __future__ import division
# Copyright 2016 The Switch-Chile Authors. All rights reserved.
# Licensed under the Apache License, Version 2, which is in the LICENSE file.
# Operations, Control and Markets laboratory at Pontificia Universidad
# Católica de Chile.

"""



"""

import psycopg2, sys
from getpass import getpass

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

costs = []
for i in range(30):
    year = 2015 + i
    costs.append([1,'CCGT',23,year,946,13.6])
    costs.append([1,'OCGT',30,year,1000,7.5])
    costs.append([1,'Coal_Steam_Turbine',25,year,3050,32.2])
    costs.append([1,'Diesel_Combustion_Turbine',28,year,946,13.6])
    costs.append([1,'PV',32,year,2100,25])
    costs.append([1,'Wind',34,year,2300,40])
    costs.append([1,'Hydro_Dam',36,year,3100,14])
    costs.append([1,'Hydro_RoR',38,year,3400,14])
    costs.append([1,'Hydro_Series',39,year,3400,14])

try:
    values_str = ','.join(cur.mogrify("(%s,%s,%s,%s,%s,%s)", cost) for cost in costs)
    query_str = "INSERT INTO chile_new.generator_yearly_costs VALUES"+values_str+";"
    cur.execute(query_str)
    con.commit()
    print "Inserted costs!"
except psycopg2.DatabaseError, e:
    if con:
        con.rollback()
    print 'Error %s' % e    


if cur:
    cur.close()
if con:
    con.close()
