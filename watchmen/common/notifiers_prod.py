from watchmen.config import settings

SNS = {
  "Cyber-Intel Endpoints": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.sockeye")
  },
  "DomainTools Email": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.domaintoolsquota")
  },
  "DomainTools Pager": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.domaintoolsquotapager")
  },
  "EMR Cluster Status": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.emrclusterstatus")
  },
  "Malspam MTA": {
    "notifier": "SnsNotifier",
    "sns": settings('sns.forevermail')
  },
  "Generic Quota Email": {
    "notifier": "SnsNotifier",
    "sns": settings('sns.genericquota')
  },
  "Lookalike2 Algorithm S3": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.lookalike2algorithms3")
  },
  "Mercator Data - RZ": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.datalakezonemonitors")
  },
  "Mitre Cti": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.mitrecti")
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
  "Generic Github atg": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.genericgithubatg")
  },
  "Generic S3 cyberintel": {
    "notifier": "SnsNotifier",
    "sns": "arn:aws:sns:us-east-1:488906355115:Generic_S3_cyberintel"
  },
  "Threatwave": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.threatwaves3")
  },
  "Psl": {
      "notifier": "SnsNotifier",
      "sns": settings("sns.psls3")
  },
  "Maxmind": {
    "notifier": "SnsNotifier",
    "sns": settings("sns.maxminds3")
  }
}
