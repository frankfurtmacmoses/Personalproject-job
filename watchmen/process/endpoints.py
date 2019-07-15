"""
# endpoints.py
"""
DATA = [{
    "name": "Sockeye NG",
    "desc": "Sockeye NG about page",
    "path": "http://internal-cyber-socke-1ip36rm488fg7-1930265787.us-east-1.elb.amazonaws.com/",
    "format": "html",
    "routes": [{
        "name": "api",
        "desc": "Sockeye NG API Gateway",
        "path": "v1/info",
        "format": "json",
        "keys": ["dbInfo"],
    }, {
        "name": "data",
        "desc": "Sockeye Data Service API",
        "path": "v1/data/info",
        "format": "json",
        "keys_check": ["dbInfo"],
    }, {
        "name": "hancock",
        "desc": "Sockeye Domains Service API",
        "path": "v1/hancock/info",
        "format": "json",
        "keys_check": ["dbInfo"],
    }, {
        "name": "truth",
        "desc": "ThreatView application and REST API",
        "path": "v1/truth/info",
        "format": "json",
        "keys_check": ["dbInfo"],
    }]
}, {
    "name": "ThreatView (prod)",
    "path": "http://35.168.224.86/threatview",
    "format": "html",
    "routes": [{
        "name": "ThreatView API (prod)",
        "path": "/rest/info",
    }, {
        "name": " ThreatView API spec (test/ci-tac)",
        "path": "/rest/info",
        "format": "text",
        "regx": "ThreatView REST API",
    }]
}, {
    "name": "ThreatView (test/ci-tac)",
    "path": "http://172.18.103.121/threatview",
    "format": "html",
    "routes": [{
        "name": "ThreatView API (test/ci-tac),",
        "path": "/rest/info",
        "format": "json",
        "keys_check": ["dbInfo"],
    }, {
        "name": "ThreatView API spec (test/ci-tac)",
        "path": "/rest/info",
        "format": "text",
        "regx": "ThreatView REST API",
    }]
}, {
    "name": "CyberIntel Services",
    "desc": "A collection of CyberIntel services with scoring, labelling, and search.",
    "path": "http://internal-cyber-applo-15ss4ldsgas1t-1993286264.us-east-1.elb.amazonaws.com/api/",
    "format": "html",
    "routes": [{
        "name": "CyberIntel API Services",
        "path": "info",
        "format": "json"
    }, {
        "name": "Coeus Rules",
        "path": "coeus/rules",
        "format": "json"
    }]
}]
