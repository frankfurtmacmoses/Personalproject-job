"""
Metropolis class for monitoring metrics and KPI change detection.
Created on 8.21.2019
@author: Jinchi Zhang
@email: jzhang@infoblox.com

Refactored on 10.17.2019
@author: Michael Garcia
@email: garciam@infoblox.com
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

BUCKET_NAME = settings("metropolis.bucket_name", "cyber-intel")
DATA_FILE = settings("metropolis.data_file", "watchmenResults.csv")
PATH_PREFIX = settings("metropolis.path_prefix", "analytics/change_detection/prod/")

# MESSAGES
DETAILS_FORMAT = "{}\n\nMetric_type: {}\nMetric_description: {}\nMetric_value: {}\n{}\n"
EXCEPTION_DETAILS = "Process: {}, Source: {} reached an exception on {} trying to get " + DATA_FILE + " from s3" \
                    " due to the following:\n\n{}\n\nPlease look at the logs for more insight."
EXCEPTION_MESSAGE = "Metropolis failed due to an exception!"
EXCEPTION_SUBJECT = "Metropolis: EXCEPTION Checking Process: {}"
FAILURE_DETAILS = "Process: {}, Source: {} is down for {}!"
FAILURE_EXCEPTION_MESSAGE = "Failure and exception checking process metrics."
FAILURE_MESSAGE = "There were moving_mean values outside of the threshold!"
FAILURE_SUBJECT = "Metropolis: OUTLIER DETECTED! - Process: {}"
GENERIC = "Generic: "
GENERIC_EXCEPTION_SUBJECT = "Metropolis: EXCEPTION Checking Process Metrics"
GENERIC_FAIL_SUBJECT = "Metropolis: FAILURE Checking Process Metrics"
GENERIC_FAIL_AND_EXCEPTION_SUBJECT = "Metropolis: FAILURE AND EXCEPTION Checking Process Metrics"
GENERIC_SUCCESS_SUBJECT = "Metropolis: No Outliers!"
MIN_AND_MAX_MESSAGE = "Moving Mean: {} || Minimum: {} || Maximum: {}"
MIN_AND_MAX_ERROR_MESSAGE = "Error: Minimum is larger than maximum."
NOT_LOADED_DETAILS = "Failed to find rows with date of {} in {} due to the following:\n{}\n\nPlease look at the " \
                     "logs or check the CSV file for more insight."
NOT_LOADED_MESSAGE = "Failed to load data from the CSV file, please check logs."
NOT_LOADED_SUBJECT = "Metropolis: ERROR Loading Data File!"
PROCESS_NOT_IN_FILE = "{} process is missing from the CSV file."
SUCCESS_DETAILS = "Process: {}, Source: {} is up and running for {}!"
SUCCESS_MESSAGE = "All moving_mean values were inside the threshold!"
SUCCESS_SUBJECT = "Metropolis: No Outliers! - {}"

# TARGETS:
TARGETS = {
    "domain_counts": "Domain Counts Metrics",
    "slowdrip": "Slowdrip Metrics",
    "reaper": "Reaper Metrics",
}
GENERIC_TARGET = "Metrics and KPI"


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
        :return: <list> list of Result objects, one for each process type and one for the generic SNS topic "Metrics
                        and KPI". Total number of Result objects created should be the number of processes + 1.
        """
        results = []
        generic_checks, generic_details = [], ""
        # Keys are all of the possible processes(add/remove if necessary in future):
        sources_per_process = {
            "domain_counts": [],
            "slowdrip": [],
            "reaper": []
        }

        row_dicts_today, tb = self._create_row_dicts_today()
        if not row_dicts_today:
            result = self._create_not_loaded_result(tb)
            return [result]

        # Dictionary of {process}: {list of rows for that process}
        sources_per_process = self._fill_sources_per_process(sources_per_process, row_dicts_today)

        for process, sources in sources_per_process.items():
            # If there are no sources to check, continue to check next process.
            if not sources:
                self.logger.info(PROCESS_NOT_IN_FILE.format(process))
                continue
            result, generic_checks, generic_details = self._check_all_sources(sources, generic_checks, generic_details)
            results.append(result)

        results.append(self._create_generic_result(generic_checks, generic_details, row_dicts_today))
        return results

    def _check_against_threshold(self, row):
        """
        This method checks if the "moving_mean" is between the threshold. The threshold is described by "3UCL" as the
        maximum and "3LCL" as the minimum. (LCL = lower control limit, UCL = upper control limit)
        :param row: <dict> dictionary that has keys: "date", "process", "metric_type", "metric_value", "moving_mean",
                    "3LCL", "3UCL", "2LCL", "2UCL", "metric_description"
        :return: <bool> <str>
        <bool> whether moving_mean is in the threshold
        <str> traceback
        """
        try:
            maximum, minimum, moving_mean = \
                float(row.get("3UCL")), \
                float(row.get("3LCL")), \
                float(row.get("moving_mean"))
            if maximum < minimum:
                return None, MIN_AND_MAX_ERROR_MESSAGE
            if minimum <= moving_mean <= maximum:
                return True, None
            return False, None
        except Exception as ex:
            self.logger.exception(traceback.extract_stack())
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception("{}: {}".format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            return None, tb

    def _check_all_sources(self, sources, generic_checks, generic_details):
        """
        Method that checks if all rows within the given list (which belong to one process) are within
        the threshold.
        :param sources: The list of rows belonging that have the same process name.
        :param generic_checks: The list of booleans indicating the success of each row. This will be filled in
                               after each row is checked, and used to make the generic email in create_generic_result().
        :param generic_details: The string containing all the details of each result object only if the check for
                                that result object failed or had an exception.
        :return: <Result> <list> <string>
        Result: The Result object created after checking all rows with the given list.
        list: The list of booleans indicating the success of each row.
        string: The string containing all the details of each result object only if the check for that result object
                failed or had an exception.
        """
        process_checks, process_details = [], ""

        for row in sources:
            process_name = row.get("process")
            threshold_check, check_tb = self._check_against_threshold(row)
            generic_checks.append(threshold_check)
            process_checks.append(threshold_check)
            threshold_msg = self._create_threshold_message(row)
            details = self._create_details(
                row=row,
                threshold_check=threshold_check,
                threshold_message=threshold_msg,
                tb=check_tb
            )
            # append to process_details if a failure or exception occurred.
            if not threshold_check:
                process_details = details + "\n" + const.MESSAGE_SEPARATOR + "\n" + process_details
                generic_details = details + "\n" + const.MESSAGE_SEPARATOR + "\n" + generic_details

        result = self._create_process_result(process_name, process_checks, process_details)
        return result, generic_checks, generic_details

    @staticmethod
    def _create_details(row, threshold_check: bool, threshold_message, tb):
        """
        Creates detailed message by process name check results or by traceback in the previous processes.
        :param row: Dictionary containing information from 1 row in watchmenResults.csv.
        :param threshold_check: <bool> result of checking threshold, None upon exception
        :param tb: <str> traceback
        :return: <str> details
        """
        date, met_desc, met_type, met_val, process_name, source_name = \
            row.get("date"), row.get("metric_description"), row.get("metric_type"), \
            row.get("metric_value"), row.get("process"), row.get("source")

        if threshold_check is None:
            return DETAILS_FORMAT.format(EXCEPTION_DETAILS.format(process_name, source_name, date, tb),
                                         met_type, met_desc, met_val, threshold_message)
        if threshold_check is True:
            return DETAILS_FORMAT.format(SUCCESS_DETAILS.format(process_name, source_name, date),
                                         met_type, met_desc, met_val, threshold_message)
        else:
            return DETAILS_FORMAT.format(FAILURE_DETAILS.format(process_name, source_name, date),
                                         met_type, met_desc, met_val, threshold_message)

    def _create_generic_result(self, generic_checks, generic_details, generic_snapshot):
        """
        Create generic result that includes all the information.
        :param generic_checks: <list> list of all check results
        :param generic_details: <str> summarized details including all the information
        :param generic_snapshot: <list> list of dict that has attribute keys
        :return: <Result> Result object
        """
        has_outlier = True if False in generic_checks else False
        has_exception = True if None in generic_checks else False
        success = False if has_outlier or has_exception else True
        disable_notifier = success

        if has_outlier and has_exception:
            short_message = GENERIC + FAILURE_EXCEPTION_MESSAGE
            subject = GENERIC_FAIL_AND_EXCEPTION_SUBJECT
            state = Watchman.STATE.get("exception")
        elif has_outlier and not has_exception:
            short_message = GENERIC + FAILURE_MESSAGE
            subject = GENERIC_FAIL_SUBJECT
            state = Watchman.STATE.get("failure")
        elif not has_outlier and has_exception:
            short_message = GENERIC + EXCEPTION_MESSAGE
            subject = GENERIC_EXCEPTION_SUBJECT
            state = Watchman.STATE.get("exception")
        else:
            short_message = GENERIC + SUCCESS_MESSAGE
            subject = GENERIC_SUCCESS_SUBJECT
            state = Watchman.STATE.get("success")
        result = self._create_result(
            short_message=short_message,
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
        Creates results that contains details indicating that csv file is not loaded, or today's date is missing
        from the
        :return: <Result> Result object
        """
        date = self._get_date_today()
        # If the traceback is empty, then the file loaded correctly but there are no rows with today's date.
        if not tb:
            tb = "No rows with today's date exist."
        details = NOT_LOADED_DETAILS.format(date, DATA_FILE, tb)
        result = self._create_result(
            short_message=NOT_LOADED_MESSAGE,
            success=False,
            disable_notifier=False,
            state=Watchman.STATE.get("exception"),
            subject=NOT_LOADED_SUBJECT,
            details=details,
            snapshot={},
            target=GENERIC_TARGET,
        )
        return result

    def _create_process_result(self, process_name, process_checks, process_details):
        has_outlier = True if False in process_checks else False
        has_exception = True if None in process_checks else False
        success = False if has_outlier or has_exception else True
        disable_notifier = success

        if has_exception:
            parameters = self._create_summary_parameters(None, process_name)
        elif has_outlier:
            parameters = self._create_summary_parameters(False, process_name)
        else:
            parameters = self._create_summary_parameters(True, process_name)

        result = self._create_result(
            short_message=parameters.get("short_message"),
            target=parameters.get("target"),
            success=parameters.get("success"),
            disable_notifier=disable_notifier,
            state=parameters.get("state"),
            subject=parameters.get("subject"),
            details=process_details,
            snapshot={}
        )

        return result

    def _create_result(self, success, disable_notifier, state, subject, details, snapshot, target, short_message):
        """
        Creates the result object.
        :param success: <bool> whether the file was found, false upon exception, otherwise false
        :param disable_notifier: <bool> whether the SNS topic will be notified.
        :param state: <str> state of the monitor check
        :param subject: <str> subject for the notification
        :param details: <str> content for the notification
        :param snapshot: <list> row(s) being monitored.
        :param target: <string> The SNS topic.
        :param short_message: <string> The short message returned to the lambda.
        :return: <Result> result based on the parameters
        """
        result = Result(
            short_message=short_message,
            success=success,
            disable_notifier=disable_notifier,
            state=state,
            subject=subject,
            watchman_name=self.watchman_name,
            snapshot=snapshot,
            target=target,
            details=details)
        return result

    def _create_row_dicts_today(self):
        """
        Method that takes rows with today's date from list of all rows found within the CSV file.
        :return: List of rows with today's date. Each row in the CSV file is represented as a dictionary.
        """
        row_dicts, tb = self._read_csv()
        if not row_dicts:
            return None, ""
        row_dicts_today = self._get_data_by_date(row_dicts, self._get_date_today())

        return row_dicts_today, tb

    @staticmethod
    def _create_summary_parameters(threshold_check: bool, process_name):
        """
        Creates a dictionary that includes:
            success: whether the target is considered successful
            disable_notifier: whether we should disable the notifier
            state: state of result
            subject: subject for long notification
            short_message: short message describing whether the target is considered successful
            target: The SNS topic that will be notified if an exception or failure occurred.
        :param threshold_check: <bool> result of checking threshold, None upon exception
        :param process_name: <str> process name
        :return: <dict> parameters for creating results
        """
        parameter_chart = {
            None: {
                "success": False,
                "disable_notifier": False,
                "state": Watchman.STATE.get("exception"),
                "subject": EXCEPTION_SUBJECT.format(process_name),
                "short_message": EXCEPTION_MESSAGE,
                "target": TARGETS.get(process_name)
            },
            True: {
                "success": True,
                "disable_notifier": True,
                "state": Watchman.STATE.get("success"),
                "subject": SUCCESS_SUBJECT.format(process_name),
                "short_message": SUCCESS_MESSAGE,
                "target": TARGETS.get(process_name)
            },
            False: {
                "success": False,
                "disable_notifier": False,
                "state": Watchman.STATE.get("failure"),
                "subject": FAILURE_SUBJECT.format(process_name),
                "short_message": FAILURE_MESSAGE,
                "target": TARGETS.get(process_name)
            },
        }
        parameters = parameter_chart.get(threshold_check)
        return parameters

    @staticmethod
    def _create_threshold_message(row):
        """
        Creates message that includes information of min(3LCL), max(3UCL), and moving_mean.
        :param row: <dict> dictionary that has keys: "date", "process", "metric_type", "metric_value",
                          "moving_mean", "3LCL", "3UCL", "2LCL", "2UCL", "metric_description"
        :return: <str> constructed message
        """
        maximum, minimum, moving_mean = row.get("3UCL"), row.get("3LCL"), row.get("moving_mean")
        return MIN_AND_MAX_MESSAGE.format(moving_mean, minimum, maximum)

    def _fill_sources_per_process(self, sources_per_process, row_dicts_today):
        """
        This method will get all the rows with process name of {key} in sources_per_process and put them into a list.
        This list is the value for each process in the sources_per_process dictionary.
        :param sources_per_process:  The original sources_per_resource dictionary that contain all the possible
                                     processes as the keys, and empty lists as values.
                                             sources_per_process = {
                                                "domain_counts": [],
                                                "slowdrip": [],
                                                "reaper": []
                                             }
        :param row_dicts_today: The list of rows with today's date.
        :return: The updated sources_per_resource dictionary.
                 Example:
                {
                    domain_counts: [{row with source1}, {row with source2}],
                    slowdrip: [{row with source2}],
                    reaper: [{row with source2}, {row with source3}]
                }
        """
        for row in row_dicts_today:
            process = row.get("process")
            sources_per_process[process].append(row)

        return sources_per_process

    @staticmethod
    def _get_data_by_date(dict_list: list, date: str):
        """
        Gets list of rows in data for certain date
        :param dict_list: <list> list of dictionary representing rows in data
        :param date: <str> date of the data, eg. 2019-03-27
        :return: <list> list of dictionary with the date
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
        :return: <str> today's date, eg. 2019-03-27
        """
        return datetime.now(pytz.timezone("US/Pacific")).strftime("%Y-%m-%d")

    def _read_csv(self):
        """
        Reads csv file, None if fails.
        :return: <list> <str>
        <list> list of dictionaries indicating each row of the csv file
        <str> tracback
        """
        data_file = DATA_FILE
        data_file = "{}{}".format(PATH_PREFIX, data_file)
        try:
            csv_content_str = get_csv_data(key_name=data_file, bucket=BUCKET_NAME)
            data = csv_string_to_dict(csv_content_str)
            return data, None
        except Exception as ex:
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception("{}: {}".format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            return None, tb
