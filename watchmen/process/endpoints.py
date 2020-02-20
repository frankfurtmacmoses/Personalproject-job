"""
# endpoints.py
"""
DATA = [{
    "name": "Sockeye NG",
    "calendar": "disabled",
    "desc": "Sockeye NG about page",
    "path": "http://internal-cyber-socke-1ip36rm488fg7-1930265787.us-east-1.elb.amazonaws.com/",
    "format": "html",
    "routes": [{
        "name": "Sockeye API",
        "calendar": "disabled",
        "desc": "Sockeye NG API Gateway",
        "path": "v1/info",
        "format": "json",
        "keys": ["dbInfo"],
    }, {
        "name": "Sockeye Data",
        "calendar": "disabled",
        "desc": "Sockeye Data Service API",
        "path": "v1/data/info",
        "format": "json",
        "keys_check": ["dbInfo"],
    }, {
        "name": "Hancock",
        "calendar": "disabled",
        "desc": "Sockeye Domains Service API",
        "path": "v1/hancock/info",
        "format": "json",
        "keys_check": ["dbInfo"],
    }, {
        "name": "Sockeye Truth",
        "calendar": "disabled",
        "desc": "ThreatView application and REST API",
        "path": "v1/truth/info",
        "format": "json",
        "keys_check": ["dbInfo"],
    }]
}, {
    "name": "Sockeye NG (test)",
    "calendar": "enabled",
    "desc": "Sockeye NG about page",
    "path": "http://internal-Cyber-Socke-S67QI36DGRPF-1116929769.us-east-1.elb.amazonaws.com/",
    "format": "html",
    "routes": [{
        "name": "Sockeye API (test)",
        "calendar": "enabled",
        "desc": "Sockeye NG API Gateway",
        "path": "v1/info",
        "format": "json",
        "keys": ["dbInfo"],
    }, {
        "name": "Sockeye Data (test)",
        "calendar": "enabled",
        "desc": "Sockeye Data Service API",
        "path": "v1/data/info",
        "format": "json",
        "keys_check": ["dbInfo"],
    }, {
        "name": "Hancock (test)",
        "calendar": "enabled",
        "desc": "Sockeye Domains Service API",
        "path": "v1/hancock/info",
        "format": "json",
        "keys_check": ["dbInfo"],
    }, {
        "name": "Sockeye Truth (test)",
        "calendar": "enabled",
        "desc": "ThreatView application and REST API",
        "path": "v1/truth/info",
        "format": "json",
        "keys_check": ["dbInfo"],
    }]
}, {
    "name": "ThreatView (prod)",
    "calendar": "disabled",
    "path": "http://35.168.224.86/threatview",
    "format": "html",
    "routes": [{
        "name": "ThreatView API (prod)",
        "calendar": "disabled",
        "path": "/rest/info",
    }, {
        "name": "ThreatView API spec (prod)",
        "calendar": "disabled",
        "path": "/rest/info",
        "format": "text",
        "regx": "ThreatView REST API",
    }]
}, {
    "name": "ThreatView (test/ci-tac)",
    "calendar": "enabled",
    "path": "http://172.18.103.121/threatview",
    "format": "html",
    "routes": [{
        "name": "ThreatView API (test/ci-tac),",
        "calendar": "enabled",
        "path": "/rest/info",
        "format": "json",
        "keys_check": ["dbInfo"],
    }, {
        "name": "ThreatView API spec (test/ci-tac)",
        "calendar": "enabled",
        "path": "/rest/info",
        "format": "text",
        "regx": "ThreatView REST API",
    }]
}, {
    "name": "CyberIntel Services",
    "calendar": "disabled",
    "desc": "A collection of CyberIntel services with scoring, labelling, and search.",
    "path": "http://internal-cyber-applo-15ss4ldsgas1t-1993286264.us-east-1.elb.amazonaws.com/api/",
    "format": "html",
    "routes": [{
        "name": "CyberIntel API Services",
        "calendar": "disabled",
        "path": "info",
        "format": "json"
    }, {
        "name": "Coeus Rules",
        "calendar": "disabled",
        "path": "coeus/rules",
        "format": "json"
    }]
}]
