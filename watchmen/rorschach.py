#!/bin/usr/python
"""
Created on May 22, 2017
# ' None of you seem to understand.  I'm not locked in here with you.
#   You're locked in here with ME!'
#  -Rorschach, The Watchmen 2009
This script is designed to monitor S3.  Specifically looking to ensure that parquet
data is flowing into the current day's folder in S3.  It should run every hour, and
verify that the current day exists, and that parquet data in it is not very old.
@author: Dan Dalton
@email: ddalton@infoblox.com
"""

# Python Imports
import datetime as _datetime
import os as _os
import pytz as _pytz
import timeit as _timeit
import traceback as _traceback
# External Libraries
import boto3.session as _boto3_session
import cyberint_aws.s3 as _s3

# Private Global Constants
_FATALERROR = 1
_SUCCESS = 0
_FILENAME = "rorschach_hancock_watcher"
_PREFIX = "PREFIX"
_BUCKET_NAME = "BUCKET_NAME"
_SUBJECT_MESSAGE = "Rorschach Detected: Farsight S3 Service Outage!"
_ERROR_MESSAGE = "ERROR: "
_NOTHING_RECENT_MESSAGE = _ERROR_MESSAGE + "No files found created recently.\n"
_NOTHING_PARQUET_MESSAGE = _ERROR_MESSAGE + "No files founding containing .parquet extensions.\n"
_EVERYTHING_ZERO_SIZE_MESSAGE = _ERROR_MESSAGE + "No .parquet files found with file sizes great than zero.\n"
# Option Help Strings (Private, Global, Constant)
_DEBUGHELP = "Used to enable debug level logging."
_LOCALHELP = "Used to enable local spark mode, no parallelization."
# Option Defaults
_DEBUGDFLT = False
_LOCALDFLT = False

_SUCCESS_HEADER = """
*******************************************************************
   SSSS    UU   UU     CCCCC     CCCCC   EEEEEE    SSSS     SSSS
  SS  SS   UU   UU    CC        CC       EE       SS  SS   SS  SS
   SS      UU   UU   CC        CC        EE        SS       SS
    SS     UU   UU   CC        CC        EEEEE      SS       SS
     SS    UU   UU   CC        CC        EE          SS       SS
  SS  SS   UU   UU    CC        CC       EE       SS  SS   SS  SS
   SSSS     UUUUU      CCCCC     CCCCC   EEEEEE    SSSS     SSSS
*******************************************************************"""

_FAILURE_HEADER = """
*******************************************************************
  FFFFFF    AAAAA    IIIIII   LL       UU   UU   RRRRRR    EEEEEE
  FF       AA   AA     II     LL       UU   UU   RR   RR   EE
  FF       AA   AA     II     LL       UU   UU   RR   RR   EE
  FFFFF    AAAAAAA     II     LL       UU   UU   RRRRRR    EEEEE
  FF       AA   AA     II     LL       UU   UU   RR   RR   EE
  FF       AA   AA     II     LL       UU   UU   RR   RR   EE
  FF       AA   AA   IIIIII   LLLLLL    UUUUU    RR   RR   EEEEEE
*******************************************************************"""


