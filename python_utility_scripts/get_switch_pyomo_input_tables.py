# -*- coding: utf-8 -*-
# Copyright 2016 The Switch-Chile Authors. All rights reserved.
# Licensed under the Apache License, Version 2, which is in the LICENSE file.
# Operations, Control and Markets laboratory at Pontificia Universidad
# Católica de Chile.
"""

Retrieves data inputs for the Switch Chile model from the database. Data
is formatted into corresponding .tab or .dat files.

"""

import time, argparse, getpass, sys, os
import psycopg2

# Set python to stream output unbuffered.
#sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

start_time = time.time()

def write_tab(fname, headers, cursor):
    with open(fname + '.tab', 'w') as f:
        f.write('\t'.join(headers) + '\n')
        for row in cursor:
            # Replace None values with dots for SWITCH
            line = [e if e is not None else '.' for e in row]
            f.write('\t'.join(map(str,line)) + '\n')

parser = argparse.ArgumentParser(
    usage='get_switch_pyomo_input_tables.py [--help] [options]',
    description='Write SWITCH input files from database tables. Default \
    options asume an SSH tunnel has been opened between the local port 5915\
    and the Postgres port at the remote host where the database is stored.')
parser.add_argument(
    '-H', type=str, default='localhost', metavar='hostname',
    help='Database host address (default is "localhost")')
parser.add_argument(
    '-P', type=int, default=5915, metavar='port',
    help='Database host port (default is "5915")')
parser.add_argument(
    '-U', type=str, default=getpass.getuser(), metavar='username',
    help='Database username (default is current system user, "%s")'
    % getpass.getuser())
parser.add_argument(
    '-D', type=str, default='switch_chile', metavar='dbname',
    help='Database name (default is "switch_chile")')
parser.add_argument(
    '-s', type=int, required=True, metavar='scenario_id',
    help='Scenario ID for the simulation')
parser.add_argument(
    '-i', type=str, default='inputs', metavar='inputsdir',
    help='Directory where the inputs will be built (default is "inputs")')
args = parser.parse_args()

passw = 'trapenses4860'
#passw = getpass.getpass('Enter database password for user %s:' % args.U)

try:
    # Connection settings are determined by parsed command line inputs
    con = psycopg2.connect(database=args.D, user=args.U, host=args.H,
        port=args.P, password=passw)
    print "Connection to database established..."
except:
    sys.exit("Error connecting to database %s at host %s." % (args.D,args.H))

if not os.path.exists(args.i):
    os.makedirs(args.i)
    print 'Inputs directory created...'
else:
    print 'Inputs directory exists, so contents will be overwritten...'

cur = con.cursor()

############################################################################################################
# These next variables determine which input data is used, though some are only for documentation and result exports.

cur.execute("SELECT * FROM chile_new.scenarios_switch_chile WHERE scenario_id = %s" % args.s)
s_details = cur.fetchone()
scenario_name, scenario_notes, sample_ts_scenario_id, hydro_id, fuel_id, gen_costs_id, new_projects_id, carbon_tax_id, carbon_cap_id, rps_id, lz_hourly_demand_id, gen_info_id, load_zones_scenario_id = s_details[1], s_details[2], s_details[3], s_details[4], s_details[5], s_details[6], s_details[7], s_details[8], s_details[9], s_details[10], s_details[11], s_details[12], s_details[13]

os.chdir(args.i)

# The format for tab files is:
# col1_name col2_name ...
# [rows of data]

# The format for dat files is the same as in AMPL dat files.

print '\nStarting data copying from the database to input files for scenario:\n "%s"' % scenario_name
    
# Write general scenario parameters into documentation file
print 'Writing scenario documentation into scenario_params.txt.'
with open('scenario_params.txt', 'w') as f:
    f.write('Scenario id: %s' % args.s)
    f.write('\nScenario name: %s' % scenario_name)
    f.write('\nScenario notes: %s' % scenario_notes)

########################################################
# TIMESCALES

print '  periods.tab...'
cur.execute('SELECT DISTINCT p.period_name, period_start, period_end FROM chile_new.timescales_sample_timeseries sts JOIN chile_new.timescales_population_timeseries pts ON sts.sampled_from_population_timeseries_id=pts.population_ts_id JOIN chile_new.timescales_periods p USING (period_id) WHERE sample_ts_scenario_id=%s ORDER BY 1;' % sample_ts_scenario_id)
write_tab('periods',['INVESTMENT_PERIOD','period_start','period_end'],cur)

print '  timeseries.tab...'
cur.execute('SELECT sample_ts_id,period_name,hours_per_tp::integer,sts.num_timepoints,sts.scaling_to_period FROM chile_new.timescales_sample_timeseries sts JOIN chile_new.timescales_population_timeseries pts ON sts.sampled_from_population_timeseries_id=pts.population_ts_id WHERE sample_ts_scenario_id=%s ORDER BY 1;' % sample_ts_scenario_id)
write_tab('timeseries', ['TIMESERIES','ts_period','ts_duration_of_tp','ts_num_tps','ts_scale_to_period'], cur)

