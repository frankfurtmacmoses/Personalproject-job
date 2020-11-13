from watchmen.config import settings

SNS = {
  "Cyber-Intel Endpoints": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:405093580753:Watchmen_Test"
  },
  "Domain Counts Metrics": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.watchmentest")
  },
  "DomainTools Email": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:405093580753:Watchmen_Test"
  },
  "DomainTools Pager": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:405093580753:Watchmen_Test"
  },
  "DS Summaries": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.watchmentest")
  },
  "EMR Cluster Status": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:405093580753:Watchmen_Test"
  },
  "Farsight Data": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:405093580753:Watchmen_Test"
  },
  "ForeverMail": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:405093580753:Watchmen_Test"
  },
  "Generic Quota Email": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:405093580753:Watchmen_Test"
  },
  "Georgia Tech S3": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.watchmentest")
  },
  "Lookalike2 Algorithm S3": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:405093580753:Watchmen_Test"
  },
  "Metrics and KPI": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:405093580753:Watchmen_Test"
  },
  "Newly Observed Data": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:405093580753:Watchmen_Test"
  },
  "Pager Duty": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:405093580753:Watchmen_Test"
  },
  "Reaper Feeds": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:405093580753:Watchmen_Test"
  },
  "Reaper Metrics": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:405093580753:Watchmen_Test"
  },
  "Slowdrip Metrics": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:405093580753:Watchmen_Test"
  },
  "Smartlisting": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.watchmentest")
  },
  "VirusTotal Email": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:405093580753:Watchmen_Test"
  },
  "VirusTotal Pager": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:405093580753:Watchmen_Test"
  },
  "Generic S3 atg": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.watchmentest")
  },
  "Ozone .com Data": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:488906355115:Watchmen_Test"
  },
  "Generic S3 saas": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:405093580753:Watchmen_Test"
  },
  "Poseidon DNS Data": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:405093580753:Watchmen_Test"
  },
  "Poseidon Northstar DNS Data": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:405093580753:Watchmen_Test"
  },
  "zVelo Data Monitor": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:488906355115:Watchmen_Test"
  },
  "Generic S3 cyberintel": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:488906355115:Watchmen_Test"
  }
}
