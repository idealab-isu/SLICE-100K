import json


eval_json = "/vast/km3888/paired_gcode/translation_data_test.json"

# load json
with open(eval_json, 'r') as f:
    data = json.load(f)

sub_select =data[:500]
json.dump(sub_select, open("/vast/km3888/paired_gcode/translation_data_test_subset.json", 'w'))
