"""
spark script to curate a file of original TI-Atlas data into the curated version for the Data Lake
This is a code update to original dns curation with a different design.
​
Usage:
spark-submit --deploy-mode cluster dns_curation.py -outpath full_path [-date date, -inpath alternate_input_path]
​
to avoid retry on failure use flag:
--conf spark.yarn.maxAppAttempts=1
​
based on the curation HLD found here:
https://docs.google.com/document/d/1E6DW3CoGcQWyNXmRWzW-BRwguNS2QrJE4nfJJJ7Jsm0/edit?ts=5e691a8b#heading=h.1nxa6wtr546b
​
sample data is located in s3, including input and output data:
s3://cyber-intel/poseidon/dns
​
This design walks the S3 directories to find customers that have logs for the given date. It then runs an ETL job for
each customer separately, including all of their different data sources. This means we run ~340-350 separate ETLs jobs,
but that each job is smaller and doesn't contain skew of our original approach.  The directory walk is done via fsspec
and uses a series of base paths for DNS data, currently the B1DDI path and other path. This could be adjusted
if the company created more paths. Because TI stores the data by customer and not by date, we have to walk every single
path in S3 and look for current data. Once date paths are found, we try to extract the storage ID using a regex from the
path. If there is a storage ID (6-7 digits) AND there is data for the run date, then we add all the paths for that id
to a list.  A dictionary of storage ids is created, with values as the lists of paths.
​
Next, for each storage id, we load all the paths and ETL the data. We do not load the filename, and instead assign the
storage_id field directly from the dictionary. Otherwise the ETL is the same as the old curation.
*** in this version, we have a hotfix for bad NIOS data in which the ancount = 0 regardless of the true value
    this conversion should be removed once NIOS fixes the upstream data *****
​
Because of the way that partitioned writes work in spark, the partitioning columns are not actually stored
in the final parquet files, only in the path. We need these values available, particularly the storage id, in our final
files in the event they are used independent of the partitioned path. To accomplish this, we'll add dummy variables and
use those as the partitioning variables: _storage_id and _pname.  If the file is read from S3 using wildcard, these
columns will be in the loaded parquet (for a select *). Additionally, we use a MAX_RECORDS per file and a repartition
prior to the write in order to balance the resulting parquet and minimize the number of output files.
​
There is some small chance the repartition for a customer will fail.  In that event, I've tried to fail gracefully
using a try/except clause. A secondary process could be used to search the logs for failed customers and rerun using the
full customer path so only the customer is run.  I am writing to both the log file and to the spark logs. the logfile
will not make it to s3 if the job fails.
​
This code is taking 1.3 - 1.5 hours to run on data from 10/26-10/30/20.  Records range up to 4.5B in those days.
​
author: rburton
date: 10/31/2020
"""

from datetime import datetime, timedelta
from dateutil import parser as date_parser
from pyspark.sql import SparkSession
from pyspark.sql.types import IntegerType
from s3fs import S3FileSystem
import argparse
import atexit
import common_utils as cu
import dremio_utils as du
import fsspec
import logging
import os
import pyspark.sql.functions as sqlfn
import re
import time

spark = SparkSession.builder.appName("dns log curation").getOrCreate()

#####
#
# SET UP GLOBAL VARIABLES
#
#####
# you can adjust the number of partitions -- fewer partitions will take longer to run because we use a repartition(n)
# however more partitions will mean small datafiles for some customers. it might be reasonable take this up to 90-100
# 60 partitions is taking about 1.3-1.5 hours.   coalesce would be much faster, but could fail if a partition is too big
# NUM_PARTITIONS = 60  # number of partitions/files to write out for a storage id

# these are the subset of fields that move to curation
# 12/8/2020 Added the last 5 fields to be included in curated data as they will be used in downstream pipelines and
# reporting. They are view,username, region, cmac and extra fields

# 02/12/2021 For reporting we start to run dns curation more frequently starting with once every 20 mins.
# At the end of a successful curation write we also move data out of the landing zone and move to ttl bucket for the
# dataset where we may store up to last 60 days of data.
# This would mean we process smaller chunks in each batch and so we don't repartition to strictly
# 60 files in each batch. We rather set the maxRecords count as 10 million. This data is again read later by a
# 'condensing' process that further squashes the number of files even lower than 60 by giving an even larger
# maxRecordsPerFile value and written back to the cz.

WANTED_FIELDS = ['opcode', 'timestamp', 'qname', 'qtype', 'qclass', 'source', 'qip', 'rip', 'protocol', 'rcode',
                 'type', 'rqr', 'raa', 'rtc', 'rrd', 'rra', 'rad', 'rcd', 'rdo', 'rrr1', 'rrr2', 'rrr3',
                 'ancount', 'nscount', 'arcount', 'pid', 'cid', 'tid', 'nanosec', 'anonymized', 'username', 'region',
                 'cmac', 'extra', 'view']
LOGDIR = 'logs'
LOGFILE = 'curated_files.log'
LOG_LEVEL = logging.INFO
MAX_RECORDS = 10000000


def set_up_logging(s3_logpath: str) -> None:
    """
    sets up logging with the s3 path for logging info. registers function to move logs to s3 on successful exit.
    :param s3_logpath: the s3 path for logging info
    :return: None
    """
    s3 = S3FileSystem()

    logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    logpath = f"{LOGDIR}/{LOGFILE}"
    if LOGFILE:  # logging is local and moved to s3 later
        if LOGDIR and not os.path.exists(LOGDIR):
            os.mkdir(LOGDIR)
        logging.basicConfig(filename=logpath, level=LOG_LEVEL)
    else:  # print to stdout
        logging.basicConfig(level=LOG_LEVEL)
    logging.info(f"established logging at {LOGFILE}")
    # move the logs to S3 at finish
    if s3_logpath:
        atexit.register(write_logs_to_s3, s3, logpath=logpath, s3_logpath=s3_logpath)
    return

