"""
# main

@author: Daryan Hanshew
@email: dhanshew@infoblox.com
@created: 2018-07-23

Refactored on 2019-11-07:
@author: Michael Garcia
@email: garciam@infoblox.com

Refactored on 2020-06-29:
@author: Laura Peaslee
@email: lpeaslee@infoblox.com


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
from watchmen.process.comedian import Comedian
from watchmen.process.crookshanks import Crookshanks
from watchmen.process.jupiter import Jupiter
from watchmen.process.manhattan import Manhattan
from watchmen.process.metropolis import Metropolis
from watchmen.process.moloch import Moloch
from watchmen.process.mothman import Mothman
from watchmen.common.result_svc import ResultSvc
from watchmen.process.rorschach import Rorschach
from watchmen.process.silhouette import Silhouette
from watchmen.process.slater import Slater
from watchmen.process.spectre import Spectre



def start_rorschach_watcher(event, context):
    """
    Start the rorschach watcher for parquet data in S3.
    :return: The context that the code is being run in.
    """
    rorschach = Rorschach(event, context)
    results = rorschach.monitor()
    result_svc = ResultSvc(results)
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
    result_svc.send_alert()
    return result_svc.create_lambda_message()


def start_crookshanks_watcher(event, context):
    """
    Start the Crookshanks watcher for the Smartlisting Feeds.
    :return: The context that the code is being run in.
    """
    crookshanks = Crookshanks(event, context)
    results = crookshanks.monitor()
    result_svc = ResultSvc(results)
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
    result_svc.send_alert()
    return result_svc.create_lambda_message()


def start_moloch_watcher(event, context):
    """
    Start the moloch watcher for NOH/D feeds.
    :return: The context that the code is being run in.
    """
    moloch = Moloch(event, context)
    results = moloch.monitor()
    result_svc = ResultSvc(results)
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
    result_svc.send_alert()
    return result_svc.create_lambda_message()


def start_slater_watcher(event, context):
    """
    Start the slater watcher for DomainTools API quota.
    :return: The context that the code is being run in.
    """
    slater = Slater(event, context)
    results = slater.monitor()
    result_svc = ResultSvc(results)
    result_svc.send_alert()
    return result_svc.create_lambda_message()


def start_spectre_watcher(event, context):
    """
    Start the spectre watcher for Georgia Tech Feed.
    :return: The context that the code is being run in.
    """
    spectre = Spectre(event, context)
    results = spectre.monitor()
    result_svc = ResultSvc(results)
    result_svc.send_alert()
    return result_svc.create_lambda_message()
