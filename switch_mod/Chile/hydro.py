# -*- coding: utf-8 -*-
# Copyright 2016 The Switch-Chile Authors. All rights reserved.
# Licensed under the Apache License, Version 2, which is in the LICENSE file.
# Operations, Control and Markets laboratory at Pontificia Universidad
# Católica de Chile.

"""

Deterministic simulation of hydroelectric reservoir management for power
production.

SYNOPSIS
>>> from switch_mod.utilities import create_model
>>> model = create_model(
...     ['timescales', 'financials', 'load_zones', 'fuels',
...     'gen_tech', 'project.build', 'project.dispatch', 'Chile.hydro'])
>>> instance = model.load_inputs(inputs_dir='test_dat')

"""
import os
from pyomo.environ import *

def define_components(mod):
    """
    
    """
    #### Water nodes
    mod.WATER_NODES = Set()
    mod.is_sink = Param(
        mod.WATER_NODES,
        within=Boolean)
    mod.WATER_SINKS = Set(
        initialize=mod.WATER_NODES,
        filter=lambda m, w: m.is_sink[w])
    mod.constant_demand = Param(
        mod.WATER_NODES,
        within=NonNegativeReals,
        default=0.0)
    mod.constant_inflow = Param(
        mod.WATER_NODES,
        within=NonNegativeReals,
        default=0.0)
    mod.water_node_inflow = Param(
        mod.WATER_NODES, mod.TIMEPOINTS,
        within=NonNegativeReals,
        default=lambda m, w, t: m.constant_inflow[w])
    mod.water_node_demand = Param(
        mod.WATER_NODES, mod.TIMEPOINTS,
        within=NonNegativeReals,
        default=lambda m, w, t: m.constant_demand[w])
    mod.WaterNodeSpilling = Var(
        mod.WATER_SINKS, mod.TIMEPOINTS,
        within=NonNegativeReals)
    
    #### Reservoirs/dams
    mod.RESERVOIRS = Set()
    mod.initial_res_vol = Param(
        mod.RESERVOIRS,
        within=NonNegativeReals)
    mod.final_res_vol = Param(
        mod.RESERVOIRS,
        within=NonNegativeReals)
    mod.reservoir_min_vol = Param(
        mod.RESERVOIRS,
        within=NonNegativeReals)
    mod.reservoir_max_vol = Param(
        mod.RESERVOIRS,
        within=PositiveReals,
        validate=lambda m, val, r: val > m.reservoir_min_vol[r])
    # vols may be specified in a timepoint basis as well (for seasonal
    # restrictions)
    mod.reservoir_min_vol_tp = Param(
        mod.RESERVOIRS, mod.TIMEPOINTS,
        within=NonNegativeReals,
        default=lambda m, r, t: m.reservoir_min_vol[r])
    mod.reservoir_max_vol_tp = Param(
        mod.RESERVOIRS, mod.TIMEPOINTS,
        within=PositiveReals,
        default=lambda m, r, t: m.reservoir_max_vol[r])
    mod.reservoir_inflow = Param(
        mod.RESERVOIRS, mod.TIMEPOINTS,
        within=NonNegativeReals,
        default=0.0)
    mod.reservoir_demand = Param(
        mod.RESERVOIRS, mod.TIMEPOINTS,
        within=NonNegativeReals,
        default=0.0)    
    mod.FilteredFlow = Var(
        mod.RESERVOIRS, mod.TIMEPOINTS,
        within=NonNegativeReals)
    mod.ReservoirInitialvol = Var(
        mod.RESERVOIRS, mod.TIMEPOINTS,
        within=NonNegativeReals)
    mod.ReservoirFinalvol = Var(
        mod.RESERVOIRS, mod.TIMEPOINTS,
        within=NonNegativeReals)    
    mod.Enforce_Res_Max_vol = Constraint(
        mod.RESERVOIRS, mod.TIMEPOINTS,
        rule=lambda m, r, t: (
            m.ReservoirFinalvol[r, t] <= m.reservoir_max_vol_tp[r, t]))
    mod.Enforce_Res_Min_vol = Constraint(
        mod.RESERVOIRS, mod.TIMEPOINTS,
        rule=lambda m, r, t: (   
            m.ReservoirFinalvol[r, t] >= m.reservoir_min_vol_tp[r, t]))
    
    #### Water Connections
    # Water flows have only one direction
    mod.WATER_CONNECTIONS = Set()
    mod.WATER_BODIES = Set(
        initialize=lambda m: m.WATER_NODES | m.RESERVOIRS)
    mod.WC_body_from = Param(
        mod.WATER_CONNECTIONS, 
        within=mod.WATER_BODIES)
    mod.WC_body_to = Param(
        mod.WATER_CONNECTIONS, 
        within=mod.WATER_BODIES)
    mod.WC_capacity = Param(
        mod.WATER_CONNECTIONS,
        within=PositiveReals,
        default=9999)
    mod.is_a_filtration = Param(
        mod.WATER_CONNECTIONS,
        within=Boolean)
    mod.DispatchWater = Var(
        mod.WATER_CONNECTIONS, mod.TIMEPOINTS,
        within=NonNegativeReals) 
                
    #### Hydroelectric projects (either reservoir or RoR in series)
    mod.HYDRO_PROJECTS = Set(
        validate=lambda m, val: val in m.PROJECTS)
    mod.HYDRO_PROJ_DISPATCH_POINTS = Set(
        initialize=mod.PROJ_DISPATCH_POINTS,
        filter=lambda m, proj, t: proj in m.HYDRO_PROJECTS)
    mod.proj_hydro_efficiency = Param(
        mod.HYDRO_PROJECTS,
        within=PositiveReals,
        validate=lambda m, val, proj: val <= 10)
    mod.hidraulic_location = Param(
        mod.HYDRO_PROJECTS,
        validate=lambda m, val, proj: val in m.WATER_CONNECTIONS)
    # Auxiliar variable for documentation. Should be removed later.
    mod.TurbinatedFlow = Var(
        mod.HYDRO_PROJ_DISPATCH_POINTS,
        within=NonNegativeReals)
    mod.SpilledFlow = Var(
        mod.HYDRO_PROJ_DISPATCH_POINTS,
        within=NonNegativeReals)
    
    # Hydro project constraints
    mod.Enforce_Hydro_Generation = Constraint(
        mod.HYDRO_PROJ_DISPATCH_POINTS,
        rule=lambda m, proj, t: (m.DispatchProj[proj, t] ==
            m.proj_hydro_efficiency[proj] * m.TurbinatedFlow[proj, t]))
    mod.Enforce_Hydro_Production = Constraint(
        mod.HYDRO_PROJ_DISPATCH_POINTS,
        rule=lambda m, proj, t: (m.TurbinatedFlow[proj, t] +
            m.SpilledFlow[proj, t] == 
            m.DispatchWater[m.hidraulic_location[proj], t]))
       
    # Still missing filtration calculation        
        
    # WC constraints
    mod.Enforce_WC_Capacity = Constraint(
        mod.WATER_CONNECTIONS, mod.TIMEPOINTS,
        rule=lambda m, wc, t: m.DispatchWater[wc, t] <= m.WC_capacity[wc])
    # It may be redundant to enforce eco flows when they are 0. Could find a better way.
    mod.min_eco_flow = Param(
        mod.WATER_CONNECTIONS, mod.TIMEPOINTS,
        within=NonNegativeReals,
        default=lambda m, w, t: 0.0)
    mod.Enforce_Min_Eco_Flow = Constraint(
        mod.WATER_CONNECTIONS, mod.TIMEPOINTS,
        rule=lambda m, w, t: (
            m.DispatchWater[w, t] >= m.min_eco_flow[w, t]))
    
    # Nodal constraints
    mod.WaterNodeNet = Expression(
        mod.WATER_NODES, mod.TIMEPOINTS,
        rule=lambda m, w, t: sum( m.DispatchWater[wc, t] 
            for wc in m.WATER_CONNECTIONS if m.WC_body_to[wc] == w) - 
            sum( m.DispatchWater[wc, t] for wc in m.WATER_CONNECTIONS 
            if m.WC_body_from[wc] == w))
    mod.Water_Node_Balance_Sinks = Constraint(
        mod.WATER_SINKS, mod.TIMEPOINTS,
        rule=lambda m, w, t: (m.water_node_inflow[w, t] + m.WaterNodeNet[w, t] ==
            m.water_node_demand[w, t] + m.WaterNodeSpilling[w, t]))
    mod.Water_Node_Balance_Others = Constraint(
        mod.WATER_NODES - mod.WATER_SINKS, mod.TIMEPOINTS,
        rule=lambda m, w, t: (m.water_node_inflow[w, t] + m.WaterNodeNet[w, t] ==
            m.water_node_demand[w, t]))
    
    # Reservoir Constraints
    mod.Reservoir_Balance = Constraint(
        mod.RESERVOIRS, mod.TIMEPOINTS,
        rule=lambda m, r, t: (
            m.reservoir_inflow[r, t] + sum( m.DispatchWater[wc, t] 
            for wc in m.WATER_CONNECTIONS if m.WC_body_to[wc] == r) == 
            (m.ReservoirFinalvol[r, t] -
                m.ReservoirInitialvol[r, t]) / m.tp_duration_hrs[t] +
            sum( m.DispatchWater[wc, t] 
                for wc in m.WATER_CONNECTIONS if m.WC_body_from[wc] == r)))
    mod.Reservoir_Filtrations = Constraint(
        mod.RESERVOIRS, mod.TIMEPOINTS,
        rule=lambda m, r, t: (
            m.FilteredFlow[r, t] == sum( m.DispatchWater[wc, t]
                for wc in m.WATER_CONNECTIONS if m.WC_body_from[wc] == r
                and m.is_a_filtration[wc])))
        
    def Enforce_Reservoir_vol_Links(m, r, t):
        if t == m.TIMEPOINTS.first():
            return (m.ReservoirInitialvol[r, t] == m.initial_res_vol[r])
        elif t in [m.TS_TPS[ts][1] for ts in m.TIMESERIES if ts != m.TIMESERIES.first()]:
            previous_ts = m.TIMESERIES.prev(m.tp_ts[t])
            previous_ts_last_tp = m.TS_TPS[previous_ts].last()
            return (m.ReservoirInitialvol[r, t] == m.ReservoirFinalvol[r, previous_ts_last_tp])
        else:
            return (m.ReservoirInitialvol[r, t] == m.ReservoirFinalvol[r, m.tp_previous[t]])
    mod.Reservoir_vol_Links = Constraint(
        mod.RESERVOIRS, mod.TIMEPOINTS,
        rule=Enforce_Reservoir_vol_Links)
    mod.Enforce_Final_vol_condition = Constraint(
        mod.RESERVOIRS, mod.PERIODS,
        rule=lambda m, r, p: (m.ReservoirFinalvol[r, m.PERIOD_TPS[p].last()] >=
            m.initial_res_vol[r]))

            
