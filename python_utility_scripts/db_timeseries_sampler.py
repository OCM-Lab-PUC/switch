# -*- coding: utf-8 -*-
# Copyright 2016 The Switch-Chile Authors. All rights reserved.
# Licensed under the Apache License, Version 2, which is in the LICENSE file.
# Operations, Control and Markets laboratory at Pontificia Universidad
# Católica de Chile.

"""


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


try:
    query_str = "insert into chile_new.timescales_sample_timeseries  select population_ts_scenario_id, population_ts_id, population_ts_name, population_ts_id, num_timepoints, scaling_to_period, initial_timestamp, notes from chile_new.timescales_population_timeseries where population_ts_scenario_id = 4;"
    cur.execute(query_str)
    con.commit()
    print "Inserted timeseries!"
except psycopg2.DatabaseError, e:
    if con:
        con.rollback()
    print 'Error %s' % e    
