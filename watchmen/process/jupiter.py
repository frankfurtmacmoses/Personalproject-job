"""
Created on January 29, 2019

This script monitors a variety of Cyber-Intel endpoints and ensures they are working correctly.
Endpoints may have keys to check that determine if certain resources are working as well.
Example: An endpoint may check the db_info key to ensure the database is working

If an endpoint is not working correctly or key check fails its conditions, an SNS will be sent.

@author: Kayla Ramos
@email: kramos@infoblox.com

Refactored on February 18, 2020
@author Michael Garcia
@email garciam@infoblox.com
"""
import json
import pytz

from datetime import datetime
from watchmen import const
from watchmen import messages
from watchmen.common.cal import InfobloxCalendar
from watchmen.common.result import Result
from watchmen.common.svc_checker import ServiceChecker
from watchmen.common.watchman import Watchman
from watchmen.config import settings
from watchmen.process.endpoints import DATA as ENDPOINTS_DATA
from watchmen.utils.sns_alerts import raise_alarm
from watchmen.utils.s3 import copy_contents_to_bucket
from watchmen.utils.s3 import get_content

CHECK_TIME_UTC = datetime.utcnow()
DATETIME_FORMAT = '%Y%m%d_%H%M%S'
HOLIDAY_NOTIFICATION_TIMES = [8, 16]
MESSAGES = messages.JUPITER
SNS_TOPIC_ARN = settings("jupiter.sns_topic", "arn:aws:sns:us-east-1:405093580753:Watchmen_Test")
TARGET = "Cyber-Intel Endpoints"
WORKDAY_NOTIFICATION_TIMES = [8, 12, 16]

# S3
S3_BUCKET = settings('jupiter.bucket')
S3_PREFIX_JUPITER = settings('jupiter.s3_prefix')


