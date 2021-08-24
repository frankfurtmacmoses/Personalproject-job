"""
Created August 2021

This watchman is designed to check status of reflections pulled out on the fly by dremio.py based on information
specified in the config, dremoio_targets.yaml.
Currently the checks that can be performed are for reflections that already be created and that does not start
with tmp. Reflections status are checked every 60minutes


@author: Olawole Frankfurt Ogunfunminiyi
@email: oogunfunminiyi@infoblox.com
"""

import datetime
import os
import traceback
import yaml
import watchmen.utils.dremio as dremio
from watchmen import const, messages
from watchmen.common.result import Result
from watchmen.common.watchman import Watchman
from watchmen.config import settings

CONFIG_NAME = settings('ozymandias.targets')

SECRETE = settings('ozymandia.dremio_secret')
ROOT_URL = settings('ozymandia.ROOT_URL')
LOGIN_URL = settings('ozymandia.LOGIN_URL')
REFLECTION_URL = ('ozymandia.REFLECTION_URL')
MESSAGES = messages.OZYMANDIAS
TARGET_ACCOUNT = settings("TARGET_ACCOUNT", "atg")

CONFIG_PATH = os.path.join(
    os.path.realpath(os.path.dirname(__file__)), 'configs', CONFIG_NAME)


class Ozymandias(Watchman):

    def __init__(self, event, context):
        """
        Ozymandias Constructor
        """
        super().__init__()
        self.event = event.get('Type')

    def monitor(self):
        """
        Monitors Dremio Targets in the config.yaml file
        :return: <List> A list of result objects from the checks performed on each target.
        """

        if not self._is_valid_event():
            return self._create_invalid_event_result()

        github_targets, tb = self._load_config()
        if tb:
            return self._create_config_not_loaded_result()

        processed_targets = self._process_targets(github_targets)
        summary_parameters = self._create_summary_parameters(processed_targets)
        results = self._create_results(summary_parameters)
        return results

    ## Needed to be specific to Ozy
    @staticmethod
    def _create_details(processed_target):
        """
        Creates details for the result objects from the new_change_strings and exception_strings if they exist.
        :param processed_target: <dict> A dictionary of the target name with any failures or exceptions that occurred
        :return: <str> A details string for the target with information from the checks performed
        """
        target_name = processed_target.get('target_name')

        if processed_target.get('success'):
            return MESSAGES.get("success_details").format(target_name)

        details = ''
        if processed_target.get("exception_strings"):
            all_exceptions_string = "\n\n".join(processed_target.get("exception_strings"))
            details += MESSAGES.get("exception_details").format(target_name, all_exceptions_string) + "\n\n"

        if processed_target.get('new_changes_strings'):
            all_changes_string = "\n\n".join(processed_target.get("new_changes_strings"))
            details += MESSAGES.get("change_detected_details").format(target_name, all_changes_string) + "\n\n"

        return details

    def _create_results(self, summary_parameters):
        """
        This creates result objects for each of the summary parameters and a generic result for all of them. These will
        then be sent to subscribers of the corresponding sns topics.
        :param summary_parameters: <list<dict>>  The parameters needed to make each Result object.
        :return: <list> Result objects for each summary parameter, as well as a generic result object that represents
            all results.
        """
        results = []
        generic_result_details = ''
        change_detected = False
        exception = False
        for parameters in summary_parameters:
            success = parameters.get("success")

            if success is False:
                change_detected = True
            if success is None:
                exception = True

            if not success:
                generic_result_details += "{}{}\n\n".format(parameters.get("details"), const.MESSAGE_SEPARATOR)

            results.append(Result(
                details=parameters.get("details"),
                disable_notifier=parameters.get("disable_notifier"),
                short_message=parameters.get("short_message"),
                snapshot={},
                state=parameters.get("state"),
                subject=parameters.get("subject"),
                success=success is True,
                target=parameters.get("target"),
                watchman_name=self.watchman_name,
            ))
        results.append(self._create_generic_result(change_detected, exception, generic_result_details))
        return results

    def _create_generic_result(self, change_detected, exception, details):
        """
        This creates the generic result object which contains information from all checks performed for all targets.
        :param change_detected: <bool> True if there was a change detected during a github check
        :param exception: <bool> True if an exception occurred during a github check
        :param details: <str> A string with all the messages generated from each check
        :return: <Result> A result with all targets check information
        """
        if change_detected and exception:
            disable_notifier = False
            short_message = MESSAGES.get("change_detected_exception_message")
            state = Watchman.STATE.get("exception")
            subject = MESSAGES.get("generic_change_detected_exception_subject")
            success = False

        elif exception:
            disable_notifier = False
            short_message = MESSAGES.get("exception_message")
            state = Watchman.STATE.get("exception")
            subject = MESSAGES.get("generic_exception_subject")
            success = False

        elif change_detected:
            disable_notifier = False
            short_message = MESSAGES.get("change_detected_message")
            state = Watchman.STATE.get("failure")
            subject = MESSAGES.get("generic_change_detected_subject")
            success = False

        else:
            disable_notifier = True
            short_message = MESSAGES.get("success_message")
            state = Watchman.STATE.get("success")
            subject = MESSAGES.get("generic_success_subject")
            success = True

        return Result(
            details=details,
            disable_notifier=disable_notifier,
            short_message=short_message,
            snapshot={},
            watchman_name=self.watchman_name,
            state=state,
            subject=subject,
            success=success,
            target=GENERIC_TARGET,
        )

    def _create_summary_parameters(self, processed_targets):
        """
        Create the parameters needed for result objects based on the checks performed for each target.
        :param processed_targets: <list<dict>> Dictionaries of information from each check performed on a target
        :return: <list<dict>> Returns a dictionary for every processed target that has the parameters needed to create
            the result object for that target
        """
        summary_parameters = []
        parameter_chart = {
            None: {
                "disable_notifier": False,
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

        for target in processed_targets:
            target_name = target.get('target_name')
            success = target.get('success')
            parameters = parameter_chart.get(success).copy()
            parameters.update({'target': target_name, 'details': self._create_details(target)})

            if success:
                parameters.update({"short_message": MESSAGES.get("success_message")})
                parameters.update({"subject": MESSAGES.get("success_subject").format(target_name)})
            elif target.get('success') is None:
                parameters.update({"short_message": MESSAGES.get("exception_message")})
                parameters.update({"subject": MESSAGES.get("exception_subject").format(target_name)})
            else:
                # If there are exceptions and failures:
                if target.get("exception_strings"):
                    parameters.update({"short_message": MESSAGES.get("change_detected_exception_message")})
                    parameters.update({"subject": MESSAGES.get("change_detected_exception_subject")
                                      .format(target_name)})
                else:
                    parameters.update({"short_message": MESSAGES.get("change_detected_message")})
                    parameters.update({"subject": MESSAGES.get("change_detected_subject").format(target_name)})

            summary_parameters.append(parameters)

        return summary_parameters

    @staticmethod
    def _format_api_exception(check_name, target_name, tb, path=None):
        """
        Returns an exception string with information about a Github API Failure
        :param check_name: <str> Name of the check that threw the exception
        :param target_name: <str> The target name
        :param tb: <str> The traceback of the exception
        :param path: <str> The path the exception occurred on, if applicable
        :return: <str> An message with information from the API exception
        """
        if path:
            return MESSAGES.get("exception_api_failed_w_path").format(check_name, target_name, path, tb)

        return MESSAGES.get("exception_api_failed").format(check_name, target_name, tb)
