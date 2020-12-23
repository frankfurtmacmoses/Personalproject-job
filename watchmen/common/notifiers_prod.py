from watchmen.config import settings

SNS = {
  "Cyber-Intel Endpoints": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:405093580753:Sockeye"
  },
  "Domain Counts Metrics": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.domaincountsmetrics")
  },
  "DomainTools Email": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:405093580753:DomainTools_Quota_Email"
  },
  "DomainTools Pager": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:405093580753:DomainTools_Quota_Pager"
  },
  "DS Summaries": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.dssummaries")
  },
  "EMR Cluster Status": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:405093580753:EMR_Clusters"
  },
  "Farsight Data": {
    "notifier": "SnsNotifier",
    "sns": settings('sns.farsightdata')
  },
  "ForeverMail": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:405093580753:cyberintel-malspam-prod"
  },
  "Generic Quota Email": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:405093580753:Generic_Quota_Email"
  },
  "Georgia Tech S3": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.georgiatechpdns")
  },
  "Lookalike2 Algorithm S3": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:405093580753:cyberintel-lookalike-s3"
  },
  "Mercator Data - RZ": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.datalakezonemonitors")
  },
  "Metrics and KPI": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:405093580753:Metrics_and_KPI"
  },
  "Newly Observed Data": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.newlyobserveddata")
  },
  "Pager Duty": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:405093580753:PagerDuty"
  },
  "Poseidon DNS Customer Data - RZ": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.datalakezonemonitors")
  },
  "Poseidon DNS Data - CZ": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.datalakezonemonitors")
  },
  "Poseidon DNS Data - LZ": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.datalakezonemonitors")
  },
  "Poseidon Heka Data - CZ": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.datalakezonemonitors")
  },
  "Poseidon Heka Data - LZ": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.datalakezonemonitors")
  },
  "Poseidon DNS Farsight Data - RZ": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.datalakezonemonitors")
  },
  "Prometheus - CZ": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.datalakezonemonitors")
  },
  "Prometheus - LZ": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.datalakezonemonitors")
  },
  "Reaper Feeds": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:405093580753:cyberintel-feeds-prod"
  },
  "Reaper Metrics": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:405093580753:Reaper_Metrics"
  },
  "SaaS Apps Customer Data Phase 1 - CZ": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.datalakezonemonitors")
  },
  "SaaS Apps Customer Data Phase 2 - CZ": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.datalakezonemonitors")
  },
  "SaaS Apps Customer Data Phase 1 - LZ": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.datalakezonemonitors")
  },
  "SaaS Apps Customer Data Phase 2 - LZ": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.datalakezonemonitors")
  },
  "Slowdrip Metrics": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:405093580753:Slowdrip_Metrics"
  },
  "Smartlisting": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.smartlistings3")
  },
  "VirusTotal Email": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:405093580753:VirusTotal_Quota_Email"
  },
  "VirusTotal Pager": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:405093580753:VirusTotal_Quota_Pager"
  },
  "Generic S3 atg": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.generics3atg")
  },
  "Ozone .com Data": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:488906355115:Ozone_COM_Data"
  },
  "Generic S3 saas": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.generics3saas")
  },
  "zVelo Data Monitor": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:488906355115:zvelo_data_monitor"
  },
  "Generic S3 cyberintel": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:488906355115:Generic_S3_cyberintel"
  },
  "Threatwave": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.threatwaves3")
  }
}
