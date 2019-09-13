"""
# main

@author: Daryan Hanshew
@email: dhanshew@infoblox.com
@created: 2018-07-23

@note: this module includes entry points for AWS lambda functions.
       the Lambda functions are configured by cron schedules; however
       it can be triggered by e.g. RDS and/or S3 event.

       - on S3 trigger, the handler will receive an event (JSON object) like
{
  "Records": [{
    "eventVersion": "2.0",
    "eventSource": "aws:s3",
    "awsRegion": "us-west-2",
    "eventTime": "2017-02-28T23:06:30.510Z",
    "eventName": "ObjectCreated:Copy",
    "userIdentity": {
      "principalId": "AWS:AIDAJYYGM2ZVXGKY7QCVY"
    },
    "s3": {
      "s3SchemaVersion": "1.0",
      "configurationId": "5561c695-8167-4ccc-87e2-6aeb52e34d64",
      "bucket": {
        "name": "cyber-intel-us-west-2",
        "ownerIdentity": {
          "principalId": "A1XGF3ZLQFRC0N"
        },
        "arn": "arn:aws:s3:::cyber-intel-us-west-2"
      },
      "object": {
        "key": "hancock/tests/part-00007-5173782a-ebeb-43ec-bedf-b48743819474.json",
        "size": 85,
        "versionId": "5nJyQiYQUlkflwKj1UKrl_hIHsXdi71z",
        "sequencer": "0058B602766EFD8566"
      }
    }
  }]
}
"""
from watchmen.common.result_svc import ResultSvc
from watchmen.process import jupiter, manhattan, moloch, ozymandias, rorschach, silhouette, spectre
from watchmen.process.metropolis import Metropolis


def start_jupiter_watcher(event, context):
    """
        Start the Jupiter watcher for the Sockeye endpoints.
        :return: The context that the code is being run in.
        """
    return jupiter.main(event, context)


def start_manhattan_watcher(event, context):
    """
    Start manhattan watcher to monitor hourly, daily and weekly Reaper feeds.
    :return: The context that the code is being run in.
    """
    return manhattan.main(event, context)


def start_metropolis_watcher(event, context):
    """
    Start metropolis watcher to monitor metrics and KPI change detection.
    :return: The context that the code is being run in.
    """
    metropolis = Metropolis(event, context)
    results = metropolis.monitor()
    result_svc = ResultSvc(results)
    result_svc.send_alert()


def start_moloch_watcher(event, context):
    """
    Start the moloch watcher for NOH/D feeds.
    :return: The context that the code is being run in.
    """
    return moloch.main(event, context)


def start_ozymandias_watcher(event, context):
    """
    Start the ozymandias watcher for Neustar data.
    :return: The context that the code is being run in.
    """
    return ozymandias.main(event, context)


def start_rorschach_watcher(event, context):
    """
    Start the rorschach watcher for parquet data in S3.
    :return: The context that the code is being run in.
    """
    return rorschach.main(event, context)


def start_silhouette_watcher(event, context):
    """
    Start the silhouette watcher for lookalike feed.
    :return: The context that the code is being run in.
    """
    return silhouette.main(event, context)


def start_spectre_watcher(event, context):
    """
    Start the spectre watcher for Georgia Tech Feed.
    :return: The context that the code is being run in.
    """
    return spectre.main(event, context)
