# -*- coding: utf-8 -*-
# Copyright 2016 The Switch-Chile Authors. All rights reserved.
# Licensed under the Apache License, Version 2, which is in the LICENSE file.
# Operations, Control and Markets laboratory at Pontificia Universidad
# Católica de Chile.

"""

Script to populate the timescales_population_timepoints table in the
switch_chile OCM database.  The only inputs required are the connection
parameters and the timeseries scenario id for which the timepoints want to be
populated.

"""

import psycopg2, sys
from getpass import getpass
from datetime import date, timedelta, time, datetime

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

###########################
population_ts_scenario_id = 2
number_weeks = 1560
ts_up = []

day = date(2015,1,1)
ts_id = 1
while day < date(2045,1,1):
    row=[]
    row.append(population_ts_scenario_id)
    row.append(ts_id)
    row.append(str(day))
    if day.year < 2025:
        row.append(1)
        row.append('2020')
    elif day.year >= 2025 and day.year < 2035:
        row.append(2)
        row.append('2030')
    else:
        row.append(3)
        row.append('2040')
    row.append(1)
    row.append(24)
    row.append(7)
    row.append(datetime.combine(day, time()))
    row.append('Day '+str(day))
    row.append(2)
    
    ts_up.append(row)
    
    ts_id += 1
    day += timedelta(days=7)

try:
    values_str = ','.join(cur.mogrify("(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", ts) for ts in ts_up)
    query_str = "INSERT INTO chile_new.timescales_population_timeseries VALUES"+values_str+";"
    cur.execute(query_str)
    con.commit()
    print "Inserted timeseries!"
except psycopg2.DatabaseError, e:
    if con:
        con.rollback()
    print 'Error %s' % e    
