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
S3_TARGETS_FILE = settings('rorschach.yaml_file')
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

        self.event = event.get("Type")

    def monitor(self):
        """
        Monitors the s3 targets.
        @return: <Result> List of Result objects
        """
        if self._check_invalid_event():
            return self._create_invalid_event_results()

        s3_targets = self._load_config(S3_TARGETS_FILE)
        if None in s3_targets:
            return self._create_config_not_load_results(s3_targets)

        check_results = self._process_checking(s3_targets)
        summary = self._create_summary(check_results)
        results = self._create_result(summary)
        return results

    def _check_invalid_event(self):
        """
        Method to check that the event passed in from the Lambda has the correct parameters. If there is no "Type"
        parameter passed in, or the "Type" does not equal any of the expected values ("Hourly", "Daily"), then the
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
        @return: One return object for the email SNS topic.
        """
        return [Result(
            disable_notifier=False,
            state=Watchman.STATE.get("exception"),
            success=False,
            subject=MESSAGES.get("exception_invalid_event_subject"),
            source=self.source,
            target="Generic S3",
            details=MESSAGES.get("exception_invalid_event_details"),
            snapshot={},
            message=MESSAGES.get("exception_message"),
        )]

    def _load_config(self, path):
        """
        Method to load the .yaml config file that contains configuration details of each s3 targets.
        @return: json object if the file can be successfully loaded, else None
        """
        try:
            with open(path) as f:
                s3_targets = yaml.load(f, Loader=yaml.FullLoader)
            s3_targets = s3_targets.get(self.event)
            return s3_targets
        except Exception as ex:
            self.logger.error("ERROR Processing Data!\n")
            self.logger.exception('{}: {}'.format(type(ex).__name__, ex))
            return None, ex

    def _create_config_not_load_results(self, s3_target):
        """
        Method to create the results for checking if the config file is successfully loaded.
        @return: One result object for the email SNS topic.
        """
        return [Result(
            disable_notifier=False,
            state=Watchman.STATE.get("exception"),
            success=False,
            subject=MESSAGES.get("exception_config_not_load_subject"),
            source=self.source,
            target="Generic S3",
            details=MESSAGES.get("exception_config_not_load_details").format('s3_config.yaml', s3_target[1]),
            snapshot={},
            message=MESSAGES.get("exception_message"),
        )]

    def _process_checking(self, s3_targets):
        """
        This method will conduct various checks for each S3 item under each target. The specific checks for each
        item is determined from the config data. It is possible for there to be many targets
        and each with multiple S3 items.
        @return: A dict containing metadata about each check for all items and all targets.
        @example: example_process_results = {
            'target1': [],
            'target2': [
                {'object_key_not_match': (True, 1)},
                {'at_least_one_file_empty': (True, ['some/path/to/something.parquet'])},
                {'file_size_too_less': ('s3://bucket/some/path/to/', 0.2, 0.3)},
                {'count_object_too_less': ('s3://bucket/some/path/to/', 2, 3)}],
            'target3': [ {'no_file_found_s3': 'some/path/to/something.zip'}]}
        """
        process_result_dict = {}
        # This goes through each target
        for target in s3_targets:
            self.logger.info("Checking target: {}".format(target))
            item_result_list = []

            # this is to ensure when multiple check items for one target
            for item in target['items']:
                # This is to validate the s3 bucket for each item
                validate_bucket = _s3.check_bucket(item['bucket_name'])
                if not validate_bucket['okay']:
                    item_result_list.append({'no_file_found_s3': "s3://" + item['bucket_name']})
                    continue

                # This is to validate the existence of an object when only one file needed to be checked
                if item.get('full_path'):
                    generate_full_path = self._generate_key(item['full_path'], self.event)
                    found_file = _s3.validate_file_on_s3(bucket_name=item['bucket_name'], key=generate_full_path)
                    if not found_file:
                        item_result_list.append({'no_file_found_s3': generate_full_path})
                    continue

                # This is to check multiple files when multiple files needed to be checked
                prefix_generate = self._generate_key(item['prefix'], self.event)
                full_path = 's3://' + item['bucket_name'] + '/' + prefix_generate
                self.logger.info("Checking s3 path: {}".format(full_path))
                contents = _s3.generate_pages(prefix_generate, **{'bucket': item['bucket_name']})
                contents = list(contents)
                count = len(contents)
                if count == 0:
                    item_result_list.append({'no_file_found_s3': full_path})
                    continue

                object_key_not_match = self._check_file_prefix_suffix(contents,
                                                                      suffix=item['suffix'],
                                                                      prefix=prefix_generate)
                self.logger.info("Searched through {} files.".format(count))
                if object_key_not_match:
                    item_result_list.append({'object_key_not_match': (object_key_not_match, count)})
                    continue

                at_least_one_file_empty, empty_file_list = self._check_file_empty(contents)
                if at_least_one_file_empty:
                    item_result_list.append({'at_least_one_file_empty': (at_least_one_file_empty, empty_file_list)})

                if item.get('check_total_size_kb'):
                    file_size_too_less, total_size = self._check_file_size_too_less(contents,
                                                                                    item['check_total_size_kb'])
                    if file_size_too_less:
                        item_result_list.append(
                            {'file_size_too_less': (full_path, total_size, item['check_total_size_kb'])})

                if item.get('check_total_object'):
                    if count < item['check_total_object']:
                        item_result_list.append(
                            {'count_object_too_less': (full_path, count, item['check_total_object'])})

            process_result_dict.update({target['target_name']: item_result_list})
        return process_result_dict

    def _create_summary(self, process_result_dict):
        """
        Method to create a summary object for all s3 targets with details messages based on the check results summary.
        @return: A list of dictionaries where each dict is a summary of the checking results of each target.
        """
        summary = []
        for target_name in process_result_dict.keys():
            try:
                if process_result_dict[target_name] == []:
                    summary_details = {
                        "success": True,
                        "subject": MESSAGES.get("success_subject").format(target_name),
                        "details": MESSAGES.get("success_details").format(target_name),
                        "message": MESSAGES.get("success_message").format(target_name),
                        "target": target_name
                    }
                    summary.append(summary_details)
                elif process_result_dict[target_name] != []:
                    msg = ""
                    for fail_items in process_result_dict[target_name]:
                        if 'no_file_found_s3' in fail_items.keys():
                            msg += MESSAGES.get('failure_no_file_found_s3').format(fail_items['no_file_found_s3'])
                        if 'object_key_not_match' in fail_items.keys():
                            msg += MESSAGES.get('failure_object_key_not_match')
                        if 'at_least_one_file_empty' in fail_items.keys():
                            for empty_file in fail_items['at_least_one_file_empty']:
                                msg += MESSAGES.get('failure_file_empty').format(empty_file)
                        if 'file_size_too_less' in fail_items.keys():
                            results_size = fail_items['file_size_too_less']
                            msg += MESSAGES.get('failure_size_too_less').format(results_size[0], results_size[1],
                                                                                results_size[2])
                        if 'count_object_too_less' in fail_items.keys():
                            results_count = fail_items['count_object_too_less']
                            msg += MESSAGES.get('failure_count_too_less').format(results_count[0], results_count[1],
                                                                                 results_count[2])

                    summary_details = {
                        "message": MESSAGES.get("failure_message").format(target_name),
                        "success": False,
                        "subject": MESSAGES.get("failure_subject").format(target_name),
                        "details": msg,
                        "target": target_name
                    }
                    summary.append(summary_details)

            except Exception as ex:
                msg = "An error occurred while checking the target at due to the following:" \
                      " {}: {}".format(type(ex).__name__, ex)
                summary_details = {
                    "message": MESSAGES.get("exception_message"),
                    "success": None,
                    "subject": MESSAGES.get("exception_subject"),
                    "details": msg,
                    "target": target_name
                }
                summary.append(summary_details)
        return summary

    def _process_checking(self, s3_targets):
        """
        This method will conduct various checks for each S3 item under each target. The specific checks for each
        item is determined from the config data. It is possible for there to be many targets
        and each with multiple S3 items.
        @return: A dict containing metadata about each check for all items and all targets.
        @example: example_process_results = {
            'target1': [],
            'target2': [
                {'object_key_not_match': (True, 1)},
                {'at_least_one_file_empty': (True, ['some/path/to/something.parquet'])},
                {'file_size_too_less': ('s3://bucket/some/path/to/', 0.2, 0.3)},
                {'count_object_too_less': ('s3://bucket/some/path/to/', 2, 3)}],
            'target3': [ {'no_file_found_s3': 'some/path/to/something.zip'}]}
        """
        process_result_dict = {}
        # This goes through each target
        for target in s3_targets:
            self.logger.info("Checking target: {}".format(target))
            item_result_list = []

            # this is to ensure when multiple check items for one target
            for item in target['items']:
                # This is to validate the s3 bucket for each item
                validate_bucket = _s3.check_bucket(item['bucket_name'])
                if not validate_bucket['okay']:
                    item_result_list.append({'no_file_found_s3': "s3://" + item['bucket_name']})
                    continue

                # This is to validate the existence of an object when only one file needed to be checked
                if item.get('full_path'):
                    generate_full_path = self._generate_key(item['full_path'], self.event)
                    found_file = _s3.validate_file_on_s3(bucket_name=item['bucket_name'], key=generate_full_path)
                    if not found_file:
                        item_result_list.append({'no_file_found_s3': generate_full_path})
                    continue

                # This is to check multiple files when multiple files needed to be checked
                prefix_generate = self._generate_key(item['prefix'], self.event)
                full_path = 's3://' + item['bucket_name'] + '/' + prefix_generate
                self.logger.info("Checking s3 path: {}".format(full_path))
                contents = _s3.generate_pages(prefix_generate, **{'bucket': item['bucket_name']})
                contents = list(contents)
                count = len(contents)
                if count == 0:
                    item_result_list.append({'no_file_found_s3': full_path})
                    continue

                object_key_not_match = self._check_file_prefix_suffix(contents,
                                                                      suffix=item['suffix'],
                                                                      prefix=prefix_generate)
                self.logger.info("Searched through {} files.".format(count))
                if object_key_not_match:
                    item_result_list.append({'object_key_not_match': (object_key_not_match, count)})
                    continue

                at_least_one_file_empty, empty_file_list = self._check_file_empty(contents)
                if at_least_one_file_empty:
                    item_result_list.append({'at_least_one_file_empty': (at_least_one_file_empty, empty_file_list)})

                if item.get('check_total_size_kb'):
                    file_size_too_less, total_size = self._check_file_size_too_less(contents,
                                                                                    item['check_total_size_kb'])
                    if file_size_too_less:
                        item_result_list.append(
                            {'file_size_too_less': (full_path, total_size, item['check_total_size_kb'])})

                if item.get('check_total_object'):
                    if count < item['check_total_object']:
                        item_result_list.append(
                            {'count_object_too_less': (full_path, count, item['check_total_object'])})

            process_result_dict.update({target['target_name']: item_result_list})
        return process_result_dict

    def _create_summary(self, process_result_dict):
        """
        Method to create a summary object for all s3 targets with details messages based on the check results summary.
        @return: A list of dictionaries where each dict is a summary of the checking results of each target.
        """
        summary = []
        for target_name in process_result_dict.keys():
            try:
                if process_result_dict[target_name] == []:
                    summary_details = {
                        "success": True,
                        "subject": MESSAGES.get("success_subject").format(target_name),
                        "details": MESSAGES.get("success_details").format(target_name),
                        "message": MESSAGES.get("success_message").format(target_name),
                        "target": target_name
                    }
                    summary.append(summary_details)
                elif process_result_dict[target_name] != []:
                    msg = ""
                    for fail_items in process_result_dict[target_name]:
                        if 'no_file_found_s3' in fail_items.keys():
                            msg += MESSAGES.get('failure_no_file_found_s3').format(fail_items['no_file_found_s3'])
                        if 'object_key_not_match' in fail_items.keys():
                            msg += MESSAGES.get('failure_object_key_not_match')
                        if 'at_least_one_file_empty' in fail_items.keys():
                            for empty_file in fail_items['at_least_one_file_empty']:
                                msg += MESSAGES.get('failure_file_empty').format(empty_file)
                        if 'file_size_too_less' in fail_items.keys():
                            results_size = fail_items['file_size_too_less']
                            msg += MESSAGES.get('failure_size_too_less').format(results_size[0], results_size[1],
                                                                                results_size[2])
                        if 'count_object_too_less' in fail_items.keys():
                            results_count = fail_items['count_object_too_less']
                            msg += MESSAGES.get('failure_count_too_less').format(results_count[0], results_count[1],
                                                                                 results_count[2])

                    summary_details = {
                        "message": MESSAGES.get("failure_message").format(target_name),
                        "success": False,
                        "subject": MESSAGES.get("failure_subject").format(target_name),
                        "details": msg,
                        "target": target_name
                    }
                    summary.append(summary_details)

            except Exception as ex:
                msg = "An error occurred while checking the target at due to the following:" \
                      " {}: {}".format(type(ex).__name__, ex)
                summary_details = {
                    "message": MESSAGES.get("exception_message"),
                    "success": None,
                    "subject": MESSAGES.get("exception_subject"),
                    "details": msg,
                    "target": target_name
                }
                summary.append(summary_details)
        return summary

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

        """
        """


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
