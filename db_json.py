import os
import json
from common import Task

def get_json(json_path):
    if not os.path.exists(json_path):
        set_json(json_path, dict())
    with open(json_path,'r') as fin:
        a = json.load(fin)
    a = {
        int(k): Task(**a[k]) for k in a
    }
    return a
def set_json(json_path, tasks):
    with open(json_path,'w') as fout:
        json.dump({
            k: tasks[k].dict() for k in tasks
        }, fout, indent=4, sort_keys=True)