class Jupiter(Watchman):

    # pylint: disable=unused-argument
    def __init__(self, event, context):
        super().__init__()
        self.result_message = ""
        pass

    def monitor(self) -> [Result]:
        """
        Monitors Cyber-Intel endpoints.
        :return: Result object list (with one Result) with information on the health of Cyber-Intel endpoints.
        """
        endpoints = self.load_endpoints()
        endpoints_with_path = self.check_endpoints_path(endpoints)

        # There is no need to run the rest of the code if there are no valid endpoints.
        if endpoints_with_path is None:
            result = self._create_invalid_endpoints_result()
            return [result]

        checker = ServiceChecker(endpoints_with_path)
        checker_results = checker.start()
        self.log_result(checker_results)
        validated_paths = checker.get_validated_paths()
        summarized_result = self.summarize(checker_results, endpoints, validated_paths)

        date_check_result, details = self._check_skip_notification_(summarized_result)
        parameters = self._get_result_parameters(date_check_result)

        # The result_message is empty if the load_endpoints and check_endpoints_path were both successful.
        if not self.result_message:
            self.result_message = MESSAGES.get("success_message")

        result = Result(
            success=parameters.get("success"),
            disable_notifier=parameters.get("disable_notifier"),
            message=self.result_message,
            snapshot={},
            state=parameters.get("state"),
            subject=parameters.get("subject"),
            source=self.source,
            target=TARGET,
            details=details
        )
        return [result]

    def _append_to_message(self, message_to_append):
        self.result_message += message_to_append + const.LINE_SEPARATOR

    def check_endpoints_path(self, endpoints):
        """
        Checks if first level endpoints are valid or not.
        Non-valid endpoints are printed with error messages.
        If too few validated endpoints exist, no need to check.
        @param endpoints: endpoints to be checked
        @return: <list>, <str>
        <list> list of validated endpoints, None if there are no endpoints with a path variable.
        <str> Message that contains information on which endpoints did not have paths. This message will be empty
              if all endpoints are valid and have an endpoint.
        """
        bad_list = []
        validated = []

        for endpoint in endpoints:
            if endpoint.get('path'):
                validated.append(endpoint)
            else:
                bad_list.append(endpoint)

        if bad_list:
            messages = []
            for item in bad_list:
                msg = 'There is not a path to check for: {}'.format(item.get('name', "There is not a name available"))
                messages.append(msg)
                self.logger.error('Notify failure:\n%s', msg)
            alarm_message = '\n'.join(messages)
            self._append_to_message(MESSAGES.get("bad_endpoints_message"))
            raise_alarm(SNS_TOPIC_ARN, subject=MESSAGES.get("error_subject"), msg=alarm_message)

        if not validated:
            self.logger.warning(MESSAGES.get("not_enough_eps_message"))
            return None

        return validated

    def _check_notification_time(self):
        """
        Checks if the current day & hour fall under the desired notification times. If the check returns
        false, there is no need to send a notification.
        @return: True if it is the correct time to send a notification, False if it is not the correct time.
        """
        now = self._get_time_pdt()
        hour = now.hour
        year = now.year
        # Create a calendar for last year, current year, and next year
        cal = InfobloxCalendar(year - 1, year + 1)

        if not cal.is_workday():
            # Holidays or weekends: Send notifications at 8am or 4pm PST.
            is_notification_time = hour in HOLIDAY_NOTIFICATION_TIMES
        else:
            # Workdays: Send notifications at 8am, 12pm, or 4pm PST.
            is_notification_time = hour in WORKDAY_NOTIFICATION_TIMES

        self.logger.debug("The current PST hour is %s and notification_time = %s", hour, is_notification_time)

        return is_notification_time

    def _check_skip_notification_(self, summarized_result):
        """
        Check if the SNS notification can be sent.
        If there are failed endpoints that do not use the calendar or an error occurred while trying to test endpoints,
        then a notification will always be sent.
        If there are failed endpoints that do use the calendar, then a notification for those endpoints will only be
        sent based on the following time configurations:
            - If the day is a holiday and the hour is 8am or 4pm, a notification will be sent.
            - If the day is a work day and the hour is 8am, 12pm, or 4pm, a notification will be sent.
        Notifications are skipped if there are no failed endpoints or if there are only failed endpoints that use the
        calendar and it is not time to send a notification.

        @param summarized_result: dictionary containing notification information
        @return: <bool>, <str>
        <bool>: True if the notification is skipped, false if not.
        <str>: The details for the result object.
        """
        failed_endpoints_not_using_cal = summarized_result.get("failed_endpoints_not_using_cal")
        failed_endpoints_using_cal = summarized_result.get("failed_endpoints_using_cal")
        failed_nocal_endpoints_msg = summarized_result.get("failed_nocal_endpoints_msg")
        message = summarized_result.get('message')
        success = summarized_result.get('success')

        if success:
            return True, message

        # If there are only failed endpoints that do not use the calendar, a notification is always sent.
        if not failed_endpoints_using_cal:
            return False, message

        is_notification_time = self._check_notification_time()

        # If it is notification time, send the notification containing all failed endpoints.
        if is_notification_time:
            return False, message

        # If it is NOT notification time, a notification containing information about the failed endpoints that do NOT
        # use the calendar will be sent.
        if not is_notification_time and failed_endpoints_not_using_cal:
            return False, failed_nocal_endpoints_msg

        # If there are only failed endpoints that use the calendar and it is not notification time, a notification
        # is NOT sent.
        return True, MESSAGES.get("skip_message_format").format(CHECK_TIME_UTC)

    def _create_invalid_endpoints_result(self):
        """
        This method is called when there are no endpoints with the "path" variable, so
        the rest of the code can not be run.
        :return: Result object.
        """
        parameters = self._get_result_parameters(None)
        message = self.result_message
        if not message:
            message = MESSAGES.get("not_enough_eps_message")

        result = Result(
            details=MESSAGES.get("not_enough_eps_message"),
            disable_notifier=parameters.get("disable_notifier"),
            message=message,
            snapshot={},
            source=self.source,
            state=parameters.get("state"),
            subject=parameters.get("subject"),
            success=parameters.get("success"),
            target=TARGET,
        )
        raise_alarm(topic_arn=SNS_TOPIC_ARN, msg=MESSAGES.get("not_enough_eps_message"),
                    subject=parameters.get('subject'))
        return result

    def _get_result_parameters(self, endpoint_check):
        """
        Returns the dictionary with the correct values for the Result object, based on the result of checking endpoints.
        :param endpoint_check: The result of checking endpoints.
        :return: Dictionary with the correct values for the Result object.
        """
        parameter_chart = {
            False: {
                "success": False,
                "disable_notifier": False,
                "state": Watchman.STATE.get("failure"),
                "subject": MESSAGES.get("failure_subject"),
            },
            None: {
                "success": False,
                "disable_notifier": False,
                "state": Watchman.STATE.get("exception"),
                "subject": MESSAGES.get("not_enough_eps"),
            },
            True: {
                "success": True,
                "disable_notifier": True,
                "state": Watchman.STATE.get("success"),
                "subject": MESSAGES.get("success_subject"),
            },
        }

        return parameter_chart.get(endpoint_check)

    def _get_time_pdt(self):
        return pytz.utc.localize(CHECK_TIME_UTC).astimezone(pytz.timezone('US/Pacific'))

    def load_endpoints(self):
        """
        Loads json file of endpoints.
        If an exception is thrown (meaning an error with opening and/or loading),
        an sns will be sent to the Sockeye Topic
        :return: the endpoints or exits upon exception
        """
        data_path = settings("jupiter.s3_prefix")
        data_file = settings("jupiter.endpoints")

        if data_path:
            data_file = '{}/{}'.format(data_path, data_file)

        bucket = settings("jupiter.bucket")

        try:
            data = get_content(key_name=data_file, bucket=bucket)
            endpoints = json.loads(data)
            if endpoints and isinstance(endpoints, list):
                return endpoints
        except Exception as ex:
            formatted_data = ""

            for endpoint in ENDPOINTS_DATA:
                formatted_data += "\tName: " + endpoint.get('name') + "\n"
                formatted_data += "\tPath: " + endpoint.get('path') + "\n\n"

            message = MESSAGES.get("s3_fail_load_message").format(bucket, data_file, formatted_data, ex)
            self._append_to_message(message)
            self.logger.warning(message)
            raise_alarm(topic_arn=SNS_TOPIC_ARN, subject=MESSAGES.get("s3_fail_load_subject"), msg=message)

        endpoints = ENDPOINTS_DATA
        return endpoints

    def log_result(self, results):
        """
        Log results to s3
        @param results: to be logged
        """
        try:
            prefix_datetime = CHECK_TIME_UTC.strftime(DATETIME_FORMAT)
            prefix_result = '{}/{}/{}'.format(S3_PREFIX_JUPITER, CHECK_TIME_UTC.year, prefix_datetime)
            self.logger.info("Jupiter Watchmen results:\n{}".format(results))
            # save result to s3
            content = json.dumps(results, indent=4, sort_keys=True)
            copy_contents_to_bucket(content, prefix_result, S3_BUCKET)
        except Exception as ex:
            self.logger.error(ex)
        return prefix_result

    def summarize(self, results, endpoints, validated_paths):
        """
        Creates a dictionary based on endpoints results.
        This dictionary will be given to monitor to create alarm messages and logs.

        Variables included in dictionary:
            failed_endpoints_not_using_cal: Boolean indicating if there were failed endpoints that do NOT use the cal.
            failed_endpoints_using_cal: Boolean indicating if there were failed endpoints that DO use the calendar.
            failed_nocal_endpoints_msg: Message (String) for failed endpoints that do not use the calendar.
            message: Message (String) describing the result of checking all endpoints.
            subject: Subject of the SNS notification (String),
            success: Boolean, true if all endpoints are working, false if any endpoints failed or an error occurred.

        @param results: dict to be checked for failed endpoints
        @param endpoints: loaded endpoints data
        @param validated_paths: validated endpoints
        @return: the notification message
        """
        if not results or not isinstance(results, dict):
            message = MESSAGES.get("results_dne")
            return {
                "failed_endpoints_not_using_cal": False,
                "failed_endpoints_using_cal": False,
                "failed_nocal_endpoints_msg": "",
                "message": message,
                "subject": MESSAGES.get("error_jupiter"),
                "success": False
            }

        failure = results.get('failure', [])
        success = results.get('success', [])

        # Checking if results is empty
        if not failure and not success:
            message = 'Empty result:\n{}\n{}\nEndpoints:\n{}\n{}\n{}'.format(
                json.dumps(results, sort_keys=True, indent=2),
                const.MESSAGE_SEPARATOR,
                json.dumps(endpoints, indent=2),
                const.MESSAGE_SEPARATOR,
                json.dumps(validated_paths, indent=2)
            )
            self.logger.error(message)
            message = "{}\n\n\n{}".format(message, MESSAGES.get("no_results"))
            return {
                "failed_endpoints_not_using_cal": False,
                "failed_endpoints_using_cal": False,
                "failed_nocal_endpoints_msg": "",
                "message": message,
                "subject": MESSAGES.get("error_jupiter"),
                "success": False
            }

        # Checking failure list and announcing errors
        if failure and isinstance(failure, list):
            failed_endpoints_not_using_cal = False
            failed_endpoints_using_cal = False
            failed_nocal_endpoints_msgs = []
            messages = []

            for item in failure:
                msg = '\tname: {}\n\tpath: {}\n\terror: {}'.format(
                    item.get('name'), item.get('path'), item.get('_err')
                )
                messages.append(msg)
                if item.get("calendar") == "enabled":
                    failed_endpoints_using_cal = True
                else:
                    failed_endpoints_not_using_cal = True
                    failed_nocal_endpoints_msgs.append(msg)

                self.logger.error('Notify failure:\n%s', msg)

            message = '{}\n\n\n{}'.format('\n\n'.join(messages), MESSAGES.get("check_logs"))
            failed_nocal_endpoints_msg = '{}\n\n\n{}'.format('\n\n'.join(failed_nocal_endpoints_msgs),
                                                             MESSAGES.get("check_logs"))

            first_failure = 's' if len(failure) > 1 else ' - {}'.format(failure[0].get('name'))
            subject = '{}{}'.format(MESSAGES.get("error_subject"), first_failure)
            return {
                "failed_endpoints_not_using_cal": failed_endpoints_not_using_cal,
                "failed_endpoints_using_cal": failed_endpoints_using_cal,
                "failed_nocal_endpoints_msg": failed_nocal_endpoints_msg,
                "message": message,
                "subject": subject,
                "success": False
            }

        # All Successes
        return {
            "failed_endpoints_not_using_cal": False,
            "failed_endpoints_using_cal": False,
            "failed_nocal_endpoints_msg": "",
            "message": MESSAGES.get("success_message"),
            "subject": MESSAGES.get("success_subject"),
            "success": True
        }
