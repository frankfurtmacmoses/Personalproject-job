"""
Created on August 6, 2018

This script is designed to monitor weekly feeds and ensure proper data flow.

@author: Daryan Hanshew
@email: dhanshew@infoblox.com

"""
# Python imports
from logging import getLogger, basicConfig, INFO
# Cyberint imports
from cyberint_watchmen.universal_watchmen import Watchmen
from cyberint_aws.sns_alerts import raise_alarm

LOGGER = getLogger("ManhattanWeekly")
basicConfig(level=INFO)

SUCCESS_MESSAGE = "Weekly feeds are up and running normally!"
FAILURE_MESSAGE = "One or more weekly feeds are down or submitting abnormal amounts of domains!"
SUBJECT_MESSAGE = "Manhattan detected an issue with one or more of weekly feeds being down!"

SUBJECT_EXCEPTION_MESSAGE = "Manhattan watchmen failed due to an exception!"
EXCEPTION_MESSAGE = "Please check logs for more details about exception!"

ERROR_FEEDS = "Failed/Downed feeds: "
ABNORMAL_SUBMISSIONS_MESSAGE = "Abnormal submission amount from these feeds: "

TABLE_NAME = "CyberInt-Reaper-prod-DynamoDbStack-3XBEIHSJPHBT-ReaperMetricsTable-1LHW3I46AEDQJ"
NOT_A_FEED_ERROR = "ERROR: Feed does not exist or is slotted in the wrong module!"

SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:405093580753:cyberintel-feeds-prod"

# IMPORTANT NOTE: This has to run on Friday in order to ensure proper date traversal!
# How it works:
#               Monday: 4
#               Tuesday: 3
#               Wednesday: 2
#               Thursday: 1
#               Friday: 0
#               To check for monday you subtract 4 days from the run day on Friday.
#               IE If the date is 08/10/2018 and I want to check feeds running on Monday
#                  then I subtract 4 days to 08/06/2018 and check the dynamodb metrics table.
FEEDS_TO_CHECK = {
    'c_APT_ure': {'metric_name': 'FQDN', 'min': 250, 'max': 450, 'hour_submitted': '09', 'days_to_subtract': 4}
}


# pylint: disable=unused-argument
def main(event, context):
    """
    main function
    :return: status of all daily feeds
    """
    watcher = Watchmen()
    status = SUCCESS_MESSAGE
    try:
        downed_feeds, submitted_out_of_range_feeds = watcher.process_feeds_metrics(FEEDS_TO_CHECK, TABLE_NAME, 2)
        if downed_feeds or submitted_out_of_range_feeds:
            status = FAILURE_MESSAGE
            message = (
                    status + '\n' + ERROR_FEEDS + str(downed_feeds) + '\n' +
                    ABNORMAL_SUBMISSIONS_MESSAGE + str(submitted_out_of_range_feeds)
            )
            raise_alarm(SNS_TOPIC_ARN, message, SUBJECT_MESSAGE)
    except Exception as ex:
        raise_alarm(SNS_TOPIC_ARN, EXCEPTION_MESSAGE, SUBJECT_EXCEPTION_MESSAGE)
        status = FAILURE_MESSAGE
        LOGGER.error(ex)
    LOGGER.info(status)
    return status