def load_inputs(mod, switch_data, inputs_dir):
    """
    """
    
    switch_data.load_aug(
        filename=os.path.join(inputs_dir, 'reservoirs.tab'),
        auto_select=True,
        index=mod.RESERVOIRS,
        param=(
            mod.reservoir_min_vol, mod.reservoir_max_vol, 
            mod.initial_res_vol, mod.final_res_vol))
    switch_data.load_aug(
        filename=os.path.join(inputs_dir, 'reservoir_tp_data.tab'),
        optional=True,
        auto_select=True,
        optional_params=[
            'mod.reservoir_inflow', 'mod.reservoir_demand', 
            'mod.reservoir_max_vol_tp', 'mod.reservoir_min_vol_tp'],
        param=(
            mod.reservoir_inflow, mod.reservoir_demand, 
            mod.reservoir_max_vol_tp, mod.reservoir_min_vol_tp))
    switch_data.load_aug(
        filename=os.path.join(inputs_dir, 'water_nodes.tab'),
        auto_select=True,
        index=mod.WATER_NODES,
        optional_params=['mod.constant_demand','mod.constant_inflow'],
        param=(mod.is_sink, mod.constant_demand, mod.constant_inflow))
    switch_data.load_aug(
        optional=True,
        filename=os.path.join(inputs_dir, 'water_node_flows.tab'),
        auto_select=True,
        optional_params=['mod.water_node_inflow', 'mod.water_node_demand'],
        param=(mod.water_node_inflow, mod.water_node_demand))
    switch_data.load_aug(
        filename=os.path.join(inputs_dir, 'water_connections.tab'),
        auto_select=True,
        index=mod.WATER_CONNECTIONS,
        param=(
            mod.WC_body_from, mod.WC_body_to, mod.WC_capacity,
            mod.is_a_filtration))
    switch_data.load_aug(
        filename=os.path.join(inputs_dir, 'hydro_projects.tab'),
        auto_select=True,
        index=mod.HYDRO_PROJECTS,
        param=(mod.proj_hydro_efficiency, mod.hidraulic_location))
    switch_data.load_aug(
        optional=True,
        filename=os.path.join(inputs_dir, 'min_eco_flows.tab'),
        auto_select=True,
        param=(mod.min_eco_flow))
