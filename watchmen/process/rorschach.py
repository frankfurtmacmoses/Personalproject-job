"""
Created on May 22, 2017
# ' None of you seem to understand.  I'm not locked in here with you.
#   You're locked in here with ME!'
#  -Rorschach, The Watchmen 2009
This Watchman is designed to generically monitor S3 targets across multiple schedules.
This Watchman can a monitor a target for single or multiple file existence, single file
size greater than zero, aggregate file size greater than a predefined value, and file count
greater than a predefined value. The required checks for a target are determined in the config file 's3_targets.py.'

@author: Dan Dalton
@email: ddalton@infoblox.com

Refactored on April, 2020
@author: Bonnie Zhang
@email: zzhang@infoblox.com
"""

# Python Imports
import datetime as _datetime
import traceback as _traceback
# External Libraries
from watchmen import messages
from watchmen.common.result import Result
import watchmen.utils.s3 as _s3
from watchmen.config import settings
from watchmen.common.watchman import Watchman

MESSAGES = messages.RORSCHACH
HOURLY = "Hourly"
DAILY = "Daily"
ALL_EVENT_TYPES = [HOURLY, DAILY]


class Rorschach(Watchman):

    def __init__(self, event, context):
        """
        Constructor of Rorschach
        """
        super().__init__()
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

    def monitor(self) -> [Result]:
        """
        monitor the parquet data, and return the result
        @return: <Result> Result ojbect
        """
        summary = self._get_parquet_result()
        result = self._create_result(summary)
        return [result]

    def _create_result(self, summary):
        """
        Create the result object
        @param summary: <dict> dictionary with three keys: "success", "subject", "details"
        @return: <Result> result based on the parameters
        """
        state_chart = {
            True: {
                "message": _SUCCESS_MESSAGE,
                "success": True,
                "disable_notifier": True,
                "state": Watchman.STATE.get("success"),
            },
            False: {
                "message": _SUBJECT_MESSAGE,
                "success": False,
                "disable_notifier": False,
                "state": Watchman.STATE.get("failure"),
            },
            None: {
                "message": _SUBJECT_EXCEPTION_MESSAGE,
                "success": None,
                "disable_notifier": False,
                "state": Watchman.STATE.get("exception"),
            }
        }
        check_result = summary.get("success")
        subject = summary.get("subject")
        details = summary.get("details")
        parameters = state_chart.get(check_result)
        result = Result(
            **parameters,
            subject=subject,
            source=self.source,
            target=TARGET,
            details=details)
        return result

    def _get_parquet_result(self):
        """
        Gets the result from the parquet stream check.
        Results can either be 'success', 'empty', or None indicating that a failure occurred.
        Also return the traceback of the exception.
        @return: <boo;l> <str>
            <bool>: One the expected results or 'error' upon exception
            <str>: traceback
        """
        try:
            my_result = self._summarize_parquet_stream()
            self.logger.info(my_result)
        except Exception as ex:
            self.logger.error("ERROR Processing Data!\n")
            self.traceback = _traceback.format_exc(ex)
            self.logger.error(self.traceback)
            msg = "An error occurred while checking the parquet at {} due to the following:" \
                  "\n\n{}\n\n".format(self.check_time, self.traceback)
            my_result = {
                "success": None,
                "subject": _SUBJECT_EXCEPTION_MESSAGE,
                "details": msg + "\n\t%s\n\t%s" % (self.full_path, self.check_time)
            }

        return my_result

    def _process_all_files(self):
        """
        Checks the date, size, and type of every file.
        @return: true if there is at least one parquet, no zero file in the last X hours else False
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

    def _summarize_parquet_stream(self):
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
                "details": msg
            }

        self.logger.info("The directory is not empty at:  %s" % self.full_path)

        # Ensure the most recent file is within the specified duration.
        self._process_all_files()

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
                "subject": _SUCCESS_SUBJECT,
                "details": _SUCCESS_MESSAGE
            }

        return {
            "success": False,
            "subject": _SUBJECT_MESSAGE,
            "details": msg
        }
