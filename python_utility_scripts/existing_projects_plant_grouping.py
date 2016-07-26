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
'iquique','diesel_zofri','emelda','escuadron','esperanza',
'estandartes_zofri','florida','guacolda','hidrobonito',
'huasco','isla','laguna_verde','laja_u','lalackama','lautaro',
'loma_los_colorados','los_corrales','los_morros','los_quilos',
'lousiana_pacific','maitenes','multiexport','munilque',
'pilmaiquen','pozo_almonte_solar','puntilla','quilleco',
'quintero','salmofood','san_lorenzo_de_d_de_almagro','santa_marta',
'skretting','solar_jama','taltal','angamos','mejillones',
'norgener','tocopilla','tomaval','ujina','ventanas','watt',
'yungay'
]
'atacama tiene dos consumos distintos, quedarse con el segundo'
tocopilla tiene varios grupos. elegir con cuidado

def plant_name(name):
    for plant_name in plants:
        if plant_name in name:
            return plant_name
    return ''

grouped_units = []
with open(csv_infile, 'r') as f:
    all_units = []
    read = reader(f)
    for row in read:
        all_units.append(row)
    
    k = 0
    for unit in all_units:
        name = unit[0]
        if plant_name(name) and plant_name(name) != all_units[-1][0]:
            k += 1
            
            
    
