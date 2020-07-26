
'''
name: battery_analysis.py 
purpose: analyze battery deration
author: Craig Smith, craig.matthew.smith@gmail.com
usage: ./src/run.sh n  where n is the number of batteries to analyze [1-5]
repo: https://github.com/weathertrader/battery_charge
'''

import os
import sys
import csv
import pandas as pd
import numpy as np
from datetime import datetime as dt 
import glob
import matplotlib
import matplotlib.pyplot as plt
# plotting from cli
matplotlib.use('Agg') 

#os.getcwd()
#os.chdir('/home/csmith/battery_charge')
#n_files = 5

def read_battery_file(input_file):

    # data dictionary    
    # energy_left      PW_EnergyRemaining  - energy left in batter [Wh]
    # energy_full      PW_FullPackEnergyAvailable - total energy capacity of battery [Wh]
    # charge_avail     PW_AvailableChargePower - max power capacity that battery can charge at this time [W]
    
    # read data into empty arrays
    dt_epoch_energy_left = []
    dt_epoch_energy_full = []
    dt_epoch_charge_avail = []
    energy_left = []
    energy_full = []
    charge_avail = []
    
    # initialize min and max dates 
    dt_epoch_min = sys.maxsize
    dt_epoch_max = -sys.maxsize
    
    batt_id = int(input_file.split('/')[1].split('.')[0])
    
    with open(input_file, "r", encoding="utf-8") as csv_read_file: # force utf-8 encoding 
        next(csv_read_file)
        for row in csv.reader(csv_read_file):
            n_fields = len(row)
            # check that battery id never changes 
            if not int(row[0]) == batt_id:
                print ('ERROR - battery id changed')
                sys.exit()
            # check that input data has correct number of fields
            if n_fields != 4:
                print ('ERROR - incorrect number of fields in row %s ' %(row))
                next(csv_read_file)                
            # check that variable is well defined
            field_read = row[2]
            if (field_read == ''):
                    next(csv_read_file)
            else:                                        
                # accumulate data and timestamp into lists
                if   field_read == 'PW_EnergyRemaining':
                    # may need to cast to int
                    dt_epoch_energy_left.append(int(row[1])/1000)
                    energy_left.append(float(row[3]))       
                elif field_read == 'PW_FullPackEnergyAvailable':
                    dt_epoch_energy_full.append(int(row[1])/1000)
                    energy_full.append(float(row[3]))
                elif field_read == 'PW_AvailableChargePower':                
                    dt_epoch_charge_avail.append(int(row[1])/1000)
                    charge_avail.append(float(row[3]))
                if (int(row[1]) < dt_epoch_min):
                    dt_epoch_min = int(row[1])/1000
                if (int(row[1]) > dt_epoch_max):
                    dt_epoch_max = int(row[1])/1000
                
    # print start and end of data set
    dt_min = dt.fromtimestamp(dt_epoch_min)
    dt_max = dt.fromtimestamp(dt_epoch_max)
    # assume UTC for monthly roll ups 
    print('    dt range %s - %s ' %(dt_min.strftime('%Y-%m-%d %H:%M:%S'), dt_max.strftime('%Y-%m-%d %H:%M:%S')))

    # calculate length of data set and expected number of records 
    reports_per_hour_expected = int(60/5) # reports every 5 min
    n_records_expected = (dt_max-dt_min).days * 24 * reports_per_hour_expected \
                       + int((dt_max-dt_min).seconds/3600 * reports_per_hour_expected)
    
    # convert epoch time to datetime stamp, could be done in place if memory was constrained by a large dataset 
    dt_energy_left  = [dt.fromtimestamp(x) for x in dt_epoch_energy_left]
    dt_energy_full  = [dt.fromtimestamp(x) for x in dt_epoch_energy_full]
    dt_charge_avail = [dt.fromtimestamp(x) for x in dt_epoch_charge_avail]
    
    # create dataframes based on the raw data
    df_energy_left  = pd.DataFrame(energy_left, index=dt_energy_left, columns =['energy_left'])         
    df_energy_full  = pd.DataFrame(energy_full, index=dt_energy_full, columns =['energy_full']) 
    df_charge_avail = pd.DataFrame(charge_avail, index=dt_charge_avail, columns =['charge_avail']) 
    # drop duplicate index entries, two values for a single timestamp     
    df_energy_left = df_energy_left.loc[~df_energy_left.index.duplicated(keep=False)]
    df_energy_full = df_energy_full.loc[~df_energy_full.index.duplicated(keep=False)]
    df_charge_avail = df_charge_avail.loc[~df_charge_avail.index.duplicated(keep=False)]
    print('    records expected %s found %s %s %s ' %(n_records_expected, len(df_energy_left), len(df_energy_full), len(df_charge_avail)))
    print('    missing %5.2f percent of data ' %(100.0 - 100.0*min(len(df_energy_left), len(df_energy_full), len(df_charge_avail))/n_records_expected))
    
    # move records to nearest 5 min time, here we assume that time offsets by 30s or 1 min 
    # can be treated as if they were at the same time 
    df_energy_left  = df_energy_left.resample('5min').fillna("pad", limit=1)
    df_energy_full  = df_energy_full.resample('5min').fillna("pad", limit=1)
    df_charge_avail = df_charge_avail.resample('5min').fillna("pad", limit=1)
    
    # check that the interpolated time series have the same number of records and begin and end at the same time 
    if not (len(df_energy_left) == len(df_energy_full)) and (len(df_energy_left) == len(df_charge_avail)):
        print('ERROR - need to match up the time series before combining')
        sys.exit()
    if not (df_energy_left.index[0] == df_energy_full.index[0]) and (df_energy_full.index[0] == df_charge_avail.index[0]):
        print('ERROR - need to match up the time series before combining')
        sys.exit()
    if not (df_energy_left.index[-1] == df_energy_full.index[-1]) and (df_energy_full.index[-1] == df_charge_avail.index[-1]):
        print('ERROR - need to match up the time series before combining')
        sys.exit()

    battery_df = df_energy_left.join(df_energy_full).join(df_charge_avail)
    # compute state of energy, soe = PW_EnergyRemaining / PW_FullPackEnergyAvailable
    battery_df['soe'] = 100.0*battery_df['energy_left']/battery_df['energy_full']
    return battery_df

