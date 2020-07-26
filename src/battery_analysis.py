
'''
name: battery_analysis.py 
purpose: analyze battery deration
author: Craig Smith, craig.matthew.smith@gmail.com
usage: ./src/run.sh n  where n is the number of batteries to analyze [1-5]
repo: https://github.com/weathertrader/battery_charge
'''
# TO DO 
# 1 hr  readme, including documentation on da and results and images
# 1 hr  refactor and clean up 
# 1 hr  run from cli using bash script



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

    # read data into empty arrays
    dt_epoch_energy_left = []
    dt_epoch_energy_full = []
    dt_epoch_charge_avail = []
    energy_left = []
    energy_full = []
    charge_avail = []
    
    # sys.maxsize
    dt_epoch_min = sys.maxsize
    dt_epoch_max = -sys.maxsize
    
    batt_id = int(input_file.split('/')[1].split('.')[0])
    
    # PW_EnergyRemaining  - energy left in batter [Wh]
    with open(input_file, "r", encoding="utf-8") as csv_read_file: # force utf-8 encoding 
        next(csv_read_file)
        for row in csv.reader(csv_read_file):
            # here check number of entries per row
            n_fields = len(row)
            #print ('%s n_fields found' %(n_fields))
    
            # check that battery id never changes 
            #print(row)
            if not int(row[0]) == batt_id:
                print ('ERROR - battery id changed')
                sys.exit()
            if n_fields != 4:
                print ('ERROR - incorrect number of fields in row %s ' %(row))
                next(csv_read_file)
                # sys.exit()
                
            field_read = row[2]
            if (field_read == ''):
                    #print ('ERROR - missing data %s ' %(row))
                    next(csv_read_file)
                    # sys.exit()
            else:
                    
                #check if this in in there already or not
                #dt_epoch_energy_left
                if (int(row[1])/1000 in dt_epoch_energy_left):
                    print('error duplicated value1')
                    sys.exit()
                if (int(row[1])/1000 in dt_epoch_energy_full):
                    print('error duplicated value2')
                    sys.exit()
                if (int(row[1])/1000 in dt_epoch_charge_avail):
                    print('error duplicated value3')
                    sys.exit()
                    
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
                
    # print(dt_epoch_min, dt_epoch_max)
    dt_min = dt.fromtimestamp(dt_epoch_min)
    dt_max = dt.fromtimestamp(dt_epoch_max)
    # calculate length of data set and expected number of records 
    # assume UTC for monthly roll ups 
    print('    dt range %s - %s ' %(dt_min.strftime('%Y-%m-%d %H:%M:%S'), dt_max.strftime('%Y-%m-%d %H:%M:%S')))
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

    # df_energy_left.get_duplicates()
    # drop duplicate values 
    #df_energy_full[df_energy_full.index.duplicated(keep='first')]
    #df_energy_full[df_energy_full.index.duplicated(keep='last')]
    #df_energy_full[df_energy_full.index.duplicated(keep=False)]
    #df_energy_left = df_energy_left.drop_duplicates(keep='first')
    #df_energy_full = df_energy_full.drop_duplicates(keep='first')
    #df_charge_avail = df_charge_avail.drop_duplicates(keep='first')
    #df_energy_left = df_energy_left.drop_duplicates(keep=False)
    #df_energy_full = df_energy_full.drop_duplicates(keep=False)
    #df_charge_avail = df_charge_avail.drop_duplicates(keep=False)
    
    
    #df_energy_left.drop_duplicates(keep=False, inplace=True)
    #df_energy_full.drop_duplicates(keep=False, inplace=True)
    #df_charge_avail.drop_duplicates(keep=False, inplace=True)
 
    df_energy_left = df_energy_left.loc[~df_energy_left.index.duplicated(keep=False)]
    df_energy_full = df_energy_full.loc[~df_energy_full.index.duplicated(keep=False)]
    df_charge_avail = df_charge_avail.loc[~df_charge_avail.index.duplicated(keep=False)]

    print('    records expected %s found %s %s %s ' %(n_records_expected, len(df_energy_left), len(df_energy_full), len(df_charge_avail)))
    print('    missing %5.2f percent of data ' %(100.0 - 100.0*min(len(df_energy_left), len(df_energy_full), len(df_charge_avail))/n_records_expected))
    
    #df_energy_left = df_energy_left.loc[~df_energy_left.index.duplicated(keep='first')]
    #df_energy_full = df_energy_full.loc[~df_energy_full.index.duplicated(keep='first')]
    #df_charge_avail = df_charge_avail.loc[~df_charge_avail.index.duplicated(keep='first')]
    
    #df_energy_full[df_energy_full.index.duplicated(keep=False)]
    #df_energy_left[df_energy_left.index.duplicated(keep=False)]
    #df_charge_avail[df_charge_avail.index.duplicated(keep=False)]

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
    # len(battery_df)
    #battery_df.head(20)
    #battery_df.tail(20)
    #  how='inner'

    # compute state of energy, soe = PW_EnergyRemaining / PW_FullPackEnergyAvailable
    # soe > 90% is 'starting to get full'
    battery_df['soe'] = 100.0*battery_df['energy_left']/battery_df['energy_full']

    return battery_df

