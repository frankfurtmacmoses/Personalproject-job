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
import watchmen.utils.s3 as _s3
from watchmen.config import settings
from watchmen.utils.sns_alerts import raise_alarm
from watchmen.utils.logger import get_logger

# Private Global Constants
_EMPTY = 0
_ERROR = -1
_SUCCESS = 1
_FILENAME = "rorschach_hancock_watcher"
_PREFIX = "PREFIX"
_BUCKET_NAME = "BUCKET_NAME"
_SUBJECT_EXCEPTION_MESSAGE = "Rorschach failed due to an Exception!"
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
    sns_topic_arn = settings("rorschach.sns_topic", "arn:aws:sns:us-east-1:405093580753:Watchmen_Test")
    suffix_format = "year=%0Y/month=%0m/day=%0d"
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
        self.logger = get_logger('Rorschach', settings('logging.level', 'INFO'))
        # Get the current Day and Time we care about
        self.nothing_recent = True
        self.nothing_parquet = True
        self.everything_zero_size = True
        self.traceback = None
        self.now = _datetime.datetime.now(_pytz.utc)
        self.logger.info("Current Time: %s" % self.now)
        self.check_time = self.now - self.dt_offset
        self.logger.info("Check Time: %s" % self.check_time)
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
        self.logger.info("Searched through %d files." % count)
        self.logger.info("Most Recent File was: %s - the check time was %s" % (most_recent, self.check_time))

        # Determine that at least the most recent file is parquet, and not zero
        if most_recent > self.check_time:
            self.nothing_recent = False
        if latest_file.get('Size') > 0:
            self.everything_zero_size = False
        if latest_file.get('Key').endswith('.parquet'):
            self.nothing_parquet = False

    def summarize_parquet_stream(self):
        """
        check parquet stream
        @return: A dict containing all notification information
        """
        # Get the file list from S3
        self.logger.info("Checking: %s" % self.full_path)
        empty, contents = _s3.check_empty_folder(self.full_path, self.bucket)

        if empty:
            msg = "The S3 bucket for today is empty or missing!  %s" % self.full_path
            return {
                "success": False,
                "subject": _SUBJECT_MESSAGE,
                "message": msg
            }

        self.logger.info("The directory is not empty at:  %s" % self.full_path)

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

        if msg is "":
            return {
                "success": True,
                "message": _SUCCESS_HEADER
            }

        return {
            "success": False,
            "subject": _SUBJECT_MESSAGE,
            "message": msg
        }

    def get_parquet_result(self):
        """
        Gets the result from the parquet stream check.
        Results can either be 'success', 'empty', or a message indicating that a failure occurred.
        @return: One the expected results or 'error' upon exception
        """
        try:
            my_result = self.summarize_parquet_stream()
            self.logger.info(my_result)
        except Exception as ex:
            self.logger.error("ERROR Processing Data!\n")
            self.traceback = _traceback.format_exc(ex)
            self.logger.error(self.traceback)
            msg = "An error occurred while checking the parquet at {} due to the following:" \
                  "\n\n{}\n\n".format(self.check_time, self.traceback)
            my_result = {
                "success": False,
                "subject": _SUBJECT_EXCEPTION_MESSAGE,
                "message": msg + "\n\t%s\n\t%s" % (self.full_path, self.check_time)
            }

        return my_result

    def notify(self, parquet_result):
        """
        If the parquet result is not a success, send an email alarm message.
        @param parquet_result: the status of the check
        @return: a header indicating success or failure
        """
        self.logger.info(parquet_result)
        success = parquet_result.get('success')
        subject = parquet_result.get('subject')
        message = parquet_result.get('message')

        if success:
            return message

        # Have to send email alarm
        raise_alarm(topic_arn=self.sns_topic_arn, msg=message, subject=subject)
        self.logger.info(_FAILURE_HEADER)
        return _FAILURE_HEADER


# pylint: disable=unused-argument
def main(event, context):
    """
    Ensures parquet data is flowing into the current day's s3 folder
    @return: the status of the parquet data flow
    """
    start = _timeit.default_timer()

    # Create Miner
    watcher = RorschachWatcher()

    parquet_results = watcher.get_parquet_result()
    status = watcher.notify(parquet_results)

    stop = _timeit.default_timer()
    print("Run time: %s" % (stop - start))
    return status
