"""
# endpoints.py
"""

data = [{
	"name": "Sockeye NG",
	"desc": "Sockeye NG about page",
	"path": "http://sng.r11.com/",
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
}]
