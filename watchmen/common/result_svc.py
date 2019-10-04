"""
watchmen/common/result_svc.py
This file is the service to process results generated from monitor()
and finds the correct notifiers to send alert messages.
The sns topic for each target is in notifier.json in order for the ResultSvc class to work.
In the future, sns topics will be in the config.yaml.

@author: Jinchi Zhang
@email: jzhang@infoblox.com
"""
# python imports
import json
import os
import traceback

# watchmen imports
from watchmen import const
from watchmen.common.result import Result
from watchmen.config import settings
from watchmen.utils.extension import convert_to_snake_case, get_class
from watchmen.utils.logger import get_logger

ENVIRONMENT = settings("ENVIRONMENT", "test")
FILE_PATH = os.path.dirname(os.path.realpath(__file__))
JSON_FILE_NAME = 'notifiers-{}.json'.format(ENVIRONMENT)
LOGGER = get_logger('watchmen.' + __name__)
NOTIFIER_MODEL_PREFIX = 'watchmen.common.'


class ResultSvc:
    """
    class of ResultSvc
    """

    def __init__(self, result_list: [Result]):
        """
        Constructor of ResultSvc class
        @param result_list: list of Result Object
        """
        self.result_list = result_list

    def create_lambda_message(self):
        """
        Makes the message that is returned to the lambda. The lambda message contains all of the messages
        within the list of result objects.
        :return: Formatted message of all "message" attributes in the list of result objects.
        """
        lambda_message = ""
        for result in self.result_list:
            lambda_message += result.message + "\n"
        return lambda_message

    def _get_notifier(self, result):
        """
        Takes result and generates notifier from the notifier dictionary.
        @param result: <Result> result object
        @return: <Notifier> notifier class
        """
        notifiers_dict = self._load_notifiers()
        target = result.target
        try:
            notifier_class_name = notifiers_dict[target].get("notifier")
            notifier_model_name = convert_to_snake_case(notifier_class_name)
            notifier_model_path = NOTIFIER_MODEL_PREFIX + notifier_model_name
            return get_class(notifier_class_name, notifier_model_path)
        except KeyError:
            LOGGER.error('Target, {}, not found in {}!'.format(target, JSON_FILE_NAME))

    def _get_sns_topic(self, result):
        """
        Takes result and gives sns topic from the notifier dictionary.
        @param result: <Result> result object
        @return: <str> sns topic
        """
        notifiers_dict = self._load_notifiers()
        target = result.target
        try:
            return notifiers_dict[target].get("sns")
        except KeyError:
            LOGGER.error('Target, {}, not found in {}!'.format(target, JSON_FILE_NAME))

    @staticmethod
    def _load_notifiers():
        """
        Load json file from JSON_FILE_NAME.
        @return: <dict> Dictionary of target names mapping to names of notifiers.
        """
        json_path = os.path.join(FILE_PATH, JSON_FILE_NAME)
        with open(json_path, 'r') as file:
            return json.load(file)

    def send_alert(self):
        """
        For each Result in result list, get its notifier and sns topic,
        and then send the alert.
        """
        try:
            for result in self.result_list:
                notifier_class = self._get_notifier(result)
                notifier = notifier_class(result)
                sns_topic = self._get_sns_topic(result)
                notifier.notify(sns_topic)
        except Exception as ex:
            LOGGER.exception(traceback.extract_stack())
            LOGGER.info('*' * const.LENGTH_OF_PRINT_LINE)
            LOGGER.exception('{}: {}'.format(type(ex).__name__, ex))
            return False
        return True
