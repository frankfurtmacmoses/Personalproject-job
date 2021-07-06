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
from watchmen.process.bernard import Bernard
from watchmen.process.comedian import Comedian
from watchmen.process.jupiter import Jupiter
from watchmen.process.manhattan import Manhattan
from watchmen.process.metropolis import Metropolis
from watchmen.process.mothman import Mothman
from watchmen.process.niteowl import Niteowl
from watchmen.process.rorschach import Rorschach
from watchmen.process.silhouette import Silhouette


def start_bernard_watcher(event, context):
    """
    Start the Bernard watcher for monitoring EMR clusters.
    :return: The context that the code is being run in.
    """
    bernard = Bernard(event, context)
    results = bernard.monitor()
    result_svc = ResultSvc(results)
    result_svc.save_results(results)
    result_svc.send_alert()
    return result_svc.create_lambda_message()


def start_comedian_watcher(event, context):
    """
    Start the Comedian watcher for the VirusTotal quota.
    :return: The context that the code is being run in.
    """
    comedian = Comedian(event, context)
    results = comedian.monitor()
    result_svc = ResultSvc(results)
    result_svc.save_results(results)
    result_svc.send_alert()
    return result_svc.create_lambda_message()


def start_jupiter_watcher(event, context):
    """
    Start the Jupiter watcher for the CyberIntel endpoints.
    :return: The context that the code is being run in.
    """
    jupiter = Jupiter(event, context)
    results = jupiter.monitor()
    result_svc = ResultSvc(results)
    result_svc.save_results(results)
    result_svc.send_alert()
    return result_svc.create_lambda_message()


def start_manhattan_watcher(event, context):
    """
    Start manhattan watcher to monitor hourly, daily and weekly Reaper feeds.
    :return: The context that the code is being run in.
    """
    manhattan = Manhattan(event, context)
    results = manhattan.monitor()
    result_svc = ResultSvc(results)
    result_svc.save_results(results)
    result_svc.send_alert()
    return result_svc.create_lambda_message()


def start_metropolis_watcher(event, context):
    """
    Start metropolis watcher to monitor metrics and KPI change detection.
    :return: The context that the code is being run in.
    """
    metropolis = Metropolis(event, context)
    results = metropolis.monitor()
    result_svc = ResultSvc(results)
    result_svc.save_results(results)
    result_svc.send_alert()
    return result_svc.create_lambda_message()


def start_mothman_watcher(event, context):
    """
    Start mothman watcher to monitor the Forevermail data in S3.
    :return: The context that the code is being run in.
    """
    mothman = Mothman(event, context)
    results = mothman.monitor()
    result_svc = ResultSvc(results)
    result_svc.save_results(results)
    result_svc.send_alert()
    return result_svc.create_lambda_message()


def start_niteowl_watcher(event, context):
    """
    Start niteowl watcher to monitor changes made in github repos.
    :return: The context that the code is being run in.
    """
    niteowl = Niteowl(event, context)
    results = niteowl.monitor()
    result_svc = ResultSvc(results)
    result_svc.save_results(results)
    result_svc.send_alert()
    return result_svc.create_lambda_message()


def start_rorschach_watcher(event, context):
    """
    Start the rorschach watcher for parquet data in S3.
    :return: The context that the code is being run in.
    """
    rorschach = Rorschach(event, context)
    results = rorschach.monitor()
    result_svc = ResultSvc(results)
    result_svc.save_results(results)
    result_svc.send_alert()
    return result_svc.create_lambda_message()


def start_silhouette_watcher(event, context):
    """
    Start the silhouette watcher for lookalike feed.
    :return: The context that the code is being run in.
    """
    silhouette = Silhouette(event, context)
    results = silhouette.monitor()
    result_svc = ResultSvc(results)
    result_svc.save_results(results)
    result_svc.send_alert()
    return result_svc.create_lambda_message()
