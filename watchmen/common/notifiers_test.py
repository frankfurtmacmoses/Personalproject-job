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
    "sns": settings("sns.watchmentest")
  },
  "Farsight Data": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.watchmentest")
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
  "Mercator Data - RZ": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.watchmentest")
  },
  "Metrics and KPI": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:405093580753:Watchmen_Test"
  },
  "Newly Observed Data": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.watchmentest")
  },
  "Pager Duty": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:405093580753:Watchmen_Test"
  },
  "Poseidon DNS Customer Data - RZ": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.watchmentest")
  },
  "Poseidon DNS Data - CZ": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.watchmentest")
  },
  "Poseidon DNS Data - LZ": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.watchmentest")
  },
  "Poseidon Heka Data - CZ": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.watchmentest")
  },
  "Poseidon Heka Data - LZ": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.watchmentest")
  },
  "Poseidon DNS Farsight Data - RZ": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.watchmentest")
  },
  "Prometheus - CZ": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.watchmentest")
  },
  "Prometheus - LZ": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.watchmentest")
  },
  "Reaper Feeds": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:405093580753:Watchmen_Test"
  },
  "Reaper Metrics": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:405093580753:Watchmen_Test"
  },
  "SaaS Apps Customer Data Phase 1 - CZ": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.watchmentest")
  },
  "SaaS Apps Customer Data Phase 2 - CZ": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.watchmentest")
  },
  "SaaS Apps Customer Data Phase 1 - LZ": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.watchmentest")
  },
  "SaaS Apps Customer Data Phase 2 - LZ": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.watchmentest")
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
    "sns": settings("sns.watchmentest")
  },
  "Poseidon DNS Data": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.watchmentest")
  },
  "Poseidon Northstar DNS Data": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.watchmentest")
  },
  "zVelo Data Monitor": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:488906355115:Watchmen_Test"
  },
  "Generic S3 cyberintel": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:488906355115:Watchmen_Test"
  },
  "Threatwave": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.watchmentest")
  }
}
