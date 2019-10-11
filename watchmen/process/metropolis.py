"""
Metropolis class for monitoring metrics and KPI change detection.
Created on 8.21.2019
@author: Jinchi Zhang
@email: jzhang@infoblox.com
"""
from datetime import datetime
import pytz
import traceback

from watchmen import const
from watchmen.common.watchman import Result
from watchmen.common.watchman import Watchman
from watchmen.config import settings
from watchmen.utils.csv import csv_string_to_dict
from watchmen.utils.s3 import get_csv_data

BUCKET_NAME = settings('metropolis.bucket_name')
DATA_FILE = settings('metropolis.data_file')
PATH_PREFIX = settings('metropolis.path_prefix')

ERROR = 'ERROR: '
EXCEPTION_MESSAGE = 'The {} process reached an exception trying to get ' + DATA_FILE + ' from s3' \
                    ' due to the following:\n\n{}\n\nPlease look at the logs for more insight.'
EXCEPTION_SUBJECT = 'Metropolis: Exception checking {}!'
FAILURE_MESSAGE = '{} process is down for {}!'
FAILURE_SUBJECT = 'Metropolis: OUTLIER DETECTED - {}!'
GENERIC_FAIL_AND_EXCEPTION_SUBJECT = 'Metropolis: FAILURE AND EXCEPTION checking process metrics'
GENERIC_EXCEPTION_SUBJECT = 'Metropolis: EXCEPTION checking process metrics'
GENERIC_FAIL_SUBJECT = 'Metropolis: FAILURE checking process metrics'
GENERIC_SUCCESS_SUBJECT = 'Metropolis: no outliers'
MIN_AND_MAX_MESSAGE = 'Minimum: {} || Maximum: {} || Actual Count: {}'
MIN_AND_MAX_ERROR_MESSAGE = ERROR + 'Minimum is larger than maximum.'
NOT_LOADED_MESSAGE = 'Failed to load {} due to the following:\n\n{}\n\nPlease look at the logs for more insight.'
NOT_LOADED_SUBJECT = 'Metropolis: ERROR loading data file!'
SUCCESS_MESSAGE = '{} process is up and running for {}!'
SUCCESS_SUBJECT = 'Metropolis: no outliers - {}!'

# Watchmen Profile
GENERIC_TARGET = 'Metrics and KPI'


