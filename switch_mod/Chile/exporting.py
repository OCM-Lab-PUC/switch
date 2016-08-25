# Copyright 2015 The Switch Authors. All rights reserved.
# Licensed under the Apache License, Version 2, which is in the LICENSE file.

"""

This modules writes out output tables with certain processing.
This tables are mostly useful for quick iterations when testing code.

"""
import os, time, sys
from pyomo.environ import *
from switch_mod.financials import *
from csv import reader
import matplotlib.pyplot as plt
import pandas as pd
from cycler import cycler
import switch_mod.export as export

def define_arguments(argparser):
    argparser.add_argument(
        "--export-marginal-costs", action='store_true', default=False,
        help="Exports energy marginal costs in US$/MWh per load zone and timepoint, calculated as dual variable values from the energy balance constraint."
    )
    argparser.add_argument(
        "--export-capacities", action='store_true', default=False,
        help="Exports cummulative installed generating capacity in MW per technology per period."
    )
    argparser.add_argument(
        "--export-tech-dispatch", action='store_true', default=False,
        help="Exports dispatched capacity per generator technology in MW per timepoint."
    )
    argparser.add_argument(
        "--export-reservoirs", action='store_true', default=False,
        help="Exports final reservoir volumes in cubic meters per timepoint."
    )
    
def define_components(mod):
    #Define dual variables, so that marginal costs can be computed eventually
    if not hasattr(mod, 'dual'):
        mod.dual = Suffix(direction=Suffix.IMPORT)

def define_dynamic_components(mod):
    #Separate the computation of Investment and Operations cost, for comparison with stochastic problem
    import switch_mod.financials as fin

    def calc_tp_costs_in_period(m, t):
            return sum(
                getattr(m, tp_cost)[t] * m.tp_weight_in_year[t]
                for tp_cost in m.cost_components_tp)

    def calc_annual_costs_in_period(m, p):
            return sum(
                getattr(m, annual_cost)[p]
                for annual_cost in m.cost_components_annual)

    mod.TotalInvestmentCost = Expression(rule=lambda m: sum(calc_annual_costs_in_period(m, p) * fin.uniform_series_to_present_value(
                    m.discount_rate, m.period_length_years[p]) * fin.future_to_present_value(
                    m.discount_rate, (m.period_start[p] - m.base_financial_year)) for p in m.PERIODS))
    mod.TotalOperationsCost = Expression(rule=lambda m: sum(m.SystemCostPerPeriod[p] for p in m.PERIODS) - m.TotalInvestmentCost)


