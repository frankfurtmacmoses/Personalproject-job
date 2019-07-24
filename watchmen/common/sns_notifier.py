"""
watchmen/common/sns_notifier.py

This class receives Result object and sends e-mail notifications with Amazon SNS by topic ARNs.

@author: Jinchi Zhang
@email: jzhang@infoblox.com
@created: July 3, 2019
"""
from watchmen.common.notifier import Notifier
from watchmen.utils.sns_alerts import raise_alarm
from watchmen.common.result import Result


class SnsNotifier(Notifier):
    """
    This Class sends e-mail notifications with Amazon SNS.
    """

    def __init__(self, result: Result):
        """
        Constructor of class SnsNotifier.

        @param result: <Result> Result object that notifier gets subject and message from.
        """
        self.result = result
        self.subject = str(result.subject)
        self.details = str(result.details)

    def notify(self, topic: str):
        """
        Sends sns alert with the given topic.

        @param topic: <str> the topic arn to be notified.
        """
        if not isinstance(topic, str):
            raise TypeError("Topic arn must be string!")
        raise_alarm(topic_arn=topic, msg=self.details, subject=self.subject)