def compute_data_availability(battery_df):

    # compute month valid records    
    mo_df = pd.DataFrame(battery_df['soe'].resample("M").count())
    # replace index with month of year 
    mo_df.index = pd.DatetimeIndex(mo_df.index).month
    mo_df.columns = ['n_valid_records']
    #mo_df.head()
     
    # compute data availability vs month, rough estimate is fine for now
    n_records_expected_per_month = 30*24*12 # could use actual days per month instead 
    mo_df['data_availability'] = 100.0*mo_df['n_valid_records']/n_records_expected_per_month
    return mo_df

def calc_charge_power_availability(battery_df):
    
    # compute charge availability with and w/o consideration of soe
    df0 = pd.DataFrame(battery_df[(battery_df['charge_avail'] <  3300.0)]['charge_avail'].resample("M").count())
    df1 = pd.DataFrame(battery_df[(battery_df['charge_avail'] >= 3300.0)]['charge_avail'].resample("M").count())
    df2 = pd.DataFrame(battery_df[(battery_df['charge_avail'] >= 3300.0) & (battery_df['soe'] >=  0.0) & (battery_df['soe'] < 100.0)]['charge_avail'].resample("M").count())
    df3 = pd.DataFrame(battery_df[(battery_df['charge_avail'] <  3300.0) & (battery_df['soe'] >= 90.0) & (battery_df['soe'] < 100.0)]['charge_avail'].resample("M").count())
    df4 = pd.DataFrame(battery_df[(battery_df['charge_avail'] <  3300.0) & (battery_df['soe'] >=  0.0) & (battery_df['soe'] <  90.0)]['charge_avail'].resample("M").count())    
    df0.columns = ['cp_not_avail_soe_n_cons']
    df1.columns = ['cp_avail_soe_n_cons']
    df2.columns = ['cp_avail_soe_either']
    df3.columns = ['cp_not_avail_soe_full']
    df4.columns = ['cp_not_avail_soe_not_full']
    cp_all_df = df0.merge(df1, left_index=True, right_index=True, how='outer')\
                   .merge(df2, left_index=True, right_index=True, how='outer')\
                   .merge(df3, left_index=True, right_index=True, how='outer')\
                   .merge(df4, left_index=True, right_index=True, how='outer')
    cp_all_df.index = pd.DatetimeIndex(cp_all_df.index).month
    del df0, df1, df2, df3, df4    

    cp_all_df['cp_not_avail_soe_full'] = cp_all_df['cp_not_avail_soe_full'].fillna(0)
    cp_all_df['cp_not_avail_soe_not_full'] = cp_all_df['cp_not_avail_soe_not_full'].fillna(0)
    return cp_all_df