class RorschachWatcher(object):
    """
    RorschachWatcher class
    """

    suffix_format = "month=%0m/day=%0d"
    prefix = _os.getenv(_PREFIX)
    bucket = _os.getenv(_BUCKET_NAME)
    offset = 3
    # offset + pst:   we're looking for 2 hours back, BUT we want to subtract the 7 hour PST vs UTC too
    # This is to make sure we don't look for "Tomorrow's" folder, before we're actually in Tomorrow...
    dt_offset = _datetime.timedelta(hours=offset)

    def __init__(self):
        """
        RorschachWatcher constructor
        """
        # Get the current Day and Time we care about
        self.nothing_recent = True
        self.nothing_parquet = True
        self.everything_zero_size = True
        self.now = _datetime.datetime.now(_pytz.utc)
        print "Current Time: %s" % self.now
        self.check_time = self.now - self.dt_offset
        print "Check Time: %s" % self.check_time
        self.suffix = self.check_time.strftime(self.suffix_format)
        assert self.prefix is not None, "ERROR: PREFIX Environment variable is not defined!"
        assert self.bucket is not None, "ERROR: BUCKET_NAME Environment variable is not defined!"
        self.full_path = "{}/{}/".format(self.prefix, self.suffix)

    def process_all_files(self):
        """
        Checks the date, size, and type of every file.
        :return: true if there is at least one parquet, no zero file in the last X hours else False
        """

        # Use paginator to ensure we get all contents (when contents > 1000)
        contents = _s3.generate_pages(self.full_path, **{'bucket': self.bucket})
        most_recent = None
        count = 0

        # Find the most recent file.
        for key in contents:
            if count == 0 or most_recent < key.get('LastModified'):
                most_recent = key.get('LastModified')
                latest_file = key
            count += 1
        print "Searched through %d files." % count
        print "Most Recent File was: %s - the check time was %s" % (most_recent, self.check_time)

        # Determine that at least the most recent file is parquet, and not zero
        if most_recent > self.check_time:
            self.nothing_recent = False
        if latest_file.get('Size') > 0:
            self.everything_zero_size = False
        if latest_file.get('Key').endswith('.parquet'):
            self.nothing_parquet = False

    def check_parquet_stream(self):
        """
        check parquet stream
        """

        # Get the file list from S3
        print "Checking: %s" % self.full_path
        empty, contents = _s3.check_empty_folder(self.full_path, self.bucket)

        if empty:
            self.raise_alarm("The S3 bucket for today is empty or missing!  %s" % self.full_path)
            return 1
        print("The directory is not empty at:  %s" % self.full_path)

        # Ensure the most recent file is within the specified duration.
        self.process_all_files()

        # If not - RAISE ALARM!
        msg = ""
        if self.nothing_recent:
            msg += _NOTHING_RECENT_MESSAGE
        if self.nothing_parquet:
            msg += _NOTHING_PARQUET_MESSAGE
        if self.everything_zero_size:
            msg += _EVERYTHING_ZERO_SIZE_MESSAGE

        if msg is not "":
            self.raise_alarm(msg + "\n\t%s\n\t%s" % (self.full_path, self.check_time))
            return 1
        else:
            return 0

    @staticmethod
    def get_sns_client():
        """
        Get SNS client
        note: This function can be customized to accept configurations
        """
        session = _boto3_session.Session()
        sns_client = session.client('sns')
        return sns_client

    @staticmethod
    def raise_alarm(msg):
        """
        raise alarm
        """

        print("***Sounding the Alarm!***\n" + msg)
        sns_client = RorschachWatcher.get_sns_client()
        response = sns_client.publish(
            TopicArn='arn:aws:sns:us-east-1:405093580753:Hancock',
            Message=msg,
            Subject=_SUBJECT_MESSAGE
        )
        try:
            assert response['ResponseMetadata']['HTTPStatusCode'] == 200, \
                "ERROR Publishing to sns failed!"
        except KeyError:
            print _ERROR_MESSAGE + "Response did not contain HTTPStatusCode\n"
            print response


# pylint: disable=unused-argument
def main(event, context):
    """ Main Function"""
    start = _timeit.default_timer()

    # Create Miner
    watcher = RorschachWatcher()

    # Call the meat of the script
    try:
        my_result = watcher.check_parquet_stream()
    except Exception as ex:
        print("ERROR Processing Data!\n")
        print(_traceback.format_exc(ex))
        my_result = _FATALERROR

    # Add Headers to the Log File for quick indication of results.
    if my_result == _SUCCESS:
        print(_SUCCESS_HEADER)
    else:
        print(_FAILURE_HEADER)
    stop = _timeit.default_timer()
    print("Run time: %s" % (stop - start))
    return my_result