def compute_data_availability(battery_df):

    # count total valid records
    n_records = len(battery_df)
    n_valid_records = battery_df['charge_avail'].count()

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

    # merge mo_df to cp_all    
    # cp_all_df = cp_all_df.merge(mo_df, left_index=True, right_index=True, how='outer')
    
    cp_all_df.head()
    
    # list(cp_all_df)
    
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
    
    n = 3
    input_file = input_files[n]
    for n, input_file in enumerate(input_files):        
        print('  reading file %s of %s, %s' %(n, len(input_files), input_file))
        battery_df = read_battery_file(input_file)        
        mo_df = compute_data_availability(battery_df)
        cp_all_df = calc_charge_power_availability(battery_df)

        # compute monthly charge power availability w/o consideration of soe at all 
        # cp_avail = time where monthly average charge_avail >= 3300.0 
        cp_avail_soe_not_cons = 100.0*cp_all_df['cp_avail_soe_n_cons'] / (cp_all_df['cp_avail_soe_n_cons'] + cp_all_df['cp_not_avail_soe_n_cons'])    
        # monthly charge power availability excluding soe > 90.0, battery getting full
        cp_avail_soe_cons = 100.0*cp_all_df['cp_avail_soe_either'] / (cp_all_df['cp_avail_soe_either'] + cp_all_df['cp_not_avail_soe_not_full'])

        # assert all data sets contains the same months assumed    
        # n_mo_read = cp_all_df.index[-1] - cp_all_df.index[0]
        # if not (list(cp_all_df.index) == list(mo_axis)):
        #     print('ERROR - months dont match expected')
        #    sys.exit()
            
        # accumulate individual batteries statistics into an array at appropiate month location
        cp_avail_soe_not_cons_n[cp_all_df.index[0]-1:cp_all_df.index[-1],n] = cp_avail_soe_not_cons
        cp_avail_soe_cons_n[cp_all_df.index[0]-1:cp_all_df.index[-1],n] = cp_avail_soe_cons
        da_n[mo_df.index[0]-1:mo_df.index[-1],n] = mo_df['data_availability']
        

    # plot the data 

    dpi_level = 500
    
    # single bar plot
    n = 0    
    
    [mo_min, mo_max, mo_int] = [7, 13, 1]
    mo_ticks = np.arange(mo_min, mo_max, mo_int)
    [mo_min_plot, mo_max_plot] = [7.5, 12.5]
    
    [y_min, y_max, y_int] = [0, 110, 20]
    y_ticks = np.arange(y_min, y_max, y_int)
    
    
    fig_num = 101 
    fig = plt.figure(num=fig_num,figsize=(10,6)) 
    plt.clf() 
    
    #plt.subplot(2, 1, 1)
    plt.bar(mo_axis, cp_avail_soe_not_cons_n[:,n], color='k', linestyle='-', width=0.8)
    #plt.bar(r_axis, bias_ws_s_h_r , color=colors_r, linestyle='-', width=0.8)
    # rects1 = ax.bar(ind, menMeans, width, color='r', yerr=menStd)
    #plt.plot([0.0, n_runs+1], [ 0, 0],  'gray', linestyle='-', linewidth=0.5, marker='o', markersize=0) 
    #plt.legend(loc=2,fontsize=12,ncol=1)
    plt.title('charge power availability vs month, battery '+str(n+1)+'\nstate of energy not considered', \
         fontsize=16,  x=0.0, y=1.01, horizontalalignment='left') 
    
    plt.xticks(mo_ticks, fontsize=14) 
    plt.xlim([mo_min_plot, mo_max_plot]) 
    #ax.set_xticklabels(stn_id, rotation='vertical')
    plt.yticks(y_ticks, fontsize=14)    
    plt.ylim([y_min, y_max]) 
    plt.xlabel('month of 2017 ',fontsize=14,labelpad=00) 
    plt.ylabel('charge power availability [%]',fontsize=14,labelpad=10)
    
    filename = 'battery_charge1.png' 
    plot_name = os.path.join('images', filename)
    plt.savefig(plot_name, dpi=dpi_level)
    
    fig_num = 102
    fig = plt.figure(num=fig_num,figsize=(10,6)) 
    plt.clf() 
    
    #plt.subplot(2, 1, 1)
    plt.bar(mo_axis, cp_avail_soe_cons_n[:,n], color='k', linestyle='-', width=0.8)
    #plt.bar(r_axis, bias_ws_s_h_r , color=colors_r, linestyle='-', width=0.8)
    # rects1 = ax.bar(ind, menMeans, width, color='r', yerr=menStd)
    #plt.plot([0.0, n_runs+1], [ 0, 0],  'gray', linestyle='-', linewidth=0.5, marker='o', markersize=0) 
    #plt.legend(loc=2,fontsize=12,ncol=1)
    plt.title('charge power availability vs month, battery '+str(n+1)+'\nstate of energy considered', \
         fontsize=16,  x=0.0, y=1.01, horizontalalignment='left') 
    
    plt.xticks(mo_ticks, fontsize=14) 
    plt.xlim([mo_min_plot, mo_max_plot]) 
    #ax.set_xticklabels(stn_id, rotation='vertical')
    plt.yticks(y_ticks, fontsize=14)    
    plt.ylim([y_min, y_max]) 
    plt.xlabel('month of 2017 ',fontsize=14,labelpad=00) 
    plt.ylabel('charge power availability [%]',fontsize=14,labelpad=10)
    
    filename = 'battery_charge2.png' 
    plot_name = os.path.join('images', filename)
    plt.savefig(plot_name, dpi=dpi_level)
    
    
    colors = ['r', 'b', 'g', 'c', 'm']
    bar_width = 0.18
    
    fig_num = 103
    fig = plt.figure(num=fig_num,figsize=(10,6)) 
    plt.clf() 
    for n in range(0, n_files):
        plt.bar(mo_axis+(n-2)*bar_width, cp_avail_soe_cons_n[:,n], color=colors[n], label=str(n+1), linestyle='-', width=bar_width)
    
    #plt.legend(loc=2,fontsize=10) 
    plt.legend(loc=2,fontsize=10,ncol=n_files) 
    
    plt.title('charge power availability vs month, all batteries \nstate of energy considered', \
         fontsize=16,  x=0.0, y=1.01, horizontalalignment='left') 
    
    plt.xticks(mo_ticks, fontsize=14) 
    plt.xlim([mo_min_plot, mo_max_plot]) 
    #ax.set_xticklabels(stn_id, rotation='vertical')
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





# battery_serial,timestamp,signal_name,signal_value
# energy_left      PW_EnergyRemaining  - energy left in batter [Wh]
# energy_full      PW_FullPackEnergyAvailable - total energy capacity of battery [Wh]
# charge_avail     PW_AvailableChargePower - max power capacity that battery can charge at this time [W]
# PW_AvailableChargePower = 3300 W except when it derates

# flags to aid in manual debugging inside and IDE/Ipython console
#manual_debug = True
# manual_debug = False
    
# print ('setting input and output file names ')
# if (manual_debug): # manually set input and output files for debugging in Ipython or IDE
#     base_dir = os.getcwd()
#     base_dir = '/home/craigmatthewsmith/consumer_complaints_cs'
#     os.chdir(base_dir)
#     input_file  = os.path.join(base_dir,'input','consumer_complaints.csv')
#     output_file = os.path.join(base_dir,'output','report.csv')
# else:
#     input_file  = sys.argv[1]
#     output_file = sys.argv[2]
# print('using input  file %s ' %(input_file))
# print('using output file %s ' %(output_file))




