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
import os
import pytz
import yaml
import traceback

# External Libraries
from watchmen import const, messages
from watchmen.common.result import Result
import watchmen.utils.s3 as _s3
from watchmen.config import settings
from watchmen.common.watchman import Watchman

MESSAGES = messages.RORSCHACH
ENVIRONMENT = settings("ENVIRONMENT", "test")
CONFIG_NAME = 's3_targets_{}.yaml'.format(ENVIRONMENT)
CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), CONFIG_NAME)
HOURLY = "Hourly"
DAILY = "Daily"
ALL_EVENT_TYPES = [HOURLY, DAILY]


class Rorschach(Watchman):

    def __init__(self, event, context):
        """
        Constructor of Rorschach
        """
        super().__init__()
        self.event = event.get("Type")

    def monitor(self):
        """
        Monitors the s3 targets.
        @return: <Result> List of Result objects
        """
        if self._check_invalid_event():
            return self._create_invalid_event_results()

        s3_targets, tb = self._load_config()
        if tb:
            return self._create_config_not_load_results(tb)

        check_results = self._process_checking(s3_targets)
        summary_parameters = self._create_summary_parameters(check_results)
        results = self._create_result(summary_parameters)

        return results

    def _check_invalid_event(self):
        """
        Method to check that the event passed in from the Lambda has the correct parameters. If there is no "Type"
        parameter passed in, or the "Type" does not equal any of the allowed event types, then the
        event parameter is invalid.
        @return: True if the event parameter passed from the Lambda is invalid, false if the event parameter is valid.
        """
        if not self.event or self.event not in ALL_EVENT_TYPES:
            self.logger.info(MESSAGES.get("failed_event_check").format(self.event))
            return True
        self.logger.info(MESSAGES.get("success_event_check"))

        return False

    def _create_invalid_event_results(self):
        """
        Method to create the results for the scenario when the Lambda sends in invalid event parameters.
        @return: List of a single Result object to be sent to the Generic S3 target
        """
        return [Result(
            disable_notifier=False,
            state=Watchman.STATE.get("exception"),
            success=False,
            subject=MESSAGES.get("exception_invalid_event_subject"),
            watchman_name=self.watchman_name,
            target="Generic S3",
            details=MESSAGES.get("exception_invalid_event_details"),
            snapshot={},
            short_message=MESSAGES.get("exception_message"),
        )]

    def _load_config(self):
        """
        Method to load the .yaml config file that contains configuration details of each s3 target.
        @return: a tuple of the s3 targets, None or None, traceback upon exception
        """
        try:
            with open(CONFIG_PATH) as f:
                s3_targets = yaml.load(f, Loader=yaml.FullLoader)
            s3_targets = s3_targets.get(self.event)
            return s3_targets, None
        except Exception as ex:
            self.logger.error("ERROR Processing Data!")
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception('{}: {}'.format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            return None, tb

    def _create_config_not_load_results(self, tb):
        """
        Method to create the Result object if the config file did not successfully loaded.
        @return: One result object for the email SNS topic.
        """
        return [Result(
            disable_notifier=False,
            state=Watchman.STATE.get("exception"),
            success=False,
            subject=MESSAGES.get("exception_config_load_failure_subject"),
            watchman_name=self.watchman_name,
            target="Generic S3",
            details=MESSAGES.get("exception_config_not_load_details").format(CONFIG_NAME, tb),
            snapshot={},
            short_message=MESSAGES.get("exception_message"),
        )]

    def _process_checking(self, s3_targets):
        """
        Method to conduct various checks for each S3 item under each target. The specific checks for each
        item is determined from the config data. It is possible for there to be many targets and each
        with multiple S3 items. For each item, the appropriate method will be called to handle the amount of files being
        checked.
        :param s3_targets: The list of dictionaries loaded from the s3_targets config file. Each dictionary contains
                           items to be checked.
        :return: A dictionary containing all of the dictionaries for each target that was checked. For each target,
                 a dictionary will be creating which contains:
                    - a boolean "success" indicating if the check was valid (True: success, False: failures (and
                      exceptions), None: all checks resulted in exceptions.
                    - a list "exception_strings" which contains strings that detail any exceptions encountered.
                    - a list "failure_strings" which contains strings that detail any failures encountered.

        Example returned dictionary:
            processed_targets =
            {
                'target1': {
                    'success': True,
                    'exception_strings: [],
                    'failure_strings: []
                },
                'target2': {
                    'success': False,
                    'exception_strings: ["example exception message", ...],
                    'failure_strings: ["example failure message", ...]
                }
                'target3': {
                    'success': None,
                    'exception_strings: ["only exceptions were encountered while performing checks for this target."],
                    'failure_strings: []
                ]
            }
        """
        processed_targets = {}

        for target in s3_targets:
            exception_strings = []
            failure_strings = []

            for item in target['items']:

                bucket_name = item.get('bucket_name')
                bucket_exists, tb = _s3.check_bucket(bucket_name)

                if tb:
                    exception_strings.append(MESSAGES.get("exception_string_format").format(item, tb))
                    continue
                elif not bucket_exists:
                    failure_strings.append(MESSAGES.get('failure_bucket_not_found').format(item.get('bucket_name')))
                    continue

                # If an item has the attribute 'full_path', then only one file is being checked.
                if item.get('full_path'):
                    file_check_exceptions, file_check_failures = self._check_single_file(item)
                else:
                    file_check_exceptions, file_check_failures = self._check_multiple_files(item)

                exception_strings.extend(file_check_exceptions)
                failure_strings.extend(file_check_failures)

            processed_targets.update(
                {
                    target.get('target_name'):
                        {
                            # Success is None if there were only exceptions, False if failures (and exceptions), and
                            # True if all checks passed.
                            'success': None if exception_strings and not failure_strings else len(failure_strings) == 0,
                            'exception_strings': exception_strings,
                            'failure_strings': failure_strings
                        }
                })

        return processed_targets

    def _check_single_file(self, item):
        """
        Method to perform all of the required checks if an item consists of only one file.
        :param item: The current item that is being checked. This item is a member of a "target" which are all defined
                     in the s3_targets config file.
        :return: The exceptions_strings list and the failure_strings list. Each of these lists contains the exceptions
                 and failures encountered while performing the checks. If all checks are successful, both of these lists
                 will be empty.
        """
        exception_strings = []
        failure_strings = []
        full_path = item.get("full_path")

        # Generating properly formatted S3 key:
        time_offset = item.get("offset", 1)
        s3_key, tb = self._generate_key(full_path, self.event, time_offset)

        if tb:
            exception_strings.append(MESSAGES.get("exception_string_format").format(item, tb))
            return exception_strings, failure_strings

        # Checking for single file existence:
        found_file, tb = self._check_single_file_existence(item, s3_key)

        if tb:
            exception_strings.append(MESSAGES.get("exception_string_format").format(item, tb))
            return exception_strings, failure_strings

        if not found_file:
            failure_strings.append(MESSAGES.get('failure_no_file_found_s3').format(s3_key))
            return exception_strings, failure_strings

        # Checking single file size:
        if item.get("check_total_size_kb"):
            valid_file_size, tb = self._check_single_file_size(item, s3_key)
            if tb:
                exception_strings.append(MESSAGES.get("exception_string_format").format(item, tb))
            if not valid_file_size:
                failure_strings.append(MESSAGES.get('failure_single_file_size').format(full_path,
                                                                                       item.get(
                                                                                           "check_total_size_kb")))
        return exception_strings, failure_strings

    def _check_single_file_size(self, item, s3_key):
        """
        Method to check that the single file size meets the required size set in the s3_targets config file.
        :param item: The current item, with one file, that is being checked.
        :return: boolean: True if the file is a valid size, false if not.
                 string: Traceback if an exception occurred, None otherwise.
        """
        try:
            kb_threshold = item.get("check_total_size_kb")
            s3_key_object = _s3.get_key(item.get("bucket_name"), s3_key)
            # Size from the s3_key_object is in bytes.
            valid_file_size = (s3_key_object.get("size") / 1000) >= kb_threshold
            return valid_file_size, None
        except Exception as ex:
            self.logger.error("ERROR Checking Single File Size!")
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception("{}: {}".format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            return None, tb

    def _check_multiple_files(self, item):
        """
        Method to perform all of the required checks if an item consists of multiple files.
        :param item: The current item that is being checked. This item is a member of a "target" which are all defined
                     in the s3_targets config file.
        :return: The exceptions_strings list and the failure_strings list. Each of these lists contains the exceptions
                 and failures encountered while performing the checks. If all checks are successful, both of these lists
                 will be empty.
        """
        exception_strings = []
        failure_strings = []

        # Generating contents from all files and returning if a failure or an exception is encountered:
        contents, count, prefix_generate, full_path, tb = self._generate_contents(item)

        if tb:
            exception_strings.append(MESSAGES.get("exception_string_format").format(item, tb))
            return exception_strings, failure_strings

        if not count:
            failure_strings.append(MESSAGES.get('failure_no_file_found_s3').format(prefix_generate))
            return exception_strings, failure_strings

        # Updating contents if there is a time offset required for the current item:
        if item.get('check_most_recent_file'):
            contents = self._check_most_recent_file(contents, item.get('check_most_recent_file'))

        # Check the prefix and suffix of all files:
        prefix_suffix_match, tb = self._check_file_prefix_suffix(contents, item.get('suffix'), prefix_generate)
        if tb:
            exception_strings.append(MESSAGES.get("exception_string_format").format(item, tb))
        if prefix_suffix_match is False:
            failure_strings.append(MESSAGES.get('failure_prefix_suffix_not_match').format(item.get('prefix'),
                                                                                          item.get('suffix')))

        # Check for empty files:
        at_least_one_file_empty, empty_file_list, tb = self._check_file_empty(contents)
        if tb:
            exception_strings.append(MESSAGES.get("exception_string_format").format(item, tb))
        if at_least_one_file_empty:
            empty_file_string = ""
            for empty_file in empty_file_list:
                empty_file_string += MESSAGES.get('failure_file_empty').format(empty_file)
            failure_strings.append(empty_file_string)

        # Check if aggregate file size meets standards:
        if item.get('check_total_size_kb'):
            is_total_size_less_than_threshold, total_size, tb = self._compare_total_file_size_to_threshold(
                contents, item.get('check_total_size_kb'))
            if tb:
                exception_strings.append(MESSAGES.get("exception_string_format").format(item, tb))
            if is_total_size_less_than_threshold:
                failure_strings.append(MESSAGES.get('failure_total_file_size_below_threshold').format(
                    full_path, total_size, item.get('check_total_size_kb')))

        # Check if the aggregate file count meets standards:
        if item.get('check_total_object'):
            if count < item.get('check_total_object'):
                failure_strings.append(MESSAGES.get('failure_count_too_less').format(full_path, count,
                                                                                     item['check_total_object']))

        return exception_strings, failure_strings

    def _create_details(self, target_name, target_check_results):
        """
        Method to create the details for a target.
        :param target_name: A string for the name of the target that was checked.
        :param target_check_results: A dictionary containing the results from checking the target and all of its items.
        :return: A string with properly formatted details for the passed in target.
        """
        success = target_check_results.get("success")

        if success:
            return MESSAGES.get("success_details").format(target_name)

        if success is None:
            exception_string = "\n\n".join(target_check_results.get("exception_strings"))
            return MESSAGES.get('exception_details').format(exception_string)

        failure_string = "\n\n".join(target_check_results.get("failure_strings"))
        if target_check_results.get("exception_strings"):
            exception_string = "\n\n".join(target_check_results.get("exception_strings"))
            failure_string += MESSAGES.get('exception_details').format(exception_string)
        return failure_string

    def _create_summary_parameters(self, processed_targets):
        """
        Method to create a summary object for all s3 targets with details messages based on the check results summary.
        @return: A list of dictionaries where each dict is a summary of the checking results of each target.
        """
        summary_parameters = []
        parameter_chart = {
            None: {
                "disable_notifier": False,
                "short_message": MESSAGES.get("exception_message"),
                "state": Watchman.STATE.get("exception"),
                "success": None
            },
            True: {
                "disable_notifier": True,
                "state": Watchman.STATE.get("success"),
                "success": True
            },
            False: {
                "disable_notifier": False,
                "state": Watchman.STATE.get("failure"),
                "success": False
            }
        }

        for target_name in processed_targets:
            success = processed_targets[target_name].get("success")
            result_parameters = dict(parameter_chart.get(success))
            result_parameters["details"] = self._create_details(target_name, processed_targets[target_name])
            result_parameters["target"] = target_name

            if success:
                result_parameters["short_message"] = MESSAGES.get("success_message").format(target_name)
                result_parameters["subject"] = MESSAGES.get("success_subject").format(target_name)

            elif processed_targets[target_name].get('success') is None:
                result_parameters["short_message"] = MESSAGES.get("exception_message")
                result_parameters["subject"] = MESSAGES.get("exception_checking_subject").format(target_name)

            else:
                # If there are exceptions and failures:
                if processed_targets[target_name].get("exception_strings"):
                    result_parameters["short_message"] = MESSAGES.get("failure_exception_message")
                    result_parameters["subject"] = MESSAGES.get("failure_exception_subject").format(target_name)
                else:
                    result_parameters["short_message"] = MESSAGES.get("failure_message")
                    result_parameters["subject"] = MESSAGES.get("failure_subject").format(target_name)

            summary_parameters.append(result_parameters)

        return summary_parameters

    def _create_result(self, summary):
        """
        Method to create a full result object based on the summary. This is used for sending email SNS topic when
        the target's state is "failure" and "exception".
        @return: One return object of all targets for the email SNS topics.
        """
        state_chart = {
            True: {
                "success": True,
                "disable_notifier": True,
                "state": Watchman.STATE.get("success"),
            },
            False: {
                "success": False,
                "disable_notifier": False,
                "state": Watchman.STATE.get("failure"),
            },
            None: {
                "success": None,
                "disable_notifier": False,
                "state": Watchman.STATE.get("exception"),
            }
        }
        results = []
        msg = ''
        failure = False
        exception = False

        for summary_item in summary:
            check_result = summary_item.get("success")
            if check_result is False:
                failure = True
            if check_result is None:
                exception = True
            msg += summary_item.get("subject") + "\n" + summary_item.get("details") + "\n\n"
            subject = summary_item.get("subject")
            details = summary_item.get("details")
            target = summary_item.get("target")
            short_message = summary_item.get("short_message")
            parameters = state_chart.get(check_result)
            results.append(Result(
                **parameters,
                subject=subject,
                watchman_name=self.watchman_name,
                target=target,
                details=details,
                short_message=short_message))

        # this is used to create a generic result for email notification
        if failure and exception:
            short_message = MESSAGES.get("exception_message") + MESSAGES.get("failure_message")
            subject = MESSAGES.get("generic_fail_exception_subject")
            parameters = state_chart.get(None)
        elif failure:
            short_message = MESSAGES.get("failure_message")
            subject = MESSAGES.get("generic_failure_subject")
            parameters = state_chart.get(False)
        elif exception:
            short_message = MESSAGES.get("exception_message")
            subject = MESSAGES.get("generic_exception_subject")
            parameters = state_chart.get(None)
        else:
            short_message = MESSAGES.get("success_message").format('All targets')
            subject = MESSAGES.get("generic_suceess_subject")
            parameters = state_chart.get(True)
        results.append(Result(
            **parameters,
            subject=subject,
            watchman_name=self.watchman_name,
            target='Generic S3',
            details=msg,
            short_message=short_message))

        return results

    def _generate_key(self, prefix_format, event, offset=1):
        """
        Method to generate prefix key for each target based on the event type.
        @return: Prefix
        """
        try:
            arg_dict = {'Hourly': 'hours', 'Daily': 'days'}
            check_time = _datetime.datetime.now(pytz.utc) - _datetime.timedelta(**{arg_dict[event]: offset})
            prefix = check_time.strftime(prefix_format)
            return prefix, None
        except Exception as ex:
            self.logger.error("ERROR Generating Key!")
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception("{}: {}".format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            return None, tb

    def _generate_contents(self, item):
        """
        Method to generate contents for the given s3 path configuration.
        @return: The files contents, files count, generated file prefix, file path and possible traceback.
        """
        try:
            if item.get('offset'):
                prefix_generate, tb = self._generate_key(item['prefix'], self.event, item['offset'])
            else:
                prefix_generate, tb = self._generate_key(item['prefix'], self.event)
            full_path = 's3://' + item['bucket_name'] + '/' + prefix_generate
            self.logger.info("Checking s3 path: {}".format(full_path))
            contents = _s3.generate_pages(prefix_generate, **{'bucket': item['bucket_name']})
            contents = list(contents)
            count = len(contents)
            self.logger.info("Checking {} files.".format(count))
            return contents, count, prefix_generate, full_path, None
        except Exception as ex:
            self.logger.error("ERROR Generating Contents!")
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception("{}: {}".format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            return None, None, None, None, tb

    def _check_single_file_existence(self, item, s3_key):
        """
        Method to check if a single file exists.
        @return: True if the file exists and False otherwise with a file path.
        """
        try:
            found_file = _s3.validate_file_on_s3(bucket_name=item['bucket_name'], key=s3_key)
            return found_file, None
        except Exception as ex:
            self.logger.error("ERROR Checking Single File Existence!")
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception("{}: {}".format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            return None, tb

    def _check_most_recent_file(self, contents, check_most_recent_file):
        """
        Method to subset the contents to the most recent N files that need to be checked.
        @return: The most recent contents.
        """

        def get_last_modified(key): return int(key['LastModified'].strftime('%s'))

        most_recent_contents = [obj for obj in sorted(contents, key=get_last_modified, reverse=True)]
        contents = most_recent_contents[0:check_most_recent_file]
        return contents

    def _check_file_prefix_suffix(self, contents, suffix, prefix):
        """
        Method to check each files in the paginator for their prefix and suffix.
        @return: True if at least one file key is matches and a possible traceback.
        """
        try:
            prefix_suffix_match = True

            for file in contents:
                if not file or prefix not in file['Key'] or not file.get('Key').endswith(suffix):
                    prefix_suffix_match = False
            return prefix_suffix_match, None
        except Exception as ex:
            self.logger.error("ERROR Checking File Prefix and Suffix!")
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception("{}: {}".format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            return None, tb

    def _check_file_empty(self, contents):
        """
        Method to check each file for size larger than 0/emptiness.
        @return: True if one file is empty and a list of empty files' keys and False otherwise.
        """
        try:
            empty_file_list = []
            at_least_one_file_empty = False

            for file in contents:
                if not (file.get('Size') > 0):
                    at_least_one_file_empty = True
                    empty_file_list.append(file['Key'])
            return at_least_one_file_empty, empty_file_list, None
        except Exception as ex:
            self.logger.error("ERROR Checking For Empty File!")
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception("{}: {}".format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            return None, None, tb

    def _compare_total_file_size_to_threshold(self, contents, size_threshold):
        """
        Method to check the total size of all files.
        @return: True if the total size is less than the expected size and False otherwise along with the total_size
        """
        try:
            total_size = 0
            for item in contents:
                total_size += item.get('Size')
            total_size = total_size / 1000  # This is to convert B to KB
            is_size_less_than_threshold = total_size < size_threshold
            return is_size_less_than_threshold, total_size, None
        except Exception as ex:
            self.logger.error("ERROR Comparing Total File Size To Threshold!")
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception("{}: {}".format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            return None, None, tb

    def _create_generic_result(self, failure_in_parameters, exception_in_parameters, details):
        """
        Method to create the generic result object.
        :param failure_in_parameters: Bool that indicates whether a failure was encountered in any of the target checks.
        :param exception_in_parameters: Bool that indicates whether an exception was encountered in any of the target
               checks.
        :param details: String containg th details for all of the target checks performed.
        :return: Generic Result object.
        """
        if failure_in_parameters and exception_in_parameters:
            disable_notifier = False
            short_message = MESSAGES.get("failure_exception_message")
            state = Watchman.STATE.get("failure")
            subject = MESSAGES.get("generic_fail_exception_subject")
            success = False

        elif failure_in_parameters:
            disable_notifier = False
            short_message = MESSAGES.get("failure_message")
            state = Watchman.STATE.get("failure")
            subject = MESSAGES.get("generic_failure_subject")
            success = False

        elif exception_in_parameters:
            disable_notifier = False
            short_message = MESSAGES.get("exception_message")
            state = Watchman.STATE.get("exception")
            subject = MESSAGES.get("generic_exception_subject")
            success = False

        else:
            disable_notifier = True
            short_message = MESSAGES.get("success_message").format('All targets')
            state = Watchman.STATE.get("success")
            subject = MESSAGES.get("generic_success_subject")
            success = True

        return (Result(
            details=details,
            disable_notifier=disable_notifier,
            short_message=short_message,
            state=state,
            subject=subject,
            success=success,
            target='Generic S3',
            watchman_name=self.watchman_name,
        ))
