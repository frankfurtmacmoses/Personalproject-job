"""
# main

@author: Deemanth
@email: dhl@infoblox.com
@created: 2020-08-24

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
from watchmen.process.rorschach import Rorschach


def start_rorschach_watcher(event, context):
    """
    Start the rorschach watcher for S3 data in cyberintel.
    :return: The context that the code is being run in.
    """
    rorschach = Rorschach(event, context)
    results = rorschach.monitor()
    result_svc = ResultSvc(results)
    result_svc.send_alert()
    result_svc.save_results(results)
    return result_svc.create_lambda_message()
