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
        results = self._create_results(summary_parameters)

        return results

    def _check_invalid_event(self):
        """
        Method to check that the event passed in from the Lambda has the correct parameters. If there is no "Type"
        parameter passed in, or the "Type" does not equal any of the allowed event types, then the
        event parameter is invalid.
        @return: True if the event parameter passed from the Lambda is invalid, false if the event parameter is valid.
        """
        if not self.event or self.event not in ALL_EVENT_TYPES:
            self.logger.info(MESSAGES.get("failure_event_check").format(self.event))
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
            details=MESSAGES.get("exception_config_load_failure_details").format(CONFIG_NAME, tb),
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
            failure_strings.append(MESSAGES.get('failure_invalid_s3_key').format(s3_key))
            return exception_strings, failure_strings

        # Checking single file size:
        if item.get("check_total_size_kb"):
            valid_file_size, tb = self._check_single_file_size(item, s3_key)
            if tb:
                exception_strings.append(MESSAGES.get("exception_string_format").format(item, tb))
            if not valid_file_size:
                failure_strings.append(MESSAGES.get('failure_single_file_size').format(item.get("check_total_size_kb"),
                                                                                       full_path))
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
        contents_dict, tb = self._generate_contents(item)

        if tb:
            exception_strings.append(MESSAGES.get("exception_string_format").format(item, tb))
            return exception_strings, failure_strings

        contents = contents_dict.get("contents")
        count = contents_dict.get("count")
        s3_prefix = contents_dict.get("s3_prefix")

        # If there are no files (count == 0), then the rest of the checks cannot be performed
        if not count:
            failure_strings.append(MESSAGES.get('failure_invalid_s3_key').format(s3_prefix))
            return exception_strings, failure_strings

        # Check the suffix of all files:
        if item.get("suffix"):
            incorrect_suffix_files, tb = self._check_file_suffix(contents, item.get("suffix"))
            if tb:
                exception_strings.append(MESSAGES.get("exception_string_format").format(item, tb))
            if incorrect_suffix_files:
                failure_strings.append(MESSAGES.get('failure_invalid_suffix').format(item.get('suffix'),
                                                                                     incorrect_suffix_files))

        # Check for empty files and total file size:
        file_size_failure_strings, tb = self._check_multiple_files_size(contents, item, s3_prefix)
        if tb:
            exception_strings.append(MESSAGES.get("exception_string_format").format(item, tb))
        
        if file_size_failure_strings:
            failure_strings.append(file_size_failure_strings)

        # Check if the aggregate file count meets standards:
        if item.get('check_total_object'):
            if count < item.get('check_total_object'):
                failure_strings.append(MESSAGES.get('failure_total_objects').format(s3_prefix, count,
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

        failure_string = MESSAGES.get("failure_details").format("\n\n".join(target_check_results.
                                                                            get("failure_strings")))
        if target_check_results.get("exception_strings"):
            exception_string = "\n\n".join(target_check_results.get("exception_strings"))
            failure_string += "\n\n{}\n\n{}".format(const.MESSAGE_SEPARATOR,
                                                    MESSAGES.get('exception_details').format(exception_string))
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
                result_parameters["short_message"] = MESSAGES.get("success_message")
                result_parameters["subject"] = MESSAGES.get("success_subject").format(target_name)

            elif processed_targets[target_name].get('success') is None:
                result_parameters["short_message"] = MESSAGES.get("exception_message")
                result_parameters["subject"] = MESSAGES.get("exception_subject").format(target_name)

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

    def _create_results(self, summary_parameters):
        """
        Method to create all of the result objects based on the summary parameters. These result objects are used for
        sending SNS alerts when the target's state is "failure" or "exception".
        :param summary_parameters: List of summary_parameter dictionaries. Each dictionary will be used to create
                                   a Result object.
        :return: List of Result objects for each target that was checked.
        """
        results = []
        generic_result_details = ''
        failure_in_parameters = False
        exception_in_parameters = False

        for summary_parameters_dict in summary_parameters:
            check_result = summary_parameters_dict.get("success")

            if check_result is False:
                failure_in_parameters = True
            if check_result is None:
                exception_in_parameters = True

            # Building the generic result's details, only include exceptions and failures:
            if not check_result:
                generic_result_details += "{}\n\n{}\n\n{}\n\n".format(summary_parameters_dict.get("subject"),
                                                                      summary_parameters_dict.get("details"),
                                                                      const.MESSAGE_SEPARATOR)

            results.append(Result(
                details=summary_parameters_dict.get("details"),
                disable_notifier=summary_parameters_dict.get("disable_notifier"),
                short_message=summary_parameters_dict.get("short_message"),
                state=summary_parameters_dict.get("state"),
                subject=summary_parameters_dict.get("subject"),
                success=check_result,
                target=summary_parameters_dict.get("target"),
                watchman_name=self.watchman_name,
            ))

        results.append(self._create_generic_result(failure_in_parameters, exception_in_parameters,
                                                   generic_result_details))

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
        @return: The files contents, files count, s3 prefix, and possible traceback.
        """
        contents_dict = {
            "contents": None,
            "count": None,
            "s3_prefix": None
        }

        try:
            time_offset = item.get("offset", 1)
            generated_prefix, tb = self._generate_key(item['prefix'], self.event, time_offset)

            if tb:
                return contents_dict, tb

            s3_prefix = 's3://' + item['bucket_name'] + '/' + generated_prefix
            contents = list(_s3.generate_pages(generated_prefix, **{'bucket': item['bucket_name']}))

            # Removing whitelisted files from contents:
            if item.get("whitelist"):
                self._remove_whitelisted_files_from_contents(item.get("whitelist"), contents)

            count = len(contents)

            self.logger.info("Checking s3 path: {}".format(s3_prefix))
            self.logger.info("Checking {} files.".format(count))

            contents_dict.update({"contents": contents, "count": count, "s3_prefix": s3_prefix})
            return contents_dict, None
        except Exception as ex:
            self.logger.error("ERROR Generating Contents!")
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception("{}: {}".format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            return contents_dict, tb

    def _remove_whitelisted_files_from_contents(self, whitelist, contents):
        """
        Method to remove the whitelisted files from the contents.
        :param whitelist: A list of file names that should be removed from the contents.
        :param contents: List of all the files to be checked.
        :return: Updated list of contents with whitelisted files removed.
        """
        for file in list(contents):
            if file.get("Key").split('/')[-1] in whitelist:
                contents.remove(file)

        return contents

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

    def _check_file_suffix(self, contents, suffix):
        """
        This method verifies that each file in the contents has the expected suffix, such as ".parquet".
        :param contents: A list of the generated contents for the item currently being checked.
        :param suffix: A string containing the suffix to check for in all files.
        :return: <String>, <String>
                 <String>: String containing all of the file(s) that did not have the correct suffix.
                 <String>: Traceback if an exception occurred.
        """
        try:
            incorrect_suffix_files = ""

            for file in contents:
                s3_key = file.get("Key")

                if not s3_key or not s3_key.endswith(suffix):
                    incorrect_suffix_files += s3_key

            return incorrect_suffix_files, None
        except Exception as ex:
            self.logger.error("ERROR Checking File Suffix!")
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception("{}: {}".format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            return None, tb

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
            subject = MESSAGES.get("generic_failure_exception_subject")
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
            short_message = MESSAGES.get("success_message")
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

    def _check_multiple_files_size(self, contents, item, s3_prefix):
        """
        Method to perform the empty file check and/or the total file size check for multiple files.
        :param contents: The contents containing all of the files for the current item being checked.
        :param item: The current item being checked.
        :param s3_prefix: The formatted S3 prefix of the current item being checked. This is required to make the
                          message if the total file size requirement is not met.
        :return: <list> <string>
                 <list>: List of all strings for all of the possible failures encountered during the checks.
                 <string>: Traceback if an exception was encountered, else None.
        """
        empty_file_list = []
        failure_string = ""
        total_size = 0

        try:
            for file in contents:
                file_size = file.get('Size')
                total_size += file_size

                if file_size == 0:
                    empty_file_list.append(file['Key'])

            if empty_file_list:
                empty_file_string = ""
                for empty_file in empty_file_list:
                    empty_file_string += "{}\n\n".format(MESSAGES.get('failure_file_empty').format(empty_file))

                failure_string += empty_file_string

            if item.get('check_total_size_kb'):
                kb_size_threshold = item.get('check_total_size_kb')
                kb_total_size = total_size / 1000

                if kb_total_size < kb_size_threshold:
                    failure_string += (MESSAGES.get('failure_multiple_file_size').format(
                        s3_prefix, total_size, kb_size_threshold))

            return failure_string, None
        except Exception as ex:
            self.logger.error("ERROR Checking Multiple Files Size!")
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception("{}: {}".format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            return None, tb
