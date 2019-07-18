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
            source: str,
            target: str,
            details: str = DEFAULT_MESSAGE,
            snapshot=DEFAULT_SNAPSHOT,
            disable_notifier=False,
            message: str = DEFAULT_MESSAGE,
            dt_created: datetime = None,
            dt_updated: datetime = None,
            is_notified=False,
            is_ack=False,
            result_id: int = 0):
        """
        Constructor of Result class

        @param source: <str> "Source of the monitoring event, mainly the name of the Watchman."
        @param target: <str> "The target system or service that has been monitored."
        @param state: <str> "State of the target, must be one of the values: SUCCESS, EXCEPTION, FAILURE, RECOVERED."
        @param success: <bool> "Indicating if the monitoring resulted in SUCCESS state."
        @param subject: <str> "The subject of the notification or alert."
        @param message: <str> "A short message of the notification or alert."
        @param details: <str> "Lengthy details of the notification or alert,
        typically the body of an email notification."
        @param snapshot: <dict> "The runtime context (JSON object) of the target system or service."
        @param dt_created: <datetime> "The date/time stamp of this result being created."
        @param dt_updated: <datetime> "The date/time stamp of this result being updated,
        e.g. notified or acknowledged."
        @param is_notified: <bool> "Indicating if this result has been sent out as a notification."
        @param is_ack: <bool> "Indicating if the result has been seen and acknowledged by the
        recipient of the notification or alert."
        """
        self.details = details
        self.disable_notifier = disable_notifier
        self.message = message
        self.dt_created = datetime.utcnow() if dt_created is None else dt_created
        self.dt_updated = datetime.utcnow() if dt_updated is None else dt_updated
        self.result_id = result_id
        self.success = success
        self.source = source
        self.state = state
        self.subject = subject
        self.target = target
        self.snapshot = snapshot
        self.is_notified = is_notified
        self.is_ack = is_ack
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
            "dt_updated": "2018-12-18T00:00:00+00:00",
            "is_ack": False,
            "is_notified": False,
            "message": "NO MESSAGE",
            "result_id": 0,
            "snapshot": None,
            "source": "Spectre",
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
            "message": self.message,
            "dt_created": self.dt_created.isoformat(),
            "dt_updated": self.dt_updated.isoformat(),
            "result_id": self.result_id,
            "success": self.success,
            "source": self.source,
            "state": self.state,
            "subject": self.subject,
            "target": self.target,
            "is_notified": self.is_notified,
            "is_ack": self.is_ack,
        }
        return dict_data
