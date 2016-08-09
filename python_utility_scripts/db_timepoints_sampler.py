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

# The timeseries scenario id must be inputted to generate the timepoints
# corresponding to that set
sample_ts_scenario_id = 2

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
cur.execute("SELECT * FROM chile_new.timescales_sample_timeseries WHERE sample_ts_scenario_id = %s ORDER BY 2" % sample_ts_scenario_id)
timeseries_table = cur.fetchall()

for row in timeseries_table:

    initial_timestamp = row[6]
    sample_ts_id = row[1]
    population_ts_id = row[3]
    num_tps = row[4]

    rows_to_insert = []

    # Populate timepoints
    cur.execute("SELECT * FROM chile_new.timescales_population_timepoints WHERE population_ts_id = %s ORDER BY 2" % population_ts_id)
    all_tps = cur.fetchall()
    values_str = ','.join(cur.mogrify("(%s,%s,DEFAULT,%s)", (all_tps[i][0],sample_ts_id,population_ts_id)) for i in range(num_tps))

    try:
        query = "INSERT INTO chile_new.timescales_sample_timepoints VALUES "+values_str+";"
        cur.execute(query)
        con.commit()
        print "Query for sampling of timeseries id %s has been successful" % population_ts_id
    except psycopg2.DatabaseError, e:
        if con:
            con.rollback()
        print 'Error %s' % e    

if cur:
    cur.close()
if con:
    con.close()
