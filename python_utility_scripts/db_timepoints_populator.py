"""

Script to populate the timescales_population_timepoints table in the
switch_chile OCM database.  The only inputs required are the connection
parameters and the timeseries scenario id for which the timepoints want to be
populated.

"""

import psycopg2, datetime, sys

# The timeseries scenario id must be inputted to generate the timepoints
# corresponding to that set
population_ts_scenario_id = 1

try:
    # Remember to enter and/or modify connection parameters accordingly to your
    # setup
    con = psycopg2.connect(database='switch_chile', user='bmaluenda', 
                            host='localhost', port='5915',
                            password='')
    print "Connection to database established..."
except:
    sys.exit("Error connecting to the switch_chile database...")

cur = con.cursor()
cur.execute("SELECT * FROM chile_new.timescales_population_timeseries WHERE population_ts_scenario_id = %s ORDER BY 2" % population_ts_scenario_id)
timeseries_table = cur.fetchall()

for row in timeseries_table:

    initial_timestamp = row[8]
    population_ts_id = row[1]
    num_tps = row[6]
    hours_per_tp = row[5]

    rows_to_insert = []
    timestamp = initial_timestamp
    delta = datetime.timedelta(hours = hours_per_tp)

    for i in range(num_tps):
        # Skip leap year's extra day.
        if timestamp.month == 2 and timestamp.day == 29:
            timestamp += datetime.timedelta(days=1)
        rows_to_insert.append((timestamp,population_ts_id))
        timestamp += delta

    try:
        query = "INSERT INTO chile_new.timescales_population_timepoints (timestamp, population_ts_id) VALUES (%s, %s)"
        cur.executemany(query, tuple(rows_to_insert))
        con.commit()
        print "Query for population of timeseries id %s has been successful" % population_ts_id
    except psycopg2.DatabaseError, e:
        if con:
            con.rollback()
        print 'Error %s' % e    

if cur:
    cur.close()
if con:
    con.close()