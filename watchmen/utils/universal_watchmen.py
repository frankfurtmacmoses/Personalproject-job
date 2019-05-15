"""
Created on July 17, 2018

This module is meant to be used as a helper for other
Watchmen scripts. Most of this class can be utilized
for verifying simple checks in S3.

@author Daryan Hanshew
@email dhanshew@infoblox.com

Refactored on May 15, 2019
@author: Kayla Ramos
@email: kramos@infoblox.com
"""
from watchmen.common.sum_result import SummarizedResult
from watchmen.config import settings
from watchmen.utils.logger import get_logger
from watchmen.utils.sns_alerts import raise_alarm

NOT_IMPLEMENTED_MESSAGE = "Each Watchmen must implement the monitor function!"
RESULTS_TYPE_ERROR = "Results must be a SummarizedResult object!\nLook at watchmen/common/sum_result.py"


class Watchmen(object):
    """
    Generic Watchmen class
    """
    def __init__(self):
        self.logger = get_logger("Universal Watchmen", settings('logging.level', 'INFO'))
        self.universal_topic = "arn:aws:sns:us-east-1:405093580753:Watchmen_Test"

    def monitor(self):
        """
        The method that every watchmen must implement because it is their unique watched subject and watching method
        """
        raise NotImplementedError(NOT_IMPLEMENTED_MESSAGE)

    def notify(self, res_dict, sns_topic, pager_topic=''):
        """
        This method takes care of sending the actual notifications for the Watchmen if one needs to be sent.
        At the moment, the following keys are used:
        success: True/False statement regarding whether or not the check was a success or not
        subject: Subject message for notification
        message: Message body for notification
        pager_message: Pager message if there needs to be a pager notification

        Any other keys will be ignored, so, if other keys are used in other functions,it will not affect the
        notification process.

        NOTE: Notifications will not be sent if success is True

        @param res_dict: SummarizedResult object containing all the information to send the notification
        @param sns_topic: SNS topic to send the notification to
        @param pager_topic: Pager SNS topic to send notification to
        @return: the general status of the Watchmen: success or failure
        """
        if not isinstance(res_dict, SummarizedResult):
            raise TypeError(RESULTS_TYPE_ERROR)

        self.logger.info(res_dict.result)

        # If results are successful, no need to raise an alarm
        success = res_dict.result.get('success')
        if success:
            return res_dict.result.get('message')

        # Results are not successful therefore have to raise alarms
        subject = res_dict.result.get('subject')
        message = res_dict.result.get('message')
        pager_message = res_dict.result.get('pager_message')

        raise_alarm(topic_arn=sns_topic, subject=subject, msg=message)
        if pager_message:
            raise_alarm(topic_arn=settings(pager_topic), subject=subject, msg=pager_message)

        return subject
