from watchmen.config import settings

SNS = {
  "Cyber-Intel Endpoints": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.sockeye")
  },
  "Domain Counts Metrics": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.domaincountsmetrics")
  },
  "DomainTools Email": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.domaintoolsquota")
  },
  "DomainTools Pager": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.domaintoolsquotapager")
  },
  "DS Summaries": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.dssummaries")
  },
  "EMR Cluster Status": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.emrclusterstatus")
  },
  "Farsight Data": {
    "notifier": "SnsNotifier",
    "sns": settings('sns.farsightdata')
  },
  "ForeverMail": {
    "notifier": "SnsNotifier",
    "sns": settings('sns.forevermail')
  },
  "Generic Quota Email": {
    "notifier": "SnsNotifier",
    "sns": settings('sns.genericquota')
  },
  "Georgia Tech S3": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.georgiatechpdns")
  },
  "Lookalike2 Algorithm S3": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.lookalike2algorithms3")
  },
  "Mercator Data - RZ": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.datalakezonemonitors")
  },
  "Metrics and KPI": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.metricsandkpi")
  },
  "Newly Observed Data": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.newlyobserveddata")
  },
  "Pager Duty": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.reaperfeedspager")
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
    "sns": settings("sns.reaperfeeds")
  },
  "Reaper Metrics": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.reapermetrics")
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
    "sns": settings("sns.slowdripmetrics")
  },
  "Smartlisting": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.smartlistings3")
  },
  "VirusTotal Email": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.virustotalquota")
  },
  "VirusTotal Pager": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.virustotalquotapager")
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
