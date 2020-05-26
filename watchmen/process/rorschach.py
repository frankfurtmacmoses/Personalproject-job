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
        summary = self._create_summary(check_results)
        results = self._create_result(summary)

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
            source=self.source,
            target="Generic S3",
            details=MESSAGES.get("exception_invalid_event_details"),
            snapshot={},
            message=MESSAGES.get("exception_message"),
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
            subject=MESSAGES.get("exception_config_not_load_subject"),
            source=self.source,
            target="Generic S3",
            details=MESSAGES.get("exception_config_not_load_details").format(tb),
            snapshot={},
            message=MESSAGES.get("exception_message"),
        )]

    def _process_checking(self, s3_targets):
        """
        Method to conduct various checks for each S3 item under each target. The specific checks for each
        item is determined from the config data. It is possible for there to be many targets and each
        with multiple S3 items.
        @return: A dict containing metadata about the failed checks and items for all items and all targets.
        @example return: example_processed_targets =
        {
            'target1': {
                'success': True,
                'failed_checks': [],
            },
            'target2': {
                'success': False,
                'failed_checks': [
                    (item1 metdata dict, check results for item 1 metadata dict),
                    (item5 metdata dict, check results for item 5 metadata dict),
                ],
            }
            'target3': {
                'success': None,
                'failed_checks': [
                (item4 metadata dict, check results for item 4 metadata)
            ]
        }

        The item metadata dict will be the exact same as the config data for that item.
        The check result metadata dict can look like the following:
        {
            'bucket_not_found': s3/bucket
            'prefix_suffix_not_match': (prefix, suffix)
            'exception': traceback
        }

        """
        processed_targets = {}

        # This goes through each target
        for target in s3_targets:
            items_failed = []
            all_checks_are_exceptions = True

            # This checks each item and the various check attributes it has
            for item in target['items']:
                failed_check_items = {}
                exception_list = []

                # Validate the s3 bucket for each item
                bucket_name = item.get('bucket_name')
                # The check bucket will need refactoring because there's no way to differentiate exception from failure
                is_valid_bucket = _s3.check_bucket(bucket_name)  # {'okay': True, 'err': None}
                # An error occurred trying to find the bucket
                if is_valid_bucket.get('err'):
                    failed_check_items.update({'exception': is_valid_bucket['err']})
                    items_failed.append((item, failed_check_items))
                    continue
                # Bucket was not found
                if not is_valid_bucket.get('okay'):
                    failed_check_items.update({'bucket_not_found': 's3://{}'.format(bucket_name)})
                    items_failed.append((item, failed_check_items))
                    all_checks_are_exceptions = False
                    continue

                # Check for file existence
                # If an item has the attribute 'full_path', this indicates that we are only checking one file,
                # so we will only need to do an existence check at the moment. Adding file size checks for single
                # files will be added later.
                if item.get('full_path'):
                    found_file, full_path_with_bucket, tb = self._check_single_file_existence(item)
                    if tb:
                        failed_check_items.update({'exception': tb})
                        items_failed.append((item, failed_check_items))
                        continue

                    if not found_file:
                        failed_check_items.update({'no_file_found_s3': full_path_with_bucket})
                        items_failed.append((item, failed_check_items))
                        all_checks_are_exceptions = False
                        continue

                    continue

                # This is to check multiple files existence since we know it doesn't have a 'full_path' attribute
                contents, count, prefix_generate, full_path, tb = self._generate_contents(item)
                if tb:
                    failed_check_items.update({'exception': tb})
                    items_failed.append((item, failed_check_items))
                    continue

                if not count:
                    failed_check_items.update({'no_file_found_s3': full_path})
                    items_failed.append((item, failed_check_items))
                    all_checks_are_exceptions = False
                    continue

                # At this point, we know that the file exists, so we can do the other checks on it.

                # Check the most recent N files, and, if provided, use a specified value from config file
                # This will replace our contents to a specified range instead of everything in the path.
                if item.get('check_most_recent_file'):
                    contents = self._check_most_recent_file(contents, item.get('check_most_recent_file'))

                # Check every file in contents to ensure the key prefix and suffix match
                prefix_suffix_match, tb = self._check_file_prefix_suffix(contents, item.get('suffix'), prefix_generate)
                if tb:
                    exception_list.append(tb)
                if prefix_suffix_match is False:
                    failed_check_items.update({'prefix_suffix_not_match': (item.get('prefix'), item.get('suffix'))})
                    all_checks_are_exceptions = False

                # Check each individual file in contents to ensure all files have a size greater than 0
                at_least_one_file_empty, empty_file_list, tb = self._check_file_empty(contents)
                if tb:
                    exception_list.append(tb)
                if at_least_one_file_empty:
                    failed_check_items.update({'at_least_one_file_empty': (at_least_one_file_empty, empty_file_list)})
                    all_checks_are_exceptions = False

                # Check if aggregate file size is greater than 0 or the minimum size specified in the config file
                if item.get('check_total_size_kb'):
                    is_total_size_less_than_threshold, total_size, tb = self._compare_total_file_size_to_threshold(
                        contents, item.get('check_total_size_kb'))
                    if tb:
                        exception_list.append(tb)
                    if is_total_size_less_than_threshold:
                        failed_check_items.update(
                            {'total_file_size_below_threshold': (full_path, total_size, item.get('check_total_size_kb'))
                             })
                        all_checks_are_exceptions = False

                # Check if the aggregate file count is greater than 0 or the minimum size specified in the config file
                if item.get('check_total_object'):
                    if count < item.get('check_total_object'):
                        failed_check_items.update(
                            {'count_object_too_less': (full_path, count, item['check_total_object'])})
                        all_checks_are_exceptions = False

                # Check for exceptions
                if exception_list:
                    failed_check_items.update({'exception': exception_list})
                # Check for any failures/exceptions
                if failed_check_items:
                    items_failed.append((item, failed_check_items))

            # Keep track of which targets passed, failed, and only had exceptions
            if items_failed:
                processed_targets.update(
                    {
                        target.get('target_name'):
                            {
                                'success': None if all_checks_are_exceptions else False,
                                'failed_checks': items_failed
                            }
                    })
            else:
                processed_targets.update(
                    {
                        target.get('target_name'):
                            {
                                'success': True,
                                'failed_checks': items_failed
                            }
                    })

        return processed_targets

    def _create_summary(self, processed_targets):
        """
        Method to create a summary object for all s3 targets with details messages based on the check results summary.
        @return: A list of dictionaries where each dict is a summary of the checking results of each target.
        """
        summary = []

        for target_name in processed_targets:
            # Create the successful summaries
            if processed_targets[target_name].get('success'):
                summary_details = {
                    "success": True,
                    "subject": MESSAGES.get("success_subject").format(target_name),
                    "details": MESSAGES.get("success_details").format(target_name),
                    "message": MESSAGES.get("success_message").format(target_name),
                    "target": target_name
                }
                summary.append(summary_details)

            # Create the exceptions only summaries
            if processed_targets[target_name].get('success') is None:
                exception_list = ""
                for item in processed_targets[target_name].get('failed_checks'):
                    exception_list += '{}{}: {}\n'.format(item[0].get('bucket_name'),
                                                          item[0].get('prefix'),
                                                          item[1].get('exception'))
                    summary_details = {
                        "message": MESSAGES.get("exception_message"),
                        "success": None,
                        "subject": MESSAGES.get("exception_checking_subject").format(target_name),
                        "details": MESSAGES.get('exception_details').format(exception_list),
                        "target": target_name
                    }
                    summary.append(summary_details)

            # Create failures and exceptions summaries
            if processed_targets[target_name].get('success') is not None and \
                    not processed_targets[target_name].get('success'):
                exception_list = ''
                failure_list = ''
                for item in processed_targets[target_name].get('failed_checks'):
                    item_data = item[0]
                    check_data = item[1]

                    # Check for the failures
                    if 'bucket_not_found' in check_data:
                        failure_list += MESSAGES.get('failure_bucket_not_found').format(item_data.get('bucket_name'))
                    if 'no_file_found_s3' in check_data:
                        failure_list += MESSAGES.get('failure_no_file_found_s3').format(item_data.get(
                            'full_path') if item_data.get('full_path') else item_data.get('prefix'))
                    if 'prefix_suffix_not_match' in check_data:
                        failure_list += MESSAGES.get('failure_prefix_suffix_not_match').format(item_data.get('prefix'),
                                                                                               item_data.get('suffix'))
                    if 'at_least_one_file_empty' in check_data:
                        empty_file_list = ''
                        for empty_file in check_data.get('at_least_one_file_empty')[1]:
                            empty_file_list += MESSAGES.get('failure_file_empty').format(empty_file)
                        failure_list += empty_file_list
                    if 'total_file_size_below_threshold' in check_data:
                        failure_list += MESSAGES.get('failure_total_file_size_below_threshold').format(
                            check_data.get('total_file_size_below_threshold')[0],
                            check_data.get('total_file_size_below_threshold')[1],
                            check_data.get('total_file_size_below_threshold')[2])
                    if 'count_object_too_less' in check_data:
                        failure_list += MESSAGES.get('failure_count_too_less').format(
                            check_data.get('count_object_too_less')[0],
                            check_data.get('count_object_too_less')[1],
                            check_data.get('count_object_too_less')[2])

                    # Check for exceptions
                    if 'exception' in check_data:
                        for ex in check_data.get('exception'):
                            exception_list += '{}/{}: {}\n'.format(item_data.get('bucket_name'),
                                                                   item_data.get('prefix'),
                                                                   ex)

                    # Create details string
                    msg = ''
                    if failure_list:
                        msg += (MESSAGES.get('failure_details').format(failure_list) + '\n\n')
                    if exception_list:
                        msg += MESSAGES.get('exception_details').format(exception_list)

                    summary_details = {
                        "message": MESSAGES.get("failure_message").format(target_name),
                        "success": False,
                        "subject": MESSAGES.get("failure_subject").format(target_name),
                        "details": msg,
                        "target": target_name
                    }
                    summary.append(summary_details)

        return summary

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
            message = summary_item.get("message")
            parameters = state_chart.get(check_result)
            results.append(Result(
                **parameters,
                subject=subject,
                source=self.source,
                target=target,
                details=details,
                message=message))

        # this is used to create a generic result for email notification
        if failure and exception:
            message = MESSAGES.get("exception_message") + MESSAGES.get("failure_message")
            subject = MESSAGES.get("generic_fail_exception_subject")
            parameters = state_chart.get(None)
        elif failure:
            message = MESSAGES.get("failure_message")
            subject = MESSAGES.get("generic_failure_subject")
            parameters = state_chart.get(False)
        elif exception:
            message = MESSAGES.get("exception_message")
            subject = MESSAGES.get("generic_exception_subject")
            parameters = state_chart.get(None)
        else:
            message = MESSAGES.get("success_message").format('All targets')
            subject = MESSAGES.get("generic_suceess_subject")
            parameters = state_chart.get(True)
        results.append(Result(
            **parameters,
            subject=subject,
            source=self.source,
            target='Generic S3',
            details=msg,
            message=message))

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
            tb = traceback.format_exc()
            self.logger.exception('{}: {}'.format(type(ex).__name__, ex))
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
            tb = traceback.format_exc()
            self.logger.exception('{}: {}'.format(type(ex).__name__, ex))
            return None, None, None, None, tb

    def _check_single_file_existence(self, item):
        """
        Method to check if a single file exists.
        @return: True if the file exists and False otherwise with a file path.
        """
        try:
            if item.get('offset'):
                generate_full_path, tb = self._generate_key(item['full_path'], self.event, item['offset'])
            else:
                generate_full_path, tb = self._generate_key(item['full_path'], self.event)
            found_file = _s3.validate_file_on_s3(bucket_name=item['bucket_name'], key=generate_full_path)
            return found_file, generate_full_path, None
        except Exception as ex:
            tb = traceback.format_exc()
            self.logger.exception('{}: {}'.format(type(ex).__name__, ex))
            return None, None, tb

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
            tb = traceback.format_exc()
            self.logger.exception('{}: {}'.format(type(ex).__name__, ex))
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
            tb = traceback.format_exc()
            self.logger.exception('{}: {}'.format(type(ex).__name__, ex))
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
            tb = traceback.format_exc()
            self.logger.exception('{}: {}'.format(type(ex).__name__, ex))
            return None, None, tb
