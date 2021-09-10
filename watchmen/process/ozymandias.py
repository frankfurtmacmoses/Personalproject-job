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
import json
import os
import traceback

import requests as requests
import yaml
import watchmen.utils.dremio as dremio
from watchmen import const, messages
from watchmen.common.result import Result
from watchmen.common.watchman import Watchman
from watchmen.config import settings

CONFIG_NAME = settings('ozymandias.targets')

SECRETE_PATH = settings('ozymandias.dremio_secret_path')
ROOT_URL = settings('ozymandias.ROOT_URL')
LOGIN_URL = settings('ozymandias.LOGIN_URL')
REFLECTION_URL = settings('ozymandias.REFLECTION_URL')
MESSAGES = messages.OZYMANDIAS
REGION = settings("ozymandias.targets.region")
secrete_name = settings("ozymandias.targets.secrete_name")
DREMIO_REFLECTIONS = "Dremio_Reflections"
CONFIG_PATH = os.path.join(
    os.path.realpath(os.path.dirname(__file__)), 'configs', CONFIG_NAME)


class Ozymandias(Watchman):

    def __init__(self, event, context):
        """
        Ozymandias Constructor
        """
        super().__init__()
        #self.event = event.get('Type')

    def monitor(self):
        """
        Monitors Dremio Targets in the config.yaml file
        :return: <List> A list of result objects from the checks performed on each target.
        """
        reflection_info = self._get_reflections_info()
        processed_reflection_info = self._process_reflection_info(reflection_info)
        result = self._create_result(processed_reflection_info)
        return result

    def _get_reflections_info(self):
        """
        Creates details for the result objects from the new_change_strings and exception_strings if they exist.
        :param processed_target: <dict> A dictionary of the target name with any failures or exceptions that occurred
        :return: <str> A details string for the target with information from the checks performed
        Return list containing dictionary of reflection result
         Get information about single reflection and return ->  "status": {
        "config": "OK",
        "refresh": "SCHEDULED",
        "availability": "AVAILABLE",
        "combinedStatus": "CAN_ACCELERATE",
        "failureCount": 0,
        "lastDataFetch": "2021-08-16T20:55:58.311Z",
        "expiresAt": "2021-08-16T23:55:58.311Z"
                                 }
        """
        computed_result = {}
        secret = dremio.get_secret(SECRETE_PATH, REGION)
        token = secret[secrete_name]
        user_name = secret['username']
        try:
            auth_token = dremio.generate_auth_token(user_name, token, LOGIN_URL)
            reflection_list = dremio.get_reflection_list(auth_token, REFLECTION_URL) #need full path
            computed_result = dremio.fetch_reflection_metadata(auth_token, REFLECTION_URL, reflection_list) ## need full path
        except requests.exceptions.RequestException as exp:
            computed_result["Error"] = exp.errno
        return computed_result

    def _process_reflection_info(self, reflection_results):
        result_bucket = {}
        for reflection in reflection_results:
            reflectionid, name, failurecount = reflection['id'], reflection['name'], \
                                               reflection['status']['failureCount']
            if failurecount == 3:
                result_bucket[reflectionid]: {name: failurecount}
        return result_bucket

    def _create_result(self, reflection_final_result) -> {}:
        """
        Determine the outcome of the check
        If {reflection_final_result} is not empty, Failed reflections present in {}
        Or exception has occurred. ,Otherwise, if {} is empty,
        All reflection passed the refresh test.
        """
        if (reflection_final_result):
            if 'Error' in reflection_final_result:
                disable_notifier = False
                short_message = MESSAGES.get("reflection_exception_message")
                state = Watchman.STATE.get("exception")
                subject = MESSAGES.get("exception_detected_subject")
                success = False
            else:
                disable_notifier = False
                short_message = MESSAGES.get("reflection_failed_message")
                state = Watchman.STATE.get("failled")
                subject = MESSAGES.get("reflection_failled_subject")
                success = False

        else:
            detail = MESSAGES.get('reflection_success_detail')
            disable_notifier = True
            short_message = MESSAGES.get("reflection_success_message")
            state = Watchman.STATE.get("success")
            subject = MESSAGES.get("reflection_success_subject")
            success = True

        return [Result(
            details=json.dumps(reflection_final_result),
            disable_notifier=disable_notifier,
            short_message=short_message,
            snapshot={},
            watchman_name=self.watchman_name,
            state=state,
            subject=subject,
            success=success,
            target=DREMIO_REFLECTIONS)]


if __name__ == '__main__':
    ozymandias_obj = Ozymandias(None, None)# If your Watchman uses an event or context, please replace “None” with the appropriate replacement.
    results = ozymandias_obj.monitor()
    for result in results:
        print(result.to_dict())
    # If you want to test the email alerts, you will need to add the code below.
    from watchmen.common.result_svc import ResultSvc
    result_svc = ResultSvc(results)
    result_svc.send_alert()
    print(result_svc.create_lambda_message)

