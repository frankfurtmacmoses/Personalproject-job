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
DEFAULT_SNAPSHOT = None


class Result:
    """
    Result is a class containing watchmen result properties
    """

    def __init__(
            self,
            success: bool,
            state: str,
            subject: str,
            watchman_name: str,
            target: str,
            details: str = DEFAULT_MESSAGE,
            snapshot=DEFAULT_SNAPSHOT,
            disable_notifier=False,
            short_message: str = DEFAULT_MESSAGE,
            dt_created: datetime = None,
            result_id: int = 0):
        """
        Constructor of Result class

        @param watchman_name: <str> "Source of the monitoring event, mainly the name of the Watchman."
        @param target: <str> "The target system or service that has been monitored."
        @param state: <str> "State of the target, must be one of the values: SUCCESS, EXCEPTION, FAILURE, RECOVERED."
        @param success: <bool> "Indicating if the monitoring resulted in SUCCESS state."
        @param subject: <str> "The subject of the notification or alert."
        @param short_message: <str> "A short message of the notification or alert."
        @param details: <str> "Lengthy details of the notification or alert,
        typically the body of an email notification."
        @param snapshot: <dict> "The runtime context (JSON object) of the target system or service."
        @param dt_created: <datetime> "The date/time stamp of this result being created."
        """
        self.details = details
        self.disable_notifier = disable_notifier
        self.short_message = short_message
        self.dt_created = datetime.utcnow() if dt_created is None else dt_created
        self.result_id = result_id
        self.success = success
        self.watchman_name = watchman_name
        self.state = state
        self.subject = subject
        self.target = target
        self.snapshot = snapshot
        LOGGER.info('Generated result: \n%s\n', json.dumps(self.to_dict(), indent=4, sort_keys=True))
        pass

    def to_dict(self):
        """
        Outputs the result properties to a dictionary.
        example dict: {
            "details": "ERROR: 2018/12/gt_mpdns_20181217.zip could not be found in "
                       "cyber-intel/hancock/georgia_tech/! Please check S3 and Georgia "
                       "Tech logs!",
            "disable_notifier": False,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "short_message": "NO MESSAGE",
            "result_id": 0,
            "snapshot": None,
            "watchman_name": "Spectre",
            "state": "FAILURE",
            "subject": "Spectre Georgia Tech data monitor detected a failure!",
            "success": False,
            "target": "Georgia Tech S3",
        }
        @return: <dict> dictionary form of the result
        """
        dict_data = {
            "details": self.details,
            "snapshot": self.snapshot,
            "disable_notifier": self.disable_notifier,
            "short_message": self.short_message,
            "dt_created": self.dt_created.isoformat(),
            "result_id": self.result_id,
            "success": self.success,
            "watchman_name": self.watchman_name,
            "state": self.state,
            "subject": self.subject,
            "target": self.target,
        }
        return dict_data
