"""
csv module including functions for csv parsing
"""


def csv_string_to_dict(csv_content_str: str):
    dict_list = []
    row_list = csv_content_str.split('\n')
    key_list = row_list.pop(0).split(',')
    for row in row_list:
        value_list = row.split(',')
        cohesive_dict = dict(zip(key_list, value_list))
        dict_list.append(cohesive_dict)
    return dict_list