def write_logs_to_s3(s3, logpath: str, s3_logpath: str) -> None:
    """
    moves log files from the local machine to the s3 path
​
    :param logpath: local path
    :param s3_logpath: s3 path
    :return: None
    """
    if s3_logpath:
        logging.info(f"moving logfile at {logpath} locally to S3 at {s3_logpath}")
        s3.put(logpath, s3_logpath)
    else:
        logging.info(f"no s3 path provided for remote logs in s3_logfile configuration")
    return


def refresh_dremio_pds(args: object):
    logging.info(f"dremio_root_url: {args.dremio_root_url}")
    logging.info(f"dremio_user_name: {args.dremio_user_name}")
    logging.info(f"pds_path: {args.pds_path}")

    secret_dict = cu.get_secret(args.dremio_secret, "us-east-1")
    secret_value = secret_dict[args.dremio_secret_key]
    dremio = du.Dremio(args.dremio_root_url, args.dremio_user_name, secret_value)
    auth_token = dremio.generate_auth_token()
    dremio.metadata_refresh(auth_token, args.pds_path)
    return


def main(args):
    # default date should be the day prior to running when run in batch mode so it gets full day of data
    # this date value corresponds to the date of the events not the date the code was run
    # if current_date is passed then that overrides everything and runs for current day.
    date = date_parser.parse(args.date) if args.date else datetime.today() - timedelta(1)
    if args.current_date is True:
        date = datetime.today()

    date_list = [date]
    if date.hour == 0: # To keep polling for the previous day's data, until 1 hour into the new day
        date_list.append(date - timedelta(1))

    s3_logpath = args.logpath.format(year=date.strftime("%Y"), month=date.strftime("%m"), day=date.strftime("%d"))

    # log setup time to append to the filename
    date_suffix = datetime.today().strftime('%Y%m%d%H%M%S')
    s3_logpath = s3_logpath.replace("customer.log", f"customer_{date_suffix}.log")

    # this is to set up the logging and move the logs to S3 at finish
    set_up_logging(s3_logpath)
    logging.info(f'Running for dates {date_list}')

    success_flag = True
    for date in date_list:
        logging.info(f"Started processing for {date}")
        return_code = curate(date, args)
        logging.info(f"Return code for {date} is {return_code}")
        success_flag*=return_code

    try:
        logging.info(f"Metadatarefresh: {args.metadatarefresh}")
        if args.metadatarefresh:
            refresh_dremio_pds(args)
            logging.info(f"PDS metadata refresh posted for {args.pds_path}")
    except Exception as ex:
        logging.error(f"Metadata refresh failed with error: {ex}")
        success_flag = False

    if not success_flag:
        error_msg = "Processing failed for one of the dates. Please check the logs for more details!"
        logging.error(error_msg)
        raise Exception(error_msg)
    return


def curate(date: datetime, args: object ) -> bool:
    # Return True if the processing is successful for all storage_ids for the given date
    # Returns False otherwise

    success_flag = True
    input_path = args.inpath
    ttl_prefix_val = args.ttl_prefix

    output_path = args.outpath.format(year=date.strftime("%Y"), month=date.strftime("%m"), day=date.strftime("%d"))

    # we iterate through the base paths to identify customer paths that have data for the given date. for valid storage
    # ids which contain data, we create a list of paths to search for logs.
    t0 = time.time()
    try:
        fs = fsspec.filesystem('s3')
        data = fs.ls(input_path)

        legacy_pat = re.compile('.+\.+(\d{6,7})')  # pattern to identify a valid storage ID from <com.infoblox.300014>
        latest_pat = re.compile('.+(?:customer|storage_id)=(\d{6,7})')  # storage_id from <customer|storage_id=300014>

        data_paths = {}
        for customer in data:
            logging.info(f"customer: {customer}")
            latest_match = re.match(latest_pat, customer)
            legacy_match = re.match(legacy_pat, customer)
            if latest_match:  # check the second pattern with "customer=<storage_id>"
                storage_id = latest_match.group(1)
                if storage_id:
                    logging.info(f"latest_match storage id: {storage_id}")
                else:
                    logging.info(f"ERROR: empty storage_id")
            elif legacy_match:  # matches a real customer for old pattern
                storage_id = legacy_match.group(1)
                if storage_id:
                    logging.info(f"legacy_match storage id: {storage_id}")
                else:
                    logging.info(f"ERROR: empty storage_id")
            else:
                continue
            date_path = f"{customer}/year={date:%Y}/month={date:%m}/day={date:%d}/"
            if fs.isdir(date_path):
                s3_path = f"s3://{date_path}" + "*.parquet"
                if storage_id not in data_paths.keys():
                    data_paths[storage_id] = [s3_path]  # add path
                else:
                    data_paths[storage_id].append(s3_path)
                logging.info(f"date_path: {date_path}")
            else:
                continue
    except Exception as ex:
        logging.error(f"Processing failed for {date}: {ex}")
        return False
    t1 = time.time()
    logging.info(f"Time taken to identify customers and their input files: {t1 - t0} secs,  Start time: {t0}, End time: {t1}")

    # at this point, we have a dictionary where the keys are valid storage IDs that have data for the given date, and
    # the values are the list of paths where those logs are located.

    # now we're going to loop through t...





