def post_solve(instance, outdir):
    summaries_dir = os.path.join(outdir,"Summaries")
    if not os.path.exists(summaries_dir):
        os.makedirs(summaries_dir)

    print "\nStarting to print summaries"
    start=time.time()

    if instance.options.export_marginal_costs:
        """
        This table writes out the marginal costs of supplying energy in each timepoint in US$/MWh.
        """
        print "marginal_costs_lz_tp.csv..."
        export.write_table(
            instance, instance.TIMEPOINTS, instance.LOAD_ZONES,
            output_file=os.path.join(summaries_dir, "marginal_costs_lz_tp.csv"),
            headings=("timepoint","load_zones","marginal_cost"),
            values=lambda m, tp, lz: (m.tp_timestamp[tp], lz, m.dual[m.Energy_Balance[lz, tp]] / (m.tp_weight_in_year[tp] * uniform_series_to_present_value(
                    m.discount_rate, m.period_length_years[m.tp_period[tp]]) * future_to_present_value(
                    m.discount_rate, (m.period_start[m.tp_period[tp]] - m.base_financial_year)))
            ))
        df = pd.read_csv('outputs/Summaries/marginal_costs_lz_tp.csv',sep='\t')
        lz_dfs = []
        for lz in instance.LOAD_ZONES:
            lz_dfs.append(df[df.load_zones == lz].drop(['load_zones','timepoint'],axis=1).reset_index(drop=True))
            lz_dfs[-1].columns = [lz]
        DF = pd.concat(lz_dfs, axis=1)
        fig = plt.figure(1)
        mc_ax = fig.add_subplot(211)
        # GO cycling through the rainbow to get line colours
        cm = plt.get_cmap('gist_rainbow')
        # You have to play with the color map and the line style list to get enough combinations for your particular plot
        mc_ax.set_prop_cycle(cycler('linestyle',['-',':','--','-.']) * cycler('color',[cm(i/5.0) for i in range(0,6)]))
        # to locate the legend: "loc" is the point of the legend for which you will specify cooridnates. These coords are specified in bbox_to_anchor (can be only 1 point or couple)
        mc_plot = DF.plot(ax=mc_ax,linewidth=1.5).legend(loc='upper center', fontsize=10, bbox_to_anchor=(0.,-0.15,1.,-0.15), ncol=3, mode="expand")
        plt.xticks([i*24 for i in range(1,len(instance.TIMEPOINTS)/24+1)],[instance.tp_timestamp[instance.TIMEPOINTS[i*24]] for i in range(1,len(instance.TIMEPOINTS)/24+1)],rotation=40,fontsize=7)
        plt.savefig('outputs/Summaries/marginal_costs.pdf',bbox_extra_artists=(mc_plot,))
    """
    This table writes out the fuel consumption in MMBTU per hour. 
    """
    # print "energy_produced_in_period_by_each_project.csv..."
    # export.write_table(
    #     instance, instance.PERIODS, instance.PROJECTS,
    #     output_file=os.path.join(summaries_dir, "energy_produced_in_period_by_each_project.csv"), 
    #     headings=("period", "project", "energy_produced_GWh"),
    #     values=lambda m, p, proj: (p, proj,) + tuple(
    #         sum(m.DispatchProj[proj,tp]*m.tp_weight[tp] for tp in m.PERIOD_TPS[p])/1000)
    #     )

    # """
    # This table writes out the fuel consumption in MMBTU per hour. 
    # """
    # print "fuel_consumption_tp_hourly.csv..."
    # export.write_table(
    #     instance, instance.TIMEPOINTS,
    #     output_file=os.path.join(summaries_dir, "fuel_consumption_tp_hourly.csv"),
    #     headings=("timepoint",) + tuple(f for f in instance.FUELS),
    #     values=lambda m, tp: (m.tp_timestamp[tp],) + tuple(
    #         sum(m.ProjFuelUseRate[proj, t, f] for (proj,t) in m.PROJ_WITH_FUEL_DISPATCH_POINTS 
    #             if m.g_energy_source[m.proj_gen_tech[proj]] == f and t == tp)
    #         for f in m.FUELS)
    #     )
    
    # """
    # This table writes out the fuel consumption in total MMBTU consumed in each period.
    # """
    # print "fuel_consumption_periods_total.csv..."
    # export.write_table(
    #     instance, instance.PERIODS,
    #     output_file=os.path.join(summaries_dir, "fuel_consumption_periods_total.csv"),
    #     headings=("period",) + tuple(f for f in instance.FUELS),
    #     values=lambda m, p: (p,) + tuple(
    #         sum(m.ProjFuelUseRate[proj, tp, f] * m.tp_weight[tp] for (proj, tp) in m.PROJ_WITH_FUEL_DISPATCH_POINTS 
    #             if tp in m.PERIOD_TPS[p] and m.g_energy_source[m.proj_gen_tech[proj]] == f)
    #         for f in m.FUELS)
    # )


    if instance.options.export_capacities:
        """
        This table writes out the capacity that it available in each period
        by technology.
        """
        print "build_proj_by_tech_p.csv..."
        export.write_table(
            instance, instance.GENERATION_TECHNOLOGIES,
            output_file=os.path.join(summaries_dir, "build_proj_by_tech_p.csv"),
            headings=("gentech","Legacy") + tuple(p for p in instance.PERIODS),
            values=lambda m, g: (g, sum(m.BuildProj[proj, bldyr] for (proj, bldyr) in m.PROJECT_BUILDYEARS
                if m.proj_gen_tech[proj] == g and bldyr not in m.PERIODS)) + tuple(
                sum(m.ProjCapacity[proj, p] for proj in m.PROJECTS if m.proj_gen_tech[proj] == g) 
                for p in m.PERIODS)
        )
        
        DF = pd.read_csv('outputs/Summaries/build_proj_by_tech_p.csv',sep='\t').transpose()
        DF.columns = DF.iloc[0]
        DF=DF.drop('gentech')
        fig = plt.figure(2)
        tech_ax = fig.add_subplot(211)
        # GO cycling through the rainbow to get line colours
        cm = plt.get_cmap('gist_rainbow')
        # You have to play with the color map and the line style list to get enough combinations for your particular plot
        tech_ax.set_prop_cycle(cycler('color',[cm(i/7.0) for i in range(0,8)]))
        # to locate the legend: "loc" is the point of the legend for which you will specify cooridnates. These coords are specified in bbox_to_anchor (can be only 1 point or couple)
        tech_plot = DF.plot(ax=tech_ax,kind='bar').legend(loc='upper center', fontsize=10, bbox_to_anchor=(0.,-0.07,1.,-0.07), ncol=2, mode="expand")
        plt.xticks(rotation=0,fontsize=12)
        plt.savefig('outputs/Summaries/gentech_capacities.pdf',bbox_extra_artists=(tech_plot,))
    


    if instance.options.export_tech_dispatch:
        """
        This table writes out the aggregated dispatch of each gen tech on each timepoint.
        """
        print "dispatch_proj_by_tech_tp.csv..."
        export.write_table(
            instance, instance.TIMEPOINTS,
            output_file=os.path.join(summaries_dir, "dispatch_proj_by_tech_tp.csv"),
            headings=("gentech",) + tuple(g for g in instance.GENERATION_TECHNOLOGIES) + ("total",),
            values=lambda m, tp: (m.tp_timestamp[tp],) + tuple(
                sum(m.DispatchProj[proj, t] for (proj, t) in m.PROJ_DISPATCH_POINTS 
                    if m.proj_gen_tech[proj] == g and t == tp) 
                for g in m.GENERATION_TECHNOLOGIES) + ( 
                sum(m.DispatchProj[proj, t] for (proj, t) in m.PROJ_DISPATCH_POINTS if t == tp),)
        )
        
        DF = pd.read_csv('outputs/Summaries/dispatch_proj_by_tech_tp.csv',sep='\t').drop(['gentech'],axis=1)
        fig = plt.figure(3)
        dis_ax = fig.add_subplot(211)
        # GO cycling through the rainbow to get line colours
        cm = plt.get_cmap('gist_rainbow')
        # You have to play with the color map and the line style list to get enough combinations for your particular plot
        dis_ax.set_prop_cycle(cycler('linestyle',['-','--',':']) * cycler('color',[cm(i/5.0) for i in range(0,6)]))
        # to locate the legend: "loc" is the point of the legend for which you will specify cooridnates. These coords are specified in bbox_to_anchor (can be only 1 point or couple)
        dis_plot = DF.plot(ax=dis_ax,linewidth=1.5).legend(loc='upper center', fontsize=10, bbox_to_anchor=(0.,-0.15,1.,-0.15), ncol=2, mode="expand")
        plt.xticks([i*5 for i in range(1,len(instance.TIMEPOINTS)/5+1)],[instance.tp_timestamp[instance.TIMEPOINTS[i*5]] for i in range(1,len(instance.TIMEPOINTS)/5+1)],rotation=40,fontsize=7)
        plt.savefig('outputs/Summaries/gentech_dispatch.pdf',bbox_extra_artists=(dis_plot,))
    
    if instance.options.export_reservoirs:
        """
        This table writes out reservoir levels in cubic meters per tp.
        """
        print "reservoir_final_vols_tp.csv..."
        export.write_table(
            instance, instance.TIMEPOINTS,
            output_file=os.path.join(summaries_dir, "reservoir_final_vols_tp.csv"),
            headings=("timepoints",) + tuple(r for r in instance.RESERVOIRS) + ("total",),
            values=lambda m, tp: (m.tp_timestamp[tp],) + tuple(m.ReservoirFinalvol[r, tp] - m.initial_res_vol[r] for r in m.RESERVOIRS) + ( 
                sum(m.ReservoirFinalvol[r, tp] - m.initial_res_vol[r] for r in m.RESERVOIRS),)
        )
        
        DF = pd.read_csv('outputs/Summaries/reservoir_final_vols_tp.csv',sep='\t').drop(['timepoints'],axis=1)
        fig2 = plt.figure(4)
        res_ax = fig2.add_subplot(211)
        # GO cycling through the rainbow to get line colours
        cm = plt.get_cmap('gist_rainbow')
        # You have to play with the color map and the line style list to get enough combinations for your particular plot
        res_ax.set_prop_cycle(cycler('linestyle',['-',':','--']) * cycler('color',[cm(i/5.0) for i in range(0,6)]))
        # to locate the legend: "loc" is the point of the legend for which you will specify cooridnates. These coords are specified in bbox_to_anchor (can be only 1 point or couple)
        res_plot = DF.plot(ax=res_ax,linewidth=1.5).legend(loc='upper center', fontsize=10, bbox_to_anchor=(0.,-0.15,1.,-0.15), ncol=2, mode="expand")
        plt.xticks([i*24 for i in range(1,len(instance.TIMEPOINTS)/24+1)],[instance.tp_timestamp[instance.TIMEPOINTS[i*24]] for i in range(1,len(instance.TIMEPOINTS)/24+1)],rotation=40,fontsize=7)
        plt.savefig('outputs/Summaries/reservoir_levels.pdf',bbox_extra_artists=(res_plot,))

    """
    Writing Objective Function value.
    """
    print "total_system_costs.txt..."
    with open(os.path.join(summaries_dir, "total_system_costs.txt"),'w+') as f:
        f.write("Total System Costs: "+str(instance.SystemCost())+"\n")
        f.write("Total Investment Costs: "+str(instance.TotalInvestmentCost())+"\n")
        f.write("Total Operations Costs: "+str(instance.TotalOperationsCost()))

    
    # # This table writes out the dispatch of each gen tech on each timepoint and load zone.
    # #This process is extremely slow, need to make it efficient
    # print "dispatch_proj_by_tech_lz_tp.csv..."
    # export.write_table(
    #     instance, instance.TIMEPOINTS, instance.LOAD_ZONES,
    #     output_file=os.path.join(summaries_dir, "dispatch_proj_by_tech_lz_tp.csv"),
    #     headings=("load zone", "timepoint",) + tuple(g for g in instance.GENERATION_TECHNOLOGIES),
    #     values=lambda m, tp, lz: (lz, m.tp_timestamp[tp],) + tuple(
    #         sum(m.DispatchProj[proj, t] for (proj, t) in m.PROJ_DISPATCH_POINTS 
    #             if m.proj_gen_tech[proj] == g and t == tp and m.proj_load_zone[proj] == lz) 
    #         for g in m.GENERATION_TECHNOLOGIES)
    # )   
    
    print "Time taken writing summaries: {dur:.2f}s".format(dur=time.time()-start)