def analyze_batteries(n_files):
    
    mo_axis = np.arange(1, 13)
    n_mo = len(mo_axis)
    cp_avail_soe_not_cons_n = np.full([n_mo, n_files], np.nan, dtype=float)
    cp_avail_soe_cons_n = np.full([n_mo, n_files], np.nan, dtype=float)
    da_n = np.full([n_mo, n_files], np.nan, dtype=float)
    
    input_files = glob.glob('data/*.csv') # glob sorts the files
    #print(input_files)
    n_files_found = len(input_files)
    if n_files_found < n_files:
        print('ERROR - no input files found')
        sys.exit()
    elif n_files_found > n_files:
        input_files = input_files[0:n_files]        
    
    n = 0
    input_file = input_files[n]
    for n, input_file in enumerate(input_files):        
        print('  reading file %s of %s, %s' %(n, len(input_files), input_file))
        # read data
        battery_df = read_battery_file(input_file)        
        # compute data availability
        mo_df = compute_data_availability(battery_df)
        # compute charge power availability
        cp_all_df = calc_charge_power_availability(battery_df)

        # compute monthly charge power availability w/o consideration of soe at all 
        # cp_avail = time where monthly average charge_avail >= 3300.0 
        cp_avail_soe_not_cons = 100.0*cp_all_df['cp_avail_soe_n_cons'] / (cp_all_df['cp_avail_soe_n_cons'] + cp_all_df['cp_not_avail_soe_n_cons'])    
        # monthly charge power availability excluding soe > 90.0, battery getting full
        cp_avail_soe_cons = 100.0*cp_all_df['cp_avail_soe_either'] / (cp_all_df['cp_avail_soe_either'] + cp_all_df['cp_not_avail_soe_not_full'])
            
        # accumulate individual batteries statistics into an array at matching month indices
        cp_avail_soe_not_cons_n[cp_all_df.index[0]-1:cp_all_df.index[-1],n] = cp_avail_soe_not_cons
        cp_avail_soe_cons_n[cp_all_df.index[0]-1:cp_all_df.index[-1],n] = cp_avail_soe_cons
        da_n[mo_df.index[0]-1:mo_df.index[-1],n] = mo_df['data_availability']
        

    # plot the data 
    dpi_level = 500
    [mo_min, mo_max, mo_int] = [7, 13, 1]
    mo_ticks = np.arange(mo_min, mo_max, mo_int)
    [mo_min_plot, mo_max_plot] = [7.5, 12.5]    
    [y_min, y_max, y_int] = [0, 110, 20]
    y_ticks = np.arange(y_min, y_max, y_int)
    colors = ['r', 'b', 'g', 'c', 'm']
    bar_width = 0.18
    
    n = 0    
    # single battery bar plot, no soe considered        
    fig_num = 101 
    fig = plt.figure(num=fig_num,figsize=(10,6)) 
    plt.clf()     
    plt.bar(mo_axis, cp_avail_soe_not_cons_n[:,n], color='k', linestyle='-', width=0.8)
    plt.title('charge power availability vs month, battery '+str(n+1)+'\nstate of energy not considered', \
         fontsize=16,  x=0.0, y=1.01, horizontalalignment='left')     
    plt.xticks(mo_ticks, fontsize=14) 
    plt.xlim([mo_min_plot, mo_max_plot]) 
    plt.yticks(y_ticks, fontsize=14)    
    plt.ylim([y_min, y_max]) 
    plt.xlabel('month of 2017 ',fontsize=14,labelpad=00) 
    plt.ylabel('charge power availability [%]',fontsize=14,labelpad=10)    
    filename = 'battery_charge1.png' 
    plot_name = os.path.join('images', filename)
    plt.savefig(plot_name, dpi=dpi_level)
    
    # single battery bar plot, soe considered
    fig_num = 102
    fig = plt.figure(num=fig_num,figsize=(10,6)) 
    plt.clf() 
    plt.bar(mo_axis, cp_avail_soe_cons_n[:,n], color='k', linestyle='-', width=0.8)
    plt.title('charge power availability vs month, battery '+str(n+1)+'\nstate of energy considered', \
         fontsize=16,  x=0.0, y=1.01, horizontalalignment='left')     
    plt.xticks(mo_ticks, fontsize=14) 
    plt.xlim([mo_min_plot, mo_max_plot]) 
    plt.yticks(y_ticks, fontsize=14)    
    plt.ylim([y_min, y_max]) 
    plt.xlabel('month of 2017 ',fontsize=14,labelpad=00) 
    plt.ylabel('charge power availability [%]',fontsize=14,labelpad=10)    
    filename = 'battery_charge2.png' 
    plot_name = os.path.join('images', filename)
    plt.savefig(plot_name, dpi=dpi_level)
        
    # all batteries bar plot, soe considered
    fig_num = 103
    fig = plt.figure(num=fig_num,figsize=(10,6)) 
    plt.clf() 
    for n in range(0, n_files):
        plt.bar(mo_axis+(n-2)*bar_width, cp_avail_soe_cons_n[:,n], color=colors[n], label=str(n+1), linestyle='-', width=bar_width, edgecolor='k')    
    plt.legend(loc=2,fontsize=10,ncol=n_files)
    plt.title('charge power availability vs month, all batteries \nstate of energy considered', \
         fontsize=16,  x=0.0, y=1.01, horizontalalignment='left')     
    plt.xticks(mo_ticks, fontsize=14) 
    plt.xlim([mo_min_plot, mo_max_plot]) 
    plt.yticks(y_ticks, fontsize=14)    
    plt.ylim([y_min, y_max]) 
    plt.xlabel('month of 2017 ',fontsize=14,labelpad=00) 
    plt.ylabel('charge power availability [%]',fontsize=14,labelpad=10)    
    fig.tight_layout()
    plt.show()    
    filename = 'battery_charge3.png' 
    plot_name = os.path.join('images', filename)
    plt.savefig(plot_name, dpi=dpi_level)
          
if __name__ == "__main__":
    n_files  = int(sys.argv[1])
    print('processing %s files' %(n_files))
    analyze_batteries(n_files)


