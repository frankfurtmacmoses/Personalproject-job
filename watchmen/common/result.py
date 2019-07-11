"""
# common/result.py

# author: jzhang@infoblox.com
# 2019-6-27
"""
from datetime import datetime
import json

from watchmen.utils.logger import get_logger

LOGGER = get_logger('watchmen.' + __name__)

DEFAULT_MESSAGE = 'NO MESSAGE'


class Result:
    """
    Result is a class containing watchmen result properties
    """

    def __init__(
            self,
            success: bool,
            state: str,
            subject: str,
            source: str,
            target: str,
            details={},
            disable_notifier=False,
            message=DEFAULT_MESSAGE,
            observed_time: datetime = None,
            result_id: int = 0):
        """
        Constructor of Result class

        @param success: <bool> whether the event that notifier watching succeeded
        @param state: <str> state of the target
        @param subject: <str> subject to be sent for long notification
        @param source: <str> source of information, mainly the name of watchmen
        @param target: <str> name of the target being monitored
        @param details: <dict> details for short notifications
        @param disable_notifier: <bool> whether the notifier should be disabled
        @param message: <str> message for long notification
        @param observed_time: <datetime> time when generated
        @param result_id: <int> id of the result
        """
        self.details = details
        self.disable_notifier = disable_notifier
        self.message = message
        self.observed_time = datetime.utcnow() if observed_time is None else observed_time
        self.result_id = result_id
        self.success = success
        self.source = source
        self.state = state
        self.subject = subject
        self.target = target
        LOGGER.info('Generated result: \n%s\n', json.dumps(self.to_dict(), indent=4, sort_keys=True))
        pass

    def to_dict(self):
        """
        Outputs the result properties to a dictionary.
        example dict: {
            "details": {},
            "disable_notifier": False,
            "message":
                "Error: 2018/12/gt_mpdns_20181217.zip"
                "could not be found in cyber-intel/hancock/georgia_tech/!
                "Please check S3 and Georgia Tech logs!",
            "observed_time": "2018-12-18T00:00:00+00:00",
            "result_id": 0,
            "success": False,
            "source": "Spectre",
            "state": "FAILURE",
            "subject": "Spectre Georgia Tech data monitor detected a failure!",
            "target": "Georgia Tech S3",
        }
        @return: <dict> dictionary form of the result
        """
        dict_data = {
            "details": self.details,
            "disable_notifier": self.disable_notifier,
            "message": self.message,
            "observed_time": self.observed_time.isoformat(),
            "result_id": self.result_id,
            "success": self.success,
            "source": self.source,
            "state": self.state,
            "subject": self.subject,
            "target": self.target,
        }
        return dict_data
