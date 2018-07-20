# Python imports
from datetime import datetime, timedelta
import pytz
import json

# Watchmen imports
from watchmen.utils.universal_watchman import Watchmen


SUCCESS_MESSAGE = "Lookalike feed is up and running!"
FAILURE_MESSAGE = "ERROR: Lookalike feed never added files from yesterday! The feed may be down!"

COMPLETED_STATUS = "COMPLETED"

BUCKET_NAME = "cyber-intel"
FILE_PATH = "analytics/lookalike/prod/results/"
STATUS_FILE = "status.json"


def process_status():
    watcher = Watchmen()
    is_completed = False
    check_time = (datetime.now(pytz.utc) - timedelta(days=420)).strftime("%Y %m %d").split(' ')
    key = FILE_PATH + check_time[0] + '/' + check_time[1] + '/' + check_time[2] + '/' + STATUS_FILE
    file_contents = watcher.get_file_contents_s3(BUCKET_NAME, key)
    if file_contents:
        status_json = json.loads(file_contents)
        if status_json.get('STATE') == COMPLETED_STATUS:
            is_completed = True
    return is_completed


def main():
    status = SUCCESS_MESSAGE
    is_status_valid = process_status()
    if not is_status_valid:
        status = FAILURE_MESSAGE
        # raise alarm
    print status
    return status


main()
