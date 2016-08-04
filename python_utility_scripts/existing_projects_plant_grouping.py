# -*- coding: utf-8 -*-
# Copyright 2016 The Switch-Chile Authors. All rights reserved.
# Licensed under the Apache License, Version 2, which is in the LICENSE file.
# Operations, Control and Markets laboratory at Pontificia Universidad
# Católica de Chile.
"""
Groups generation units by plant to reduce number of variables. This is
not adequate when performing UC or OPF, but is acceptable when considering
long term planning.

"""
from csv import reader, writer
from getpass import getpass
import sys
import psycopg2

############
# Parameters

# Name of the ungrouped file
csv_infile = 'centrales.csv'

# Type of grouping. More than one may be chosen, to get multiple outputs
group_by_plant_name = True
plants = [
'abanico','angostura','antilhue','arauco','atacama',
'bocamina','callao','candelaria','casblanca','chuyaca',
'cmpc_pacifico','cochrane','colihues','arica','enaex',
'iquique','diesel_zofri','emelda','escuadron','esperanza_u',
'estandartes_zofri','florida','guacolda','hidrobonito',
'huasco_tg','isla','laguna_verde','laja_u','lalackama','lautaro',
'loma_los_colorados','los_corrales','los_morros','los_quilos',
'lousiana_pacific','maitenes','multiexport','munilque',
'pilmaiquen','pozo_almonte_solar','puntilla','quilleco',
'quintero','salmofood','san_lorenzo_de_d_de_almagro','santa_marta',
'skretting','solar_jama','taltal_','angamos','mejillones',
'norgener','tocopilla','tomaval','ujina','ventanas_','watt',
'yungay'
]
#atacama tiene dos consumos distintos, quedarse con el segundo'
#tocopilla tiene varios grupos. elegir con cuidado
def plant_name(name):
    for p_name in plants:
        if p_name in name:
            return p_name
    return ''
    
ok_to_group = False
    
def group_plant(units):
    max_power = 0
    n_units = 0
    spec_cons = 0
    for u in units:
        n_units += int(u[2])
        max_power += float(u[5]) * int(u[2])
        if u[12] != '':
            spec_cons += float(u[12])
        else:
            spec_cons = None
    # Average specific consumption rate of fuel
    if spec_cons:
        spec_cons = spec_cons/n_units
    units[-1][0] = 'central_'+plant_name(units[-1][0])
    units[-1][2] = n_units
    units[-1][5] = max_power
    units[-1][12] = spec_cons
    return units[-1]
        

grouped_units = []
with open(csv_infile, 'r') as f:
    all_units = []
    read = reader(f)
    for row in read:
        all_units.append(row)
    all_units.sort()
    
    aux_plant = []
    for index, unit in enumerate(all_units):
        name = unit[0]
        if plant_name(name) == 'tocopilla' or plant_name(name) == 'mejillones':
            grouped_units.append(unit)
            continue
        if plant_name(name) != '' and plant_name(name) != plant_name(all_units[index-1][0]):
            # If its the first plant to be grouped, skip grouping
            if ok_to_group == True:
                # Group previous plant
                grouped_units.append(group_plant(aux_plant))
                # And start storing the new one        
                aux_plant = [unit]
            else:
                ok_to_group = True
        elif plant_name(name) != '':
            aux_plant.append(unit)
        else:
            grouped_units.append(unit)
    # Group the last plant
    grouped_units.append(group_plant(aux_plant))

    with open('grouped_plants.csv', 'w') as out:
        csv_writer = writer(out, delimiter = ',')
        for plant in grouped_units:
            csv_writer.writerow(plant)
    


##############################
####### UPLOAD TO DB #########

projects_for_db = []
with open('grouped_plants.csv', 'r') as f:
    read = reader(f)
    for row in read:
        for i in range(11, 20):
            # Enter null values if fuel info not present
            if not row[i]:
                row[i] = None
        projects_for_db.append(row)

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

# Clean database
try:
    cleaning = "DELETE FROM chile_new.geo_existing_projects"
    cur.execute(cleaning)
    print("Table erased")
except psycopg2.DatabaseError as e:
    if con:
        con.rollback()
    print(e)

# Load new data
try:
    values_str = ','.join(cur.mogrify("(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        project) for project in projects_for_db)
    query_str = "INSERT INTO chile_new.geo_existing_projects (db_name, system, units, main_energy_source, start_date, max_net_power, min_net_power, connection_point, voltage_connection, easting, northing, fuel_1, specific_consumption_1, units_specific_consumption_1, fuel_2, specific_consumption_2, units_specific_consumption_2, fuel_3, specific_consumption_3, units_specific_consumption_3) VALUES "+values_str+";"
    cur.execute(query_str)
    con.commit()
    print ("New existing project data has been uploaded to the DB.")
except psycopg2.DatabaseError as e:
    if con:
        con.rollback()
    print(e)
    
# Update geometry column with new coordinates
try:
    query_str = "UPDATE chile_new.geo_existing_projects SET geom = ST_SetSrid(ST_MakePoint(easting, northing), 32718)"
    cur.execute(query_str)
    con.commit()
    print ("Updated geometry column with new data.")
except psycopg2.DatabaseError as e:
    if con:
        con.rollback()
    print(e)

if cur:
    cur.close()
if con:
    con.close()
