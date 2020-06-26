"""
Metropolis class for monitoring metrics and KPI change detection.
Created on 8.21.2019
@author: Jinchi Zhang
@email: jzhang@infoblox.com

Refactored on 10.17.2019
@author: Michael Garcia
@email: garciam@infoblox.com
"""
from collections import Counter
from datetime import datetime
import pytz
import requests
import traceback

from watchmen import const
from watchmen import messages
from watchmen.common.watchman import Result
from watchmen.common.watchman import Watchman
from watchmen.config import settings
from watchmen.utils.csv import csv_string_to_dict
from watchmen.utils.s3 import get_csv_data

BUCKET_NAME = settings("metropolis.bucket_name", "cyber-intel")
DATA_FILE = settings("metropolis.data_file", "watchmenResults.csv")
MESSAGES = messages.METROPOLIS
PATH_PREFIX = settings("metropolis.path_prefix", "analytics/change_detection/prod/")
REAPER_HEADERS = {"x-api-key": settings("metropolis.reaper.metrics_api_key")}
REAPER_INDICATOR_TYPES = {'IPV4', 'IPV6', 'FQDN', 'URI'}
REAPER_METRICS_URL = settings("metropolis.reaper.metrics_url")

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
        self.reaper_metrics = {}

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
                self.logger.info(MESSAGES.get("process_not_in_file").format(process))
                continue
            result, generic_checks, generic_details = self._check_all_sources(sources, generic_checks, generic_details)
            results.append(result)

        results.append(self._create_generic_result(generic_checks, generic_details, row_dicts_today))
        return results

    def _calculate_reaper_indicator_metrics(self, metrics_data):
        """
        Calculate the total number of indicators received for past 24 hrs
        :param metrics_data: <dict>
        Updates reaper_metrics: <list> list of dictionaries of reaper metrics. Looks like below format:
               [
                 {"source": "AIS", "metric": {"IPV4_TIDE_SUCCESS": 312, "IPV4": 156}},
                 {"source": "BLOX_cyberint", "metric": {"FQDN_TIDE_SUCCESS": 783, "FQDN": 261}},
                 {"source": "AIS", "metric": {"FQDN_TIDE_SUCCESS": 312, "FQDN": 20}}
               ]
        <dict> dictionary of reaper metrics in the format below:
               {'FQDN': 100, 'IPV4': 500, 'URI': 50}
        """
        counter = Counter()
        for item in metrics_data:
            for key in item['metric'].keys():
                if key in REAPER_INDICATOR_TYPES:
                    counter.update({key: int(item['metric'][key])})
        self.reaper_metrics = dict(counter)

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
                return None, MESSAGES.get("min_and_max_error_message")
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
        Method that checks if all rows with moving_mean within the given list (which belong to one process) are within
        the threshold. The rows without moving_mean, triggers to get live data from targets and update the moving_mean
        accordingly and check against the threshold.
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
            should_check_against_threshold = True
            if row.get('moving_mean') is None:
                # get the live data for the process incase 'moving mean' is not present.
                should_check_against_threshold, tb = self._get_live_target_data(row)
            if should_check_against_threshold:
                threshold_check_result, check_tb = self._check_against_threshold(row)
            else:
                threshold_check_result, check_tb = should_check_against_threshold, tb
            generic_checks.append(threshold_check_result)
            process_checks.append(threshold_check_result)
            threshold_msg = self._create_threshold_message(row)
            details = self._create_details(
                row=row,
                threshold_check=threshold_check_result,
                threshold_message=threshold_msg,
                tb=check_tb
            )
            # append to process_details if a failure or exception occurred.
            if not threshold_check_result:
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

        if threshold_check:
            return MESSAGES.get("details_format").format(MESSAGES.get("success_details").format(process_name,
                                                         source_name, date), met_type, met_desc, met_val,
                                                         threshold_message)

        if threshold_check is None:
            return MESSAGES.get("details_format").format(MESSAGES.get("exception_details").format(process_name,
                                                         source_name, date, tb), met_type, met_desc, met_val,
                                                         threshold_message)

        return MESSAGES.get("details_format").format(MESSAGES.get("failure_details").format(process_name,
                                                     source_name, date), met_type, met_desc, met_val,
                                                     threshold_message)

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
            short_message = MESSAGES.get("generic") + MESSAGES.get("failure_exception_message")
            subject = MESSAGES.get("generic_fail_and_exception_subject")
            state = Watchman.STATE.get("exception")
        elif has_outlier and not has_exception:
            short_message = MESSAGES.get("generic") + MESSAGES.get("failure_message")
            subject = MESSAGES.get("generic_fail_subject")
            state = Watchman.STATE.get("failure")
        elif not has_outlier and has_exception:
            short_message = MESSAGES.get("generic") + MESSAGES.get("exception_message")
            subject = MESSAGES.get("generic_exception_subject")
            state = Watchman.STATE.get("exception")
        else:
            short_message = MESSAGES.get("generic") + MESSAGES.get("success_message")
            subject = MESSAGES.get("generic_success_subject")
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
        details = MESSAGES.get("not_loaded_details").format(date, DATA_FILE, tb)
        result = self._create_result(
            short_message=MESSAGES.get("not_loaded_message"),
            success=False,
            disable_notifier=False,
            state=Watchman.STATE.get("exception"),
            subject=MESSAGES.get("not_loaded_subject"),
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
                "subject": MESSAGES.get("exception_subject").format(process_name),
                "short_message": MESSAGES.get("exception_message"),
                "target": TARGETS.get(process_name)
            },
            True: {
                "success": True,
                "disable_notifier": True,
                "state": Watchman.STATE.get("success"),
                "subject": MESSAGES.get("success_subject").format(process_name),
                "short_message": MESSAGES.get("success_message"),
                "target": TARGETS.get(process_name)
            },
            False: {
                "success": False,
                "disable_notifier": False,
                "state": Watchman.STATE.get("failure"),
                "subject": MESSAGES.get("failure_subject").format(process_name),
                "short_message": MESSAGES.get("failure_message"),
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
        return MESSAGES.get("min_and_max_message").format(moving_mean, minimum, maximum)

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

    def _get_live_target_data(self, row):
        """
        Get the live target data from all the sources.
        Note: New target name to be updated under "live_target" when added
        :param row: Dictionary containing information from row in watchmenResults.csv
        :return: <bool> <str>
        <bool> return value from target function
        <str> traceback
        """
        source = row.get("process")
        try:
            source_function = getattr(self, '_get_{}_data'.format(source))
            return source_function(row)
        except Exception as ex:
            self.logger.error("ERROR retrieving source {} function!".format(source))
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception("{}: {}".format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            return None, tb

    def _get_reaper_data(self, row):
        """
        Performs a GET request to the Metrics API to get the indicator volume for last 24 hours.
        :param row: Dictionary containing information from row in watchmenResults.csv
        :return: <bool> <str>
        <bool> whether moving_mean is updated
        <str> traceback

        Reaper metrics data will be in following format:
        {
            "total_tide_submissions": 699220,
            "details": [
            {
                "source": "AIS",
                "metric": {
                    "IPV4_TIDE_SUCCESS": 312,
                    "IPV4": 156,
                    "Policy_NCCICwatchlist": 156
                },
                "timestamp": "2020-06-05T11"
            },
            {
                "source": "BLOX_cyberint",
                "metric": {
                    "IPV4_TIDE_SUCCESS": 783,
                    "Scanner_Generic": 259,
                    "Bot_Mirai": 2,
                    "IPV4": 261
            },
            "timestamp": "2020-06-05T11"
            ]
        }

        The part we are interested in is the "details" dictionary, so we grab that and return it as the
        "metrics_data".
        """
        try:
            if not self.reaper_metrics:
                metrics_api_response = requests.get(url=REAPER_METRICS_URL, headers=REAPER_HEADERS).json()
                metrics_data = metrics_api_response["details"]
                self._calculate_reaper_indicator_metrics(metrics_data)

            if row['metric_type'] in self.reaper_metrics:
                row['moving_mean'] = self.reaper_metrics[row['metric_type']]
                return True, None
            return False, MESSAGES.get('no_indicator_message').format(row.get('metric_type'), row.get('process'))
        except Exception as ex:
            self.logger.error("ERROR retrieving Reaper Data!")
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception("{}: {}".format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            return None, tb

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
