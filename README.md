# Consumer Complaints

## Table of Contents
1. [Run Instructions](README.md#run-instructions)
1. [Solution](README.md#Solution)
1. [Tests](README.md#tests)
1. [Scaling Tests](README.md#Scaling-tests)
1. [Questions?](README.md#questions?)


## Run Instructions 

Clone the repo, enter the dictory and execute `./run.sh` from the cli.

That script will assume that you have python3.7 on your system

## Solution

My solution steps in `./src/consumer_complaints.py` are roughly as follows:

0) define input and output file names and check that the former exists
1) read the csv and check for malformed data and missing fields
2) append good input data to 3 lists with year received, company name and product name 
3) find unique products, companies and years from each of those lists, and order them alphabetically and numerically
4) count total number of individual products, years and companies 
5) looping over unique years and products, analyze the data using a list comprehension looking for elements that match expected, count the results, and write to a csv

Since my background is primarily in scientific computing I also created an alternative solution using `numpy` in `./src/consumer_complaints_using_np.py`.

## Tests

My code (`./src/consumer_complaints.py`) contains logic that checks for malformed data in the input csv file.
I chose to add malformed data to sample input files in the `insight_testsuite/test_*` as follows:

* `test_1` - insight input file as assigned 
* `test_2` - checks datetime_format, wrong date format, etc 
* `test_3` - checks number of fields per row and missing data, number of entries or commas per line
* `test_4` - checks for wonky company and product names, non-utf characters

## Scaling Tests 

I wanted to test the scaling of files of larger sizes, so I created copies of the ~1G large csv that was linked in the assignment.
I created copies at 1/4, 1/2, 2x and 4x the size of original using the simple bash commands

```
head -n 1200000 consumer_complaints_x1.0.csv >> consumer_complaints_x0.50.csv
head -n 600000 consumer_complaints_x1.0.csv >> consumer_complaints_x0.25.csv
cat consumer_complaints_x1.0.csv consumer_complaints_x1.0.csv > consumer_complaints_x2.0.csv
cat consumer_complaints_x2.0.csv consumer_complaints_x2.0.csv > consumer_complaints_x4.0.csv
```

and then checked rows per file and file size using 


```
wc -l consumer_complaints*csv
 600000 consumer_complaints_x0.25.csv
1200000 consumer_complaints_x0.50.csv
2485465 consumer_complaints_x1.0.csv
4970930 consumer_complaints_x2.0.csv
9941860 consumer_complaints_x4.0.csv

du -hs consumer_complaints*csv
235M    consumer_complaints_x0.25.csv
408M    consumer_complaints_x0.50.csv
902M    consumer_complaints_x1.0.csv
1.8G    consumer_complaints_x2.0.csv
3.6G    consumer_complaints_x4.0.csv
```

These files are too large to be included in the git repo, so I've added them to the `.gitignore` file (and thus you won't be able to run them)

I moved and renamed these input csvs into the top level input directory and recorded the timing for processing each with `./run_tests_scaling.sh` of the two most time-intensive steps (`read_data` and `analyze_data`) of the code using `time` as follows (in minutes) on my chromebook linux container: 

```
read_data    = [0.08, 0.19, 0.46, 0.94, 1.83]
analyze_data = [0.16, 0.43, 0.92, 2.04, 3.63]
```

and normalized by the x1 file size (original) as 

```
read_data    = [0.173, 0.41, 1.00, 2.04, 3.98]
analyze_data = [0.174, 0.47, 1.00, 2.21, 3.95]
```

which means that the algorithms are scaling linearly.

I assumed that out-of-core file sizes are beyond the scope of this coding challenge.

In case of very large file sizes (and due to the nature of single GIL in python), I would have tried an approach using `multiprocessing ` to process single core chunks of the file
and then a `map/reduce` algorithm to process the data.  The latter would have to be slightly arranged from what I submitted as a single core solution.  Naturally my first choice for out-of-core csv would have been some combination of `dask`, `pandas`, and `numpy`.

## Questions?
Email me at craig.matthew.smith@gmail.com