class Metropolis(Watchman):
    """
    Metropolis class
    """

    # pylint: disable=unused-argument
    def __init__(self, event, context):
        super().__init__()

    def monitor(self) -> [Result]:
        """
        Monitors Metrics and KPI change detection.
        @return: <list> list of Results
        """
        dicts_list, tb = self._read_csv()
        if not dicts_list:
            result = self._create_not_loaded_result(tb)
            return [result]
        dicts_list_today = self._get_data_by_date(dicts_list, self._get_date_today())
        results = []
        generic_checks, generic_details = [], ''
        for attr_dict in dicts_list_today:
            threshold_check, check_tb = self._check_against_threshold_poc(attr_dict)
            generic_checks.append(threshold_check)
            threshold_msg = self._create_threshold_message(attr_dict)
            process_name, date = attr_dict.get("process"), attr_dict.get("date")
            details = self._create_details(
                process_name=process_name,
                date=date,
                threshold_check=threshold_check,
                threshold_message=threshold_msg,
                tb=check_tb
            )
            # append details in False or None checks to generic details
            if not threshold_check:
                generic_details = generic_details + details + '\n' + const.MESSAGE_SEPARATOR + '\n'
            parameters = self._create_summary_parameters(threshold_check, process_name)
            # notice: snapshot for Metropolis is same with the data dictionary at each row,
            # and target is process name at each row
            result = self._create_result(
                success=parameters.get("success"),
                disable_notifier=parameters.get("disable_notifier"),
                state=parameters.get("state"),
                subject=parameters.get("subject"),
                details=details,
                snapshot=attr_dict,
                target=process_name
            )
            results.append(result)
        results.append(self._create_generic_result(generic_checks, generic_details, dicts_list_today))
        return results

    def _check_against_threshold_poc(self, attr_dict):
        """
        Checks if count is in the threshold.
        @param attr_dict: <dict> dictionary that has keys: "process", "min", "max", "count"
        @return: <bool> <str>
        <bool> whether count is in the threshold
        <str> traceback
        """
        try:
            maximum, minimum, count = \
                float(attr_dict.get("max")), \
                float(attr_dict.get("min")), \
                float(attr_dict.get("count"))
            if maximum < minimum:
                return None, MIN_AND_MAX_ERROR_MESSAGE
            if minimum <= count <= maximum:
                return True, None
            return False, None
        except Exception as ex:
            self.logger.exception(traceback.extract_stack())
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception('{}: {}'.format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            return None, tb

    def _check_outlier(self, threshold_check, attr_dict):
        """
        Check if the process has an outlier,
        and check if outlier value is the same as our check against threshold value.
        @param threshold_check: <bool> result of checking threshold, None upon exception
        @param attr_dict: <dict> dictionary that has keys: "process", "min", "max", "count", "outlier"
        @return: <bool> <str>
        <bool> whether threshold check is same as outlier attribute in attribute dictionary
        <str> traceback
        """
        try:
            is_outlier = attr_dict["outlier"]
            return threshold_check == is_outlier, None
        except Exception as ex:
            self.logger.exception(traceback.extract_stack())
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception('{}: {}'.format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            return None, tb

    @staticmethod
    def _create_details(process_name, date, threshold_check: bool, threshold_message, tb):
        """
        Creates detailed message by process name check results or by traceback in the previous processes.
        @param process_name: process name for the row in csv
        @param date: date in the attributes
        @param threshold_check: <bool> result of checking threshold, None upon exception
        @param tb: <str> traceback
        @return: <str> details
        """
        if threshold_check is None:
            return EXCEPTION_MESSAGE.format(process_name, tb)
        if threshold_check is True:
            details_start = SUCCESS_MESSAGE.format(process_name, date)
        else:
            details_start = FAILURE_MESSAGE.format(process_name, date)
        details = details_start + '\n\n' + threshold_message
        return details

    def _create_generic_result(self, generic_checks, generic_details, generic_snapshot):
        """
        Create generic result that includes all the information.
        @param generic_checks: <list> list of all check results
        @param generic_details: <str> summarized details including all the information
        @param generic_snapshot: <list> list of dict that has attribute keys
        @return: <Result> Result object
        """
        has_outlier = True if False in generic_checks else False
        has_exception = True if None in generic_checks else False
        success = False if has_outlier or has_exception else True
        disable_notifier = success

        if has_outlier and has_exception:
            subject = GENERIC_FAIL_AND_EXCEPTION_SUBJECT
            state = Watchman.STATE.get("exception")
        elif has_outlier and not has_exception:
            subject = GENERIC_FAIL_SUBJECT
            state = Watchman.STATE.get("failure")
        elif not has_outlier and has_exception:
            subject = GENERIC_EXCEPTION_SUBJECT
            state = Watchman.STATE.get("exception")
        else:
            subject = GENERIC_SUCCESS_SUBJECT
            state = Watchman.STATE.get("success")
        result = self._create_result(
            success=success,
            disable_notifier=disable_notifier,
            state=state,
            subject=subject,
            details=generic_details,
            snapshot=generic_snapshot,
            target=GENERIC_TARGET
        )
        return result

    def _create_not_loaded_result(self, tb):
        """
        Creates results that contains details indicating that csv file is not loaded.
        @return: <Result> Result object
        """
        details = NOT_LOADED_MESSAGE.format(DATA_FILE, tb)
        result = self._create_result(
            success=False,
            disable_notifier=False,
            state=Watchman.STATE.get("exception"),
            subject=NOT_LOADED_SUBJECT,
            details=details,
            snapshot={},
            target=GENERIC_TARGET
        )
        return result

    @staticmethod
    def _create_summary_parameters(threshold_check: bool, process_name):
        """
        Creates a dicitonary that includes:
            success: whether the target is considered successful
            disable_notifier: whether we should disable the notifier
            state: state of result
            subject: subject for long notification
        @param threshold_check: <bool> result of checking threshold, None upon exception
        @param process_name: <str> process name
        @return: <dict> parameters for creating results
        """
        parameter_chart = {
            None: {
                "success": False,
                "disable_notifier": False,
                "state": Watchman.STATE.get("exception"),
                "subject": EXCEPTION_SUBJECT.format(process_name),
            },
            True: {
                "success": True,
                "disable_notifier": True,
                "state": Watchman.STATE.get("success"),
                "subject": SUCCESS_SUBJECT.format(process_name),
            },
            False: {
                "success": False,
                "disable_notifier": False,
                "state": Watchman.STATE.get("failure"),
                "subject": FAILURE_SUBJECT.format(process_name),
            },
        }
        parameters = parameter_chart.get(threshold_check)
        return parameters

    @staticmethod
    def _create_threshold_message(attr_dict):
        """
        Creates message that includes information of min, max, and count.
        @param attr_dict: <dict> dictionary that has keys: "process", "min", "max", "count"
        @return: <str> constructed message
        """
        maximum, minimum, count = attr_dict.get("max"), attr_dict.get("min"), attr_dict.get("count")
        return MIN_AND_MAX_MESSAGE.format(minimum, maximum, count)

    def _create_result(self, success, disable_notifier, state, subject, details, snapshot, target):
        """
        Create the result object
        @param success: <bool> whether the file was found, false upon exception, otherwise false
        @param state: <str> state of the monitor check
        @param subject: <str> subject for the notification
        @param details: <str> content for the notification
        @return: <Result> result based on the parameters
        """
        result = Result(
            success=success,
            disable_notifier=disable_notifier,
            state=state,
            subject=subject,
            source=self.source,
            snapshot=snapshot,
            target=target,
            details=details)
        return result

    @staticmethod
    def _get_data_by_date(dict_list: list, date: str):
        """
        Gets list of rows in data for certain date
        @param dict_list: <list> list of dictionary representing rows in data
        @param date: <str> date of the data, eg. 2019-03-27
        @return: <list> list of dictionary with the date
        """
        modified_list = []
        for row in dict_list:
            if row.get("date") == date:
                modified_list.append(row)
        return modified_list

    @staticmethod
    def _get_date_today():
        """
        Gets the today's date in NOTICE: PST
        @return: <str> today's date, eg. 2019-03-27
        """
        return datetime.now(pytz.timezone('US/Pacific')).strftime('%Y-%m-%d')

    # TODO when Laura determines how each process deals with zeros
    def _load_zeros_data(self):
        pass

    def _read_csv(self):
        """
        Reads csv file, None if fails.
        @return: <list> <str>
        <list> list of dictionaries indicating each row of the csv file
        <str> tracback
        """
        data_file = DATA_FILE
        if PATH_PREFIX:
            data_file = '{}{}'.format(PATH_PREFIX, data_file)
        try:
            csv_content_str = get_csv_data(key_name=data_file, bucket=BUCKET_NAME)
            data = csv_string_to_dict(csv_content_str)
            return data, None
        except Exception as ex:
            self.logger.exception(traceback.extract_stack())
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception('{}: {}'.format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            return None, tb
