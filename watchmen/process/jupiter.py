"""
Created on January 29, 2019

This script monitors a variety of Cyber-Intel endpoints and ensures they are working correctly.
Endpoints may have keys to check that determine if certain resources are working as well.
Example: An endpoint may check the db_info key to ensure the database is working

If an endpoint is not working correctly or key check fails its conditions, an SNS will be sent.

@author: Kayla Ramos
@email: kramos@infoblox.com

Refactored on October 30, 2019
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
from watchmen.config import get_boolean
from watchmen.config import settings
from watchmen.process.endpoints import DATA as ENDPOINTS_DATA
from watchmen.utils.sns_alerts import raise_alarm
from watchmen.utils.s3 import copy_contents_to_bucket
from watchmen.utils.s3 import get_content
from watchmen.utils.s3 import mv_key

CHECK_TIME_UTC = datetime.utcnow()
CHECK_TIME_PDT = pytz.utc.localize(CHECK_TIME_UTC).astimezone(pytz.timezone('US/Pacific'))
DATETIME_FORMAT = '%Y%m%d_%H%M%S'
MESSAGES = messages.JUPITER
SNS_TOPIC_ARN = settings("jupiter.sns_topic", "arn:aws:sns:us-east-1:405093580753:Watchmen_Test")
TARGET = "Cyber-Intel Endpoints"

# S3
S3_BUCKET = settings('jupiter.bucket')
S3_PREFIX_JUPITER = settings('jupiter.s3_prefix')
S3_PREFIX_STATE = '{}/LATEST'.format(S3_PREFIX_JUPITER)


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
        # This method is only used when updating the endpoints on S3.
        # _update_endpoints()
        endpoints = self.load_endpoints()
        endpoints_with_path = self.check_endpoints_path(endpoints)

        # There is no need to run the rest of the code if there are no valid endpoints.
        if endpoints_with_path is None:
            result = self._create_invalid_endpoints_result()
            return [result]

        checker = ServiceChecker(endpoints_with_path)
        checker_results = checker.start()
        prefix = self.log_result(checker_results)
        validated_paths = checker.get_validated_paths()
        summarized_result = self.summarize(checker_results, endpoints, validated_paths)
        self.log_state(summarized_result, prefix)

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

    def _check_failure(self):
        """
        Use key, e.g. bucket/prefix/LATEST to check if the current check failed.
        LATEST key contains result (non-empty) if current result has failure; empty indicates success.

        @return: True if current check failed; otherwise, False.
        """
        data = get_content(S3_PREFIX_STATE, bucket=S3_BUCKET)
        return data != '' and data is not None

    def _check_notification_time(self):
        """
        Checks if the current day & hour fall under the desired notification times. If the check returns
        false, there is no need to send a notification.
        @return: True if it is the correct time to send a notification, False if it is not the correct time.
        """
        now = self._get_time_pdt()
        hour = now.hour
        year = now.year
        notification_time = False
        # Create a calendar for last year, current year, and next year
        cal = InfobloxCalendar(year - 1, year + 1)

        if not cal.is_workday():
            notification_time = hour != 0 and hour % 8 == 0
        elif cal.is_workhour(hour):
            notification_time = hour % 4 == 0

        self.logger.debug("The current hour is %s and notification_time = %s", hour, notification_time)

        return notification_time

    def _check_skip_notification_(self, summarized_result):
        """
        Check if the SNS notification can be sent.
        If the day is a holiday and the hour is 8am or 4pm, a notification will be sent.
        If the day is a work day and the hour is 8am, 12pm, or 4pm, a notification will be sent.
        Otherwise, all notifications will be skipped.
        @param summarized_result: dictionary containing notification information
        @return: <bool>, <str>
        <bool>: True if the notification is skipped, false if not.
        <str>: The details for the result object.
        """
        details = summarized_result.get('message')
        success = summarized_result.get('success')

        if success:
            return True, details

        enable_calendar = get_boolean('jupiter.enable_calendar')
        failed = summarized_result.get('last_failed')
        notification_time = self._check_notification_time()
        # Skip if last check in state file is a failure and it is not time to send a notification
        is_skipping = enable_calendar and failed and not notification_time
        if is_skipping:
            return True, MESSAGES.get("skip_message_format").format(CHECK_TIME_UTC)

        return False, details

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

    def log_state(self, summarized_result, prefix):
        """
        Logs whether the current state of Jupiter contains failed endpoints or all are successes.
        If there are failures, they will be written to the LATEST file on s3.
        An empty LATEST file indicates that there are no failures.
        Each time this method is run, it will overwrite the contents of LATEST.
        @param summarized_result: dictionary containing results of the sanitization of the successful and
                                  failed endpoints.
        @param prefix: prefix of the original file
        """
        try:
            success = summarized_result.get('success')
            content = '' if success else json.dumps(summarized_result, indent=4, sort_keys=True)
            copy_contents_to_bucket(content, S3_PREFIX_STATE, S3_BUCKET)
            state = 'SUCCESS' if success else 'FAILURE'
            mv_key(prefix, '{}_{}.json'.format(prefix, state), bucket=S3_BUCKET)
        except Exception as ex:
            self.logger.error(ex)

    def summarize(self, results, endpoints, validated_paths):
        """
        Creates a dictionary based on endpoints results.
        This dictionary will be given to monitor to create alarm messages and logs.
        @param results: dict to be checked for failed endpoints
        @param endpoints: loaded endpoints data
        @param validated_paths: validated endpoints
        @return: the notification message
        """
        is_failure = self._check_failure()

        if not results or not isinstance(results, dict):
            message = MESSAGES.get("results_dne")
            return {
                "last_failed": is_failure,
                "message": message,
                "subject": MESSAGES.get("error_jupiter"),
                "success": False,
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
                "last_failed": is_failure,
                "message": message,
                "subject": MESSAGES.get("error_jupiter"),
                "success": False,
            }

        # Checking failure list and announcing errors
        if failure and isinstance(failure, list):
            messages = []
            for item in failure:
                msg = '\tname: {}\n\tpath: {}\n\terror: {}'.format(
                    item.get('name'), item.get('path'), item.get('_err')
                )
                messages.append(msg)
                self.logger.error('Notify failure:\n%s', msg)
            message = '{}\n\n\n{}'.format('\n\n'.join(messages), MESSAGES.get("check_logs"))

            first_failure = 's' if len(failure) > 1 else ' - {}'.format(failure[0].get('name'))
            subject = '{}{}'.format(MESSAGES.get("error_subject"), first_failure)
            return {
                "last_failed": is_failure,
                "message": message,
                "subject": subject,
                "success": False,
            }

        # All Successes
        return {
            "message": MESSAGES.get("success_message"),
            "subject": MESSAGES.get("success_subject"),
            "success": True,
        }

    def _update_endpoints(self):
        """
        This methods will update the the endpoints.json file on S3 to match watchmen/process/endpoints.json
        This is a private method that is only used locally and should be uncommented in the monitor() when intending
        to update endpoints.
        """
        content = json.dumps(ENDPOINTS_DATA, indent=4, sort_keys=True)
        key = '{}/endpoints.json'.format(S3_PREFIX_JUPITER)
        copy_contents_to_bucket(content, key, S3_BUCKET)
