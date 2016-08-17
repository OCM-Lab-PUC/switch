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
from calendar import monthrange

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

def add_months(sourcedate,months):
     month = sourcedate.month - 1 + months
     year = int(sourcedate.year + month / 12 )
     month = month % 12 + 1
     day = min(sourcedate.day,monthrange(year,month)[1])
     return date(year,month,day)


###########################
# Population: 1 day hourly res. per month
###########################
population_ts_scenario_id = 4
ts_up = []

day = date(2015,1,15)
ts_id = 394
while day < date(2045,1,1):
    row=[]
    row.append(population_ts_scenario_id)
    row.append(ts_id)
    row.append(str(day)+'_hourly')
    
    if day.year < 2020:
        row.append(6)
        row.append('2017')
    elif day.year >= 2020 and day.year < 2025:
        row.append(7)
        row.append('2022')
    elif day.year >= 2025 and day.year < 2030:
        row.append(8)
        row.append('2027')
    elif day.year >= 2030 and day.year < 2035:
        row.append(9)
        row.append('2032')
    elif day.year >= 2035 and day.year < 2040:
        row.append(10)
        row.append('2037')
    else:
        row.append(11)
        row.append('2042')
    
    row.append(1)
    row.append(24)
    row.append(365)
    row.append(datetime.combine(day, time()))
    row.append('Day '+str(day)+' hourly')
    row.append(3)
    
    ts_up.append(row)
    
    ts_id += 1
    day = add_months(day,1)

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