print '  timepoints.tab...'
cur.execute("SELECT sample_tp_id,to_char(timestamp, 'YYYYMMDDHH24'),sample_ts_id FROM chile_new.timescales_sample_timepoints JOIN chile_new.timescales_sample_timeseries USING (sample_ts_id) WHERE sample_ts_scenario_id=%s ORDER BY 1;" % sample_ts_scenario_id)
write_tab('timepoints', ['timepoint_id','timestamp','timeseries'], cur)

########################################################
# LOAD ZONES AND BALANCING AREAS

print '  load_zones.tab...'
cur.execute("SELECT lz_name, cost_multiplier, ccs_distance_km, lz_dbid, existing_local_td, local_td_annual_cost_per_mw FROM chile_new.load_zones WHERE load_zones_scenario_id=%s ORDER BY 1;" % load_zones_scenario_id)
write_tab('load_zones',['LOAD_ZONE','lz_cost_multipliers','lz_ccs_distance_km','lz_dbid','existing_local_td','local_td_annual_cost_per_mw'],cur)

# For now, only taking 2014 demand and repeating it.
print '  loads.tab...'
cur.execute("SELECT lz_name, tps.sample_tp_id, lz_demand_mwh FROM chile_new.lz_hourly_demand lzd JOIN chile_new.timescales_sample_timepoints tps ON TO_CHAR(tps.timestamp,'MMDDHH24')=TO_CHAR(lzd.timestamp_cst,'MMDDHH24') JOIN chile_new.timescales_sample_timeseries USING (sample_ts_id) JOIN chile_new.load_zones USING (lz_name,load_zones_scenario_id) WHERE sample_ts_scenario_id = %s AND load_zones_scenario_id = %s AND lz_hourly_demand_id = %s AND TO_CHAR(lzd.timestamp_cst,'YYYY') = '2014' ORDER BY 1,2;" % (sample_ts_scenario_id,load_zones_scenario_id,lz_hourly_demand_id))
write_tab('loads',['LOAD_ZONE','TIMEPOINT','lz_demand_mw'],cur)

print '  balancing_areas.tab...'
cur.execute("SELECT balancing_area, quickstart_res_load_frac, quickstart_res_wind_frac, quickstart_res_solar_frac,spinning_res_load_frac, spinning_res_wind_frac, spinning_res_solar_frac FROM chile_new.balancing_areas;")
write_tab('balancing_areas',['BALANCING_AREAS','quickstart_res_load_frac','quickstart_res_wind_frac','quickstart_res_solar_frac','spinning_res_load_frac','spinning_res_wind_frac','spinning_res_solar_frac'],cur)

print '  lz_balancing_areas.tab...'
cur.execute("SELECT lz_name, balancing_area FROM chile_new.load_zones WHERE load_zones_scenario_id = %s;" % load_zones_scenario_id)
write_tab('lz_balancing_areas',['LOAD_ZONE','balancing_area'],cur)

# For now, only taking 2014 peak demand and repeating it.
print '  lz_peak_loads.tab'
cur.execute("SELECT lzd.lz_name, p.period_name, max(lz_demand_mwh) FROM chile_new.timescales_sample_timepoints tps JOIN chile_new.lz_hourly_demand lzd ON TO_CHAR(lzd.timestamp_cst,'MMDDHH24')=TO_CHAR(tps.timestamp,'MMDDHH24') JOIN chile_new.timescales_sample_timeseries sts USING (sample_ts_id) JOIN chile_new.timescales_population_timeseries pts ON sts.sampled_from_population_timeseries_id = pts.population_ts_id JOIN chile_new.timescales_periods p USING (period_id) WHERE sample_ts_scenario_id = %s AND lz_hourly_demand_id = %s AND load_zones_scenario_id = %s AND TO_CHAR(lzd.timestamp_cst,'YYYY') = '2014' GROUP BY lzd.lz_name, p.period_name ORDER BY 1,2;" % (sample_ts_scenario_id,lz_hourly_demand_id,load_zones_scenario_id))
write_tab('lz_peak_loads',['LOAD_ZONE','PERIOD','peak_demand_mw'],cur)

########################################################
# TRANSMISSION

print '  transmission_lines.tab...'
cur.execute("SELECT transmission_line_id,lz1, lz2, trans_length_km, trans_efficiency, existing_trans_cap_mw FROM chile_new.transmission_lines WHERE load_zones_scenario_id = %s ORDER BY 2,3;" % load_zones_scenario_id)
write_tab('transmission_lines',['TRANSMISSION_LINE','trans_lz1','trans_lz2','trans_length_km','trans_efficiency','existing_trans_cap'],cur)

