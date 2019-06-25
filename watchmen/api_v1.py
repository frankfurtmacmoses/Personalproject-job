"""
watchmen/api_v1.py
"""
import watchmen.api.v1.info as info


################################################################################
# API info
def getInfo():
    return info.get_info()


def getApiDoc():
    return info.get_api_doc()
