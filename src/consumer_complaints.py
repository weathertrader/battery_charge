
###############################################################################
# consumer_complaints.py 
# author: Craig Smith, craig.matthew.smith@gmail.com
# purpose: process consumer complaints to a report 
# revision history:  
#   03/15/2020 - original 
# data required: 
#   input csv file 
# usage:  
#   python3.7 ./src/consumer_complaints.py ./input/consumer_complaints.csv ./output/report.csv
# repository link
#   https://github.com/weathertrader/consumer_complaints_cs.git
#   test sumbmission here 
#   https://insight-cc-submission.com/test-my-repo-link
# directions 
#   https://github.com/insightdatascience/consumer_complaints
#
###############################################################################


# to do 
#   U   1 hr plot scaling, add to READme.md 
#   M   1 hr document tests 
#   W   1 hr add README.md - scaling, out of core compute -> dask and etc 
#   W   1 hr submit 




# flags to aid in manual debugging inside and IDE/Ipython console
#manual_debug = True
manual_debug = False

import sys
import os
import csv
import datetime as dt 
import time
    
print ('setting input and output file names ')
if (manual_debug): # manually set input and output files for debugging in Ipython or IDE
    base_dir = os.getcwd()
    base_dir = '/home/craigmatthewsmith/consumer_complaints_cs'
    os.chdir(base_dir)
    input_file  = os.path.join(base_dir,'input','consumer_complaints.csv')
    output_file = os.path.join(base_dir,'output','report.csv')
else:
    input_file  = sys.argv[1]
    output_file = sys.argv[2]
print('using input  file %s ' %(input_file))
print('using output file %s ' %(output_file))

# remove a pre-existing output file
if (os.path.isfile(output_file)):
    os.remove(output_file)

# assert that input file exists
if not (os.path.isfile(input_file)):
    print('ERROR missing input_file %s ' %(input_file))
    sys.exit()    

# manually define a-priori, could also be defined from csv header line
n_fields_expected = 18 
print ('n_fields_expected is %s ' %(n_fields_expected))

time_start = time.time()
print ('read data ')
# read data into empty arrays
yy_recvd_list = []
product_list  = []
company_list  = []
with open(input_file, "r", encoding="utf-8") as csv_read_file: # force utf-8 encoding 
    next(csv_read_file)
    for row in csv.reader(csv_read_file):
        # here check number of entries per row
        n_fields = len(row)
        #print ('%s n_fields found' %(n_fields))
        if not (n_fields == n_fields_expected):
            print ('ERROR - incorrect number of fields in row %s ' %(row))
        else: 
            dt_temp_str =  row[0]
            product_temp = row[1]
            company_temp = row[7]
            if (str.isspace(product_temp) or str.isspace(company_temp) or not(product_temp) or not(company_temp)):
                print ('ERROR with product or company fields, "%s", "%s" ' %(product_temp, company_temp))
                next(csv_read_file)
            else: # continue reading this row 
                try: # if any single one fails, no fields should be appended at all 
                    #yy_recvd_list.append(dt.datetime.strptime(dt_temp_str, '%Y-%m-%d').year)
                    yy_recvd_list.append(dt.datetime.strptime(dt_temp_str, '%Y-%m-%d').year)
                    product_list.append(product_temp.lower())
                    company_list.append(company_temp.lower())
                except: # ValueError: 
                    print ('ERROR skipping row  due to malformed datetime string %s ' %(dt_temp_str))
time_end = time.time()
process_dt = (time_end - time_start)/60.0
print ('read    data took %5.2f minutes ' %(process_dt))

print ('find unique products, companies and years')
# find unique products, companies and years and sort alphabetically and numerically 
products_unique  = sorted(list(set(product_list)))
companies_unique = sorted(list(set(company_list)))
yy_unique        = sorted(list(set(yy_recvd_list)))

print ('count total number of individual entries') 
# count total number of indiviudal entries 
n_yy        = len(yy_unique)
n_products  = len(products_unique)
n_companies = len(companies_unique)
print ('unique entries found: %s years, %s products, %s companies ' %(n_yy, n_products, n_companies)) 

time_start = time.time()
print ('analyze and write data') 
yy = 5
product = 5
#count = 0 # easy way to keep track of two loops, np array shown below is simpler
# write the data 
#count = 0
with open(output_file, 'w', newline='') as csv_write_file:
    # quotechar will add " if string contains a comma
    csv_writer = csv.writer(csv_write_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    for product in range(0, n_products, 1):
        #print('  processing product %s of %s ' %(str(product), str(n_products)))
        temp_string1 = products_unique[product] 
        for yy in range(0, n_yy, 1):
            #print('    processing yy '+str(yy_unique[yy]))
            product_filtered = list(product_elements for yy_elements, product_elements in zip(yy_recvd_list, product_list) if yy_elements == yy_unique[yy] and product_elements == products_unique[product])
            companies_filtered = list(company_elements for yy_elements, product_elements, company_elements in zip(yy_recvd_list, product_list, company_list) if yy_elements == yy_unique[yy] and product_elements == products_unique[product])
            #print('      found %s and %s products and unique companies ' %(len(product_filtered), len(set(companies_filtered))))
            if (len(product_filtered) > 0):
                n_complaints_per_product_per_yr = len(product_filtered)
                # len(set) calculates unique entries
                n_companies_per_product_per_yr = len(set(companies_filtered))
                # avoid dividing by zeros in case of no complaints
                #if (n_complaints_per_product_per_yr[count] > 0):
                # int() always rounds floats down, round() gives the desired behavior
                percent_max_per_product_per_yr = round(100.0*float(n_companies_per_product_per_yr)/float(n_complaints_per_product_per_yr))
                temp_string2 = temp_string1+','+str(yy_unique[yy])+','+str(n_complaints_per_product_per_yr)+','+str(n_companies_per_product_per_yr)+','+str(percent_max_per_product_per_yr)
                csv_writer.writerow([products_unique[product], str(yy_unique[yy]), str(n_complaints_per_product_per_yr), str(n_companies_per_product_per_yr), str(percent_max_per_product_per_yr)])
                #count = count+1
time_end = time.time()
process_dt = (time_end - time_start)/60.0
print ('analyze data took %5.2f minutes ' %(process_dt))



        