print '  trans_optional_params.tab...'
cur.execute("SELECT transmission_line_id, transmission_line_id, derating_factor, terrain_multiplier, new_build_allowed FROM chile_new.transmission_lines WHERE load_zones_scenario_id = %s ORDER BY 1;" % load_zones_scenario_id)
write_tab('trans_optional_params.tab',['TRANSMISSION_LINE','trans_dbid','trans_derating_factor','trans_terrain_multiplier','trans_new_build_allowed'],cur)

print '  trans_params.dat...'
with open('trans_params.dat','w') as f:
    f.write("param trans_capital_cost_per_mw_km:=1000;\n")
    f.write("param trans_lifetime_yrs:=20;\n")
    f.write("param trans_fixed_o_m_fraction:=0.03;\n")
    #f.write("param distribution_loss_rate:=0.0652;\n")

########################################################
# FUEL
print '  fuels.tab...'
cur.execute("SELECT energy_source, co2_intensity, upstream_co2_intensity FROM chile_new.energy_sources WHERE fuel IS TRUE;")
write_tab('fuels',['fuel','co2_intensity','upstream_co2_intensity'],cur)

print '  non_fuel_energy_sources.tab...'
cur.execute("SELECT energy_source FROM chile_new.energy_sources WHERE non_fuel_energy_source IS TRUE;")
write_tab('non_fuel_energy_sources',['energy_source'],cur)

# Fuel projections are yearly averages in the DB. For now, Switch only accepts fuel prices per period, so they are averaged.
print '  fuel_cost.tab'
cur.execute("SELECT lz_name, fuel, period_name, AVG(fuel_price) FROM chile_new.fuel_yearly_prices CROSS JOIN chile_new.timescales_periods WHERE fuel_yearly_prices_id = %s AND load_zones_scenario_id = %s AND projection_year BETWEEN period_start AND period_end AND period_name IN (SELECT DISTINCT p.period_name FROM chile_new.timescales_sample_timeseries sts JOIN chile_new.timescales_population_timeseries pts ON sts.sampled_from_population_timeseries_id=pts.population_ts_id JOIN chile_new.timescales_periods p USING (period_id) WHERE sample_ts_scenario_id=%s) GROUP BY lz_name, fuel, period_name ORDER BY 1, 2, 3;" % (fuel_id,load_zones_scenario_id, sample_ts_scenario_id))
write_tab('fuel_cost',['load_zone','fuel','period','fuel_cost'],cur)

########################################################
# GENERATOR TECHNOLOGIES

print '  generator_info.tab...'
cur.execute("SELECT technology_name, max_age, CASE WHEN variable THEN 1 ELSE 0 END, CASE WHEN baseload THEN 1 ELSE 0 END, CASE WHEN flexible_baseload THEN 1 ELSE 0 END, CASE WHEN cogen THEN 1 ELSE 0 END, CASE WHEN competes_for_space THEN 1 ELSE 0 END, variable_o_m, energy_source, technology_id, scheduled_outage_rate, forced_outage_rate, min_build_capacity, full_load_heat_rate, unit_size FROM chile_new.generator_info WHERE generator_info_id = %s ORDER BY 1;" % gen_info_id) 
write_tab('generator_info',['generation_technology','g_max_age','g_is_variable','g_is_baseload','g_is_flexible_baseload','g_is_cogen','g_competes_for_space','g_variable_o_m','g_energy_source','g_dbid','g_scheduled_outage_rate','g_forced_outage_rate','g_min_build_capacity','g_full_load_heat_rate','g_unit_size'],cur)

# Yearly overnight and fixed o&m cost projections are averaged for each study period.
print '  gen_new_build_costs.tab...'
cur.execute("SELECT technology_name, period_name, AVG(overnight_cost), AVG(fixed_o_m) FROM chile_new.generator_yearly_costs JOIN chile_new.generator_info USING (technology_name) CROSS JOIN chile_new.timescales_periods WHERE generator_yearly_costs_id = %s AND generator_info_id = %s AND projection_year BETWEEN period_start AND period_end AND period_name IN (SELECT DISTINCT p.period_name FROM chile_new.timescales_sample_timeseries sts JOIN chile_new.timescales_population_timeseries pts ON sts.sampled_from_population_timeseries_id=pts.population_ts_id JOIN chile_new.timescales_periods p USING (period_id) WHERE sample_ts_scenario_id=%s)  GROUP BY 1,2 ORDER BY 1,2;" % (gen_costs_id,gen_info_id,sample_ts_scenario_id)) 
write_tab('gen_new_build_costs',['generation_technology','investment_period','g_overnight_cost','g_fixed_o_m'],cur)

########################################################
# PROJECTS

