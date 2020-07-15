"""
Created on November 27, 2019

This Watchman monitors the VirusTotal API to ensure that our team does not go over our monthly quota limit. This
Watchman will send both email and SMS alerts if the used-to-allowed ratio crosses its threshold.

@author: Michael Garcia
@email: garciam@infoblox.com
"""

import hashlib
import hmac
import os
import requests
import traceback
import yaml

from datetime import datetime
from watchmen import const
from watchmen import messages
from watchmen.common.result_svc import Result
from watchmen.common.watchman import Watchman
from watchmen.config import settings


ERROR = "ERROR"
CONFIG_NAME = 'api_targets.yaml'
CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), CONFIG_NAME)

GENERIC = 'Generic Quota'
MESSAGES = messages.COMEDIAN
TARGET_EMAIL = "{} Email"
TARGET_PAGER = "{} Pager"


class Comedian(Watchman):
    # pylint: disable=unused-argument
    def __init__(self, event, context):
        super().__init__()

    def monitor(self) -> [Result]:
        api_targets, tb = self._load_config()
        if tb or api_targets is None:
            details = MESSAGES.get("exception_config_details").format(tb)
            result = self._create_generic_result(False, True, details)
            return [result]

        targets_quota_info = self._get_targets_quota_info(api_targets)
        if not targets_quota_info:
            details = MESSAGES.get("exception_api_details")
            result = self._create_generic_result(False, True, details)
            return [result]

        targets_check_info, tb = self._check_api_quotas(targets_quota_info)
        if tb:
            details = MESSAGES.get("quota_exception_details").format(tb)
            result = self._create_generic_result(False, True, details)
            return [result]

        result_parameters, failure_in_results, exception_in_results = self._create_result_parameters(targets_check_info)

        return self._create_results(result_parameters,  failure_in_results, exception_in_results)

    def _build_header(self, api_config, timestamp=None):
        """
        Builds the header for a get request. The config tags must match the header tags.
        :param api_config: The api configuration information
        :param timestamp: The current timestamp
        :return: A Dictionary of the header information
        """
        try:
            head = api_config['head']
            header = {}

            for tag in head:
                if head[tag] == 'apikey':
                    header.update({tag: self._get_api_key(api_config)})
                    continue

                if head[tag] == 'timestamp':
                    header.update({tag: timestamp})
                    continue

                if tag == 'signature':
                    tag_name = tag
                    if 'api_key' in head[tag]:
                        key = self._get_api_key(api_config)
                    else:
                        key = head[tag]['key']

                    if 'tag' in head[tag]:
                        tag_name = head[tag]['tag']

                    signature = self._create_signature(key, head['signature']['msg'], timestamp, api_config['hash'],
                                                       api_config['encode'])

                    header.update({tag_name: signature})
                    continue

                header.update({tag: api_config['head'][tag]})

            return header, None
        except Exception as ex:
            self.logger.error("ERROR Creating HEADER!")
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception("{}: {}".format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            return None, tb

    def _build_url(self, api_config, timestamp=None):
        """
        Builds the url for a get request.
        :param api_config: The api configuration information
        :param timestamp: The current timestamp
        :return: The Url as a string
        """
        try:
            url = api_config['url']
            if 'url_arguments' not in api_config.keys():
                return url, None

            url_arguments = api_config['url_arguments']
            kwargs = {}

            for arg_key, arg_val in url_arguments.items():
                if arg_key == 'timestamp':
                    kwargs.update({'timestamp': timestamp})
                    continue

                if arg_key == 'signature':
                    if 'api_key' in url_arguments['signature']:
                        key = self._get_api_key(api_config)

                    else:
                        key = url_arguments['signature']['key']

                    signature = self._create_signature(key, url_arguments['signature']['msg'], timestamp,
                                                       api_config['hash'],
                                                       api_config['encode'])

                    kwargs.update({'signature': signature})
                    continue

                kwargs.update({arg_key: arg_val})

            return url.format(**kwargs), None
        except Exception as ex:
            self.logger.error("ERROR Creating URL!")
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception("{}: {}".format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            return None, tb

    def _calculate_threshold(self, api_target):
        """
        Calculates the used-to-allowed quota threshold based on the current day of the month. The threshold is
        calculated by starting at the api-specified start_threshold(found in api_targets.yaml) for the first day of the
        month, and adding the api-specified increment to the threshold each day.
        :param: The api to calculate the threshold for
        :return: The current used-to-allowed quota threshold.
        """
        try:
            day = datetime.utcnow().day
            threshold = (api_target['threshold_start'] + (day * api_target['increment'])) / 100
            return threshold, None
        except Exception as ex:
            self.logger.error("ERROR With Threshold Values!")
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception("{}: {}".format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            return None, tb

    def _check_api_quotas(self, target_quota_info):
        """
        Checks the quotas for each API within target_quota_info to ensure that the values are within the
        current threshold. If any quotas listed are above their threshold, an SNS alert will be sent.
        :param target_quota_info: Dictionary of each API's formatted quota usage information. Each quota includes
        Used and Allowed values, which is compared against their API's threshold.
        :return: A list containing the results of the quota check for each API as well as a combined result.
        """
        check_results = {}
        try:
            for api_name in target_quota_info:
                success = True
                api_details = ''

                #checks to see if there is a traceback instead of target quota data
                if isinstance(target_quota_info.get(api_name), str):
                    tb = target_quota_info.get(api_name)
                    api_details = MESSAGES.get("exception_details").format(api_name, tb)
                    success = None
                else:

                    threshold, tb = self._calculate_threshold(target_quota_info[api_name])
                    if tb:
                        api_details = MESSAGES.get("exception_details").format(api_name, tb)
                        success = None

                    else:
                        target_quota_list = target_quota_info[api_name]['quotas']
                        for quota in target_quota_list:

                            used = target_quota_list[quota]["used"]
                            allowed = target_quota_list[quota]["allowed"]

                            if used is None or not allowed:
                                success = None
                                api_details += MESSAGES.get('exception_quota_details').format(quota)
                                continue

                            used = int(used)
                            allowed = int(allowed)
                            check_quota_results, check_success = self._check_threshold(threshold, used, allowed, quota)
                            api_details += check_quota_results

                            success = check_success

                    api_details = "\n\n{}\n{}".format(api_name, api_details)

                check_results.update(
                    {
                        api_name:
                            {
                                'success': success,
                                'api_details': api_details,
                                'snapshot': target_quota_info[api_name]
                            }
                    })

            return check_results, None
        except Exception as ex:
            self.logger.info("ERROR Checking API Quotas")
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception("{}: {}".format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            return None, tb

    def _check_threshold(self, threshold, used, allowed, quota_name):
        """
        Checks the used statistic against its corresponding threshold. Returns the result as a message
        :param threshold: The percentage used should not go beyond
        :param used: The current usage of the specified quota
        :param allowed: The allowed amount of usage for the quota
        :param quota_name: The quota name
        """
        # Multiplying `used` by 1.0 to prevent the decimal being truncated by Python.
        quota_usage = (used * 1.0) / allowed
        if quota_usage >= threshold:
            exceeded_details = MESSAGES.get("quota_exceeded") \
                .format(quota_name, threshold * 100, quota_usage * 100, used, allowed)
            return exceeded_details, False
        return '', True

    def _create_data_template(self, api):
        """
        Creates a template dictionary to enter quota information into
        :params api: api config info
        :return: dictionary with threshold and increment information and an empty section for quota information
        """
        try:
            formatted_data = {
                'threshold_start': api['threshold_start'],
                'increment': api['increment'],
                'quotas': {}}
            return formatted_data, None
        except Exception as ex:
            self.logger.error("ERROR retrieving threshold information from Config")
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception("{}: {}".format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            return None, tb

    def _create_generic_result(self, failure, exception, details):
        """
        Method to create the generic result object
        :param failure: Boolean value to indicate a failure occurred
        :param exception: Boolean value to indicate an exception occurred
        :param details: String of all api details
        """
        if exception:
            disable_notifier = False
            short_message = MESSAGES.get("exception_short_message")
            state = Watchman.STATE.get("exception")
            subject = MESSAGES.get("exception_subject")
            success = False

        elif failure:
            disable_notifier = False
            short_message = MESSAGES.get("failure_short_message")
            state = Watchman.STATE.get("failure")
            subject = MESSAGES.get("failure_subject")
            success = False

        else:
            disable_notifier = True
            short_message = MESSAGES.get("success_short_message")
            state = Watchman.STATE.get("success")
            subject = MESSAGES.get("success_subject")
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
            target=TARGET_EMAIL.format(GENERIC),
        )

    def _create_results(self, parameters, failure_in_results, exception_in_results):
        """
        Takes in a list of parameters describing the state of the api quotas that have been checked and creates a list
        of result objects as well as a generic result object which combines all parameters
        :param parameters: list of parameters describing the state of the api quotas
        :param failure_in_results: Boolean for if there was a failure
        :param exception_in_results: Boolean for if there was an exception
        :return: List of results objects for each api as well as a generic result object
        """
        results = []
        generic_details = ''

        for param in parameters:
            generic_details += param.get("details") + "\n" + const.MESSAGE_SEPARATOR

            if param.get("api_name") is not ERROR:

                email_result = Result(
                    details=param.get("details"),
                    disable_notifier=param.get("disable_notifier"),
                    short_message=param.get("short_message"),
                    snapshot=param.get("snapshot"),
                    watchman_name=self.watchman_name,
                    state=param.get("state"),
                    subject=param.get("subject"),
                    success=param.get("success"),
                    target=TARGET_EMAIL.format(param.get("api_name")),
                )
                pager_result = Result(
                    details=param.get("details"),
                    disable_notifier=param.get("disable_notifier"),
                    short_message=param.get("short_message"),
                    snapshot=param.get("snapshot"),
                    watchman_name=self.watchman_name,
                    state=param.get("state"),
                    subject=param.get("subject"),
                    success=param.get("success"),
                    target=TARGET_PAGER.format(param.get("api_name")),
                )

                results.extend((email_result, pager_result))

        generic_result = self._create_generic_result(failure_in_results, exception_in_results, generic_details)
        results.append(generic_result)
        return results

    def _create_result_parameters(self, targets_check_info):
        """
        Creates the Result object parameters based on the success of the quota checks.
        :param targets_check_info: A dictionary of success, details, snapshots for each target
        :return: A dictionary containing "details", "disable_notifier", "short_message", "snapshot", "state", "subject",
        and "success".
        """

        parameter_chart = {
            None: {
                "disable_notifier": False,
                "short_message": MESSAGES.get("exception_short_message"),
                "state": Watchman.STATE.get("exception"),
                "subject": MESSAGES.get("exception_subject"),
                "success": False,
            },
            True: {
                "disable_notifier": True,
                "state": Watchman.STATE.get("success"),
                "success": True,
            },
            False: {
                "disable_notifier": False,
                "state": Watchman.STATE.get("failure"),
                "success": False,
            },
        }

        parameters = []
        exception_occurred = False
        failure_occurred = False
        for api_name, target_check in targets_check_info.items():
            api_success = target_check.get("success")
            target_parameters = parameter_chart.get(api_success).copy()

            if api_success is None:
                exception_occurred = True
                target_parameters.update({
                    "details": target_check.get("api_details"),
                    "snapshot": target_check.get("snapshot"),
                    "api_name": api_name,
                })

            elif not api_success:
                failure_occurred = True
                target_parameters.update({
                    "details": target_check.get("api_details"),
                    "short_message": MESSAGES.get("failure_short_message_single").format(api_name),
                    "snapshot": target_check.get("snapshot"),
                    "subject": MESSAGES.get("failure_subject_single").format(api_name),
                    "api_name": api_name,
                })

            else:
                target_parameters.update({
                    "details": MESSAGES.get("success_details_single").format(api_name),
                    "short_message": MESSAGES.get("success_short_message_single").format(api_name),
                    "snapshot": target_check.get("snapshot"),
                    "subject": MESSAGES.get("success_subject_single").format(api_name),
                    "api_name": api_name,
                })

            parameters.append(target_parameters)

        return parameters, failure_occurred, exception_occurred

    def _create_signature(self, sign_key, msg, timestamp, hash_alg, encode):
        """
        Creates a signature by hashing a key and message together with the specified hashing algorithm
        :param sign_key: The signatures key
        :param msg: The signature message. It may be a combination of arguments
        :param timestamp: The timestamp of the request
        :param hash_alg: The algorithm to hash the other arguments by. Currently only supports: sha1, sha256
        :param encode: What to encode the arguments as.
        """
        params_builder = []

        for key in msg:
            if key == 'timestamp':
                params_builder.append(timestamp)
            else:
                params_builder.append(msg[key])

        params = ''.join(params_builder)

        if hash_alg == 'sha1':
            return hmac.new(sign_key.encode(encode), params.encode(encode), digestmod=hashlib.sha1).hexdigest()

        if hash_alg == 'sha256':
            return hmac.new(sign_key.encode(encode), params.encode(encode), digestmod=hashlib.sha256).hexdigest()

        return None

    def _get_api_info(self, api):
        """
        Retrieves the api-specific function and returns formatted api quota details based on the api name. Function
        naming convention is _get_[api_name]_data(). It then passes the config details to the api-specific function
        :param api: The config details for the specific api found in api_targets_{}.yaml
        :return: Dictionary of formatted information returned from the api-specific function
        """
        try:
            source_function = getattr(self, '_get_{}_data'.format(api['target_name'].lower()))
            return source_function(api)
        except Exception as ex:
            self.logger.error("ERROR retrieving source {} function!".format(api['target_name']))
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception("{}: {}".format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            return None, tb

    def _get_api_key(self, api):
        """
        Gets and decodes the api key from config.yaml file. Naming is [target_name]_api_key in config.yaml
        :param api: Config details for the specific api
        :return: decoded api key
        """
        path = 'comedian.{}_api_key'.format(api['target_name'].lower())
        return settings(path)

    def _get_domaintools_data(self, api):
        """
        Performs the DomainTools get request and formats the response
        :param api: the DomainTools api config information
        :return: A specially formatted dictionary of quota information and quota limits. Example:
            {
            'threshold_start': 26,
            'increment': 2,
            'quotas': {'api_requests_monthly': {'used': 311, 'allowed': 1000000000},
                       'intelligence_downloads_monthly': {'used': 0, 'allowed': 300},
                       'intelligence_hunting_rules': {'used': 20, 'allowed': 20000},
                       'intelligence_retrohunt_jobs_monthly': {'used': 0, 'allowed': 5},
                       'intelligence_searches_monthly': {'used': 21, 'allowed': 300}}}
            }
        """
        timestamp = datetime.utcnow().strftime(api['timestamp'])

        url, tb = self._build_url(api, timestamp)
        if tb:
            return None, tb

        try:
            domaintools_response = requests.get(url).json()
            domaintools_quotas = domaintools_response['response']['products']
        except Exception as ex:
            self.logger.info("ERROR in DomainTools GET Request")
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception("{}: {}".format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            return None, tb

        formatted_data, tb = self._create_data_template(api)
        if tb:
            return None, tb

        api_quotas = api['quotas']
        for quota in domaintools_quotas:
            if quota['id'] in api_quotas:
                formatted_data['quotas'].update({quota['id']:
                                                {
                                                    'used': quota['usage']['month'],
                                                    'allowed': quota['per_month_limit']
                                                }})
        return formatted_data, None

    def _get_targets_quota_info(self, api_targets):
        """
        For each API specified in the config file it will call the API-specific method which will provide its current
        quota information.
        :param api_targets: All API targets in the config file
        :return: A Dictionary of quota usage and quota limits for each API, as well as a traceback if an exception
        occurs .
        Example Dictionary:
        {
             'DomainTools': {
                'threshold_start': 26,
                'increment': 2,
                'quotas': {
                    'api_requests_monthly': {'used': 311, 'allowed': 1000000000},
                    'intelligence_downloads_monthly': {'used': 0, 'allowed': 300},
                    'intelligence_hunting_rules': {'used': 20, 'allowed': 20000},
                    'intelligence_retrohunt_jobs_monthly': {'used': 0, 'allowed': 5},
                    'intelligence_searches_monthly': {'used': 21, 'allowed': 300}}}
            },
             'VirusTotal': {
                'threshold_start': 26,
                'increment': 2,
                'quotas': {
                    'api_requests_monthly': {'used': 311, 'allowed': 1000000000},
                    'intelligence_downloads_monthly': {'used': 0, 'allowed': 300},
                    'intelligence_hunting_rules': {'used': 20, 'allowed': 20000},
                    'intelligence_retrohunt_jobs_monthly': {'used': 0, 'allowed': 5},
                    'intelligence_searches_monthly': {'used': 21, 'allowed': 300}}}
             }
        }

        """

        api_target_quotas = {}
        for api in api_targets:
            try:
                self.logger.info("Reading: {}".format(api['target_name']))
                info, tb = self._get_api_info(api)
                if tb:
                    api_target_quotas.update({api['target_name']: tb})
                    continue

                api_target_quotas.update({api['target_name']: info})
            except Exception as ex:
                self.logger.info("ERROR Retrieving quota information!")
                self.logger.info(const.MESSAGE_SEPARATOR)
                self.logger.exception("{}: {}".format(type(ex).__name__, ex))
                tb = traceback.format_exc()
                api_target_quotas.update({ERROR: tb})

        return api_target_quotas

    def _get_virustotal_data(self, api):
        """
        Performs the VirusTotal get request and formats the response
        :param api: the VirusTotal api config information
        :return: A specially formatted dictionary of quota information and quota limits. Example:
            {
            'threshold_start': 26,
            'increment': 2,
            'quotas': {'api_requests_monthly': {'used': 311, 'allowed': 1000000000},
                      'intelligence_downloads_monthly': {'used': 0, 'allowed': 300},
                      'intelligence_hunting_rules': {'used': 20, 'allowed': 20000},
                      'intelligence_retrohunt_jobs_monthly': {'used': 0, 'allowed': 5},
                      'intelligence_searches_monthly': {'used': 21, 'allowed': 300}}}
            }
        """
        header, tb = self._build_header(api)
        if tb:
            return None, tb

        url, tb = self._build_url(api)
        if tb:
            return None, tb

        try:
            virustotal_api_response = requests.get(url=url, headers=header).json()
            virustotal_quotas = virustotal_api_response["data"]["attributes"]["quotas"]
        except Exception as ex:
            self.logger.info("ERROR in VirusTotal GET Request")
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception("{}: {}".format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            return None, tb

        formatted_data, tb = self._create_data_template(api)
        if tb:
            return None, tb

        api_quotas = api['quotas']
        for quota in virustotal_quotas:
            if quota in api_quotas:
                formatted_data['quotas'].update({quota:
                                                {
                                                    'used': virustotal_quotas[quota]['used'],
                                                    'allowed': virustotal_quotas[quota]['allowed']
                                                }})
        return formatted_data, None

    def _load_config(self):
        """
        Loads the config file, api_targets.yaml
        :returns: List of config details for each api
        """
        try:
            with open(CONFIG_PATH) as f:
                api_targets = yaml.load(f, Loader=yaml.FullLoader)
            return api_targets, None
        except Exception as ex:
            self.logger.error("ERROR Loading Config!")
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception("{}: {}".format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            return None, tb
