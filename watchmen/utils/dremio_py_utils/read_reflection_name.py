import json


def get_reflection_names(filename):
    with open(filename) as f:
        elements = json.load(f)
        for element in elements['data']:
            print(element['id'], " : " + element['name'])


get_reflection_names('reflections-list-dev.json')
