"""
# extension module

@author: Jason Zhu
@email: jzhu@infoblox.com
@created: 2017-02-20

"""

import json


class DictEncoder(json.JSONEncoder):
    """
    Default encoder for json.dumps
    """
    def default(self, obj):
        """default encoder"""
        return obj.__dict__


def get_attr(obj, *args):
    """
    Get nested attributes
    """
    data = None
    if obj:
        data = obj
        try:
            for key in args:
                if isinstance(key, basestring):
                    data = data.get(key, None)
                elif isinstance(key, int) and isinstance(data, list):
                    data = data[key] if len(data) >= (key - 1) else None
                else:
                    data = None  # bad key type
                if not data:
                    return None
        except:
            return None
    return data


def get_json(obj, indent=4):
    """
    Get formatted JSON dump string
    """
    return json.dumps(obj, sort_keys=True, indent=indent)