print '  project_info.tab...'
cur.execute("SELECT project_name, gen_tech, load_zone, connect_cost_per_mw, variable_o_m, full_load_heat_rate, forced_outage_rate, scheduled_outage_rate, project_id, capacity_limit_mw, hydro_efficiency FROM chile_new.project_info_existing \
    UNION SELECT project_name, gen_tech, load_zone, connect_cost_per_mw, variable_o_m, full_load_heat_rate, forced_outage_rate, scheduled_outage_rate, project_id, capacity_limit_mw, hydro_efficiency FROM chile_new.project_info_new JOIN chile_new.new_projects_sets USING (project_id)WHERE new_projects_sets_id = %s ORDER BY 2,3;" % new_projects_id)
write_tab('project_info',['PROJECT','proj_gen_tech','proj_load_zone','proj_connect_cost_per_mw','proj_variable_om','tproj_full_load_heat_rate','proj_forced_outage_rate','proj_scheduled_outage_rate','proj_dbid','proj_capacity_limit_mw','proj_hydro_efficiency'],cur)

print '  proj_existing_builds.tab...'
cur.execute("SELECT project_name, start_year, capacity_mw FROM chile_new.project_info_existing;")
write_tab('proj_existing_builds',['PROJECT','build_year','proj_existing_cap'],cur)

print '  proj_build_costs.tab...'
cur.execute("SELECT project_name, start_year, overnight_cost, fixed_o_m FROM chile_new.project_info_existing;")
write_tab('proj_build_costs',['PROJECT','build_year','proj_overnight_cost','proj_fixed_om'],cur)

########################################################
# FINANCIALS

print '  financials.dat...'
with open('financials.dat','w') as f:
    f.write("param base_financial_year := 2014;\n")
    f.write("param interest_rate := .07;\n")
    f.write("param discount_rate := .07;\n")

########################################################
# VARIABLE CAPACITY FACTORS

#Pyomo will raise an error if a capacity factor is defined for a project on a timepoint when it is no longer operational (i.e. Canela 1 was built on 2007 and has a 30 year max age, so for tp's ocurring later than 2037, its capacity factor must not be written in the table).

# This will only get exactly the cf in the moment when the timepoint beings
# If a timepoint lasts for 2 hours, then the cf for the first hour will be
# stored.    
# For now, only taking 2014 profile and repeating it.

#The order is:
# 1: Fill new solar and wind
# 2: Fill existing dam plants
# 3: Fill existing solar, ror and wind
print '  variable_capacity_factors.tab...'
cur.execute("SELECT project_name, sample_tp_id, CASE WHEN capacity_factor>1.999 THEN 1.999 ELSE capacity_factor END FROM chile_new.variable_capacity_factors_new cf JOIN (SELECT * FROM chile_new.timescales_sample_timepoints JOIN chile_new.timescales_sample_timeseries USING (sample_ts_id) WHERE sample_ts_scenario_id=%s) tps ON TO_CHAR(cf.timestamp_cst,'MMDDHH24')=TO_CHAR(tps.timestamp,'MMDDHH24') JOIN chile_new.new_projects_sets USING (project_id) WHERE new_projects_sets_id=%s \
    UNION SELECT project_name, sample_tp_id, CASE WHEN capacity_factor>1.999 THEN 1.999 ELSE capacity_factor END FROM chile_new.variable_capacity_factors_existing cf JOIN (SELECT * FROM chile_new.timescales_sample_timepoints JOIN chile_new.timescales_sample_timeseries USING (sample_ts_id) WHERE sample_ts_scenario_id=%s) tps ON TO_CHAR(cf.timestamp_cst,'MMDDHH24')=TO_CHAR(tps.timestamp,'MMDDHH24') WHERE project_name != 'PV' AND project_name != 'Wind' AND project_name != 'Hydro_RoR'\
    UNION SELECT info.project_name, sample_tp_id, capacity_factor FROM chile_new.variable_capacity_factors_existing cf JOIN chile_new.project_info_existing info ON info.gen_tech = cf.project_name JOIN (SELECT * FROM chile_new.timescales_sample_timepoints JOIN chile_new.timescales_sample_timeseries USING (sample_ts_id) WHERE sample_ts_scenario_id=%s) tps ON TO_CHAR(cf.timestamp_cst,'MMDDHH24')=TO_CHAR(tps.timestamp,'MMDDHH24') \
    ORDER BY 1,2;" % (sample_ts_scenario_id, new_projects_id,sample_ts_scenario_id,sample_ts_scenario_id))
write_tab('variable_capacity_factors',['PROJECT','timepoint','proj_max_capacity_factor'],cur)

if cur:
    cur.close()
if con:
    print '\nClosing DB connection.'
    con.close()
    
os.chdir('..')

end_time = time.time()

print '\nScript took %s seconds building input tables.' % (end_time-start_time)
