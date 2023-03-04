from common import Task, TASK_ONGOING, TASK_COMPLETED, TASK_DELETED
TASK_COUNTER = 0

TASK_JSON_PATH = "tasks.json"

from db_json import get_json as _get_json, set_json as _set_json
def get_json():
    return _get_json(TASK_JSON_PATH)
def set_json(tasks):
    return _set_json(TASK_JSON_PATH, tasks)

def handle_create_task(tasks: dict, name):
    """create task, default state TASK_ONGOING"""
    global TASK_COUNTER
    TASK_COUNTER += 1
    t = Task(name, TASK_ONGOING, TASK_COUNTER)
    tasks[t.id] = t
    set_json(tasks)
    return t.id

def handle_update_task_name(tasks, task_id, name):
    t: Task = tasks[task_id]
    t.name = name
    set_json(tasks)
    
def handle_update_task_state(tasks, task_id, state: int):
    t: Task = tasks[task_id]
    t.state = state
    set_json(tasks)

def handle_read_task(tasks, task_id):
    t: Task = tasks[task_id]
    return t

def handle_read_task_all(tasks):
    for k in tasks:
        yield tasks[k]

def handle_delete_task(tasks: dict, task_id):
    tasks.pop(task_id)
    set_json(tasks)

def handle_help():
    print("""
view: view all tasks
create [name]: create new task
update [id] [new name]: update name for task
complete [id]: update task as completed
ongoing [id]: update task as ongoing
delete [id]: delete task
exit: exit app
            """)

def handle_view_tasks(tasks:dict):
    global TASK_ONGOING
    global TASK_COMPLETED
    global TASK_DELETED
    
    print("------")
    print("YOUR TASKS")
    if not tasks:
        print("-- none found --")
    else:
        for t_ in handle_read_task_all(tasks):
            t: Task = t_
            state_str = " "
            if t.state == TASK_COMPLETED:
                state_str = "/"

            print(f"[{state_str}] {t.id}: {t.name}")
    print("------")

import re
pat_create = re.compile(r"create (.*)")
pat_update = re.compile(r"update (\d*) (.*)")
pat_complete = re.compile(r"complete (\d*)")
pat_ongoing = re.compile(r"ongoing (\d*)")
pat_delete = re.compile(r"delete (\d*)")
def loop(tasks: dict):
    print("### CLI IN-MEMORY TO-TO LIST ###")
    print("##   To-do's are persistent! It's in a file   ##")
    handle_view_tasks(tasks)
    while True:
        c = input("enter command: ")
        if c.lower().startswith("help"):
            handle_help()
        elif c.lower().startswith("exit"):
            break
        elif c.lower().startswith("view"):
            handle_view_tasks(tasks)
        elif not pat_create.search(c) is None:
            m = pat_create.search(c)
            name = m.groups()[0]
            task_id = handle_create_task(tasks, name)
            handle_read_task(tasks, task_id)
            print(f"created task {task_id}: {name}")
            handle_view_tasks(tasks)
        elif not pat_update.search(c) is None:
            m = pat_update.search(c)
            task_id, name = m.groups()
            task_id = int(task_id)
            handle_update_task_name(tasks, task_id, name)
            print(f"updated task {task_id}: {name}")
            handle_view_tasks(tasks)
        elif not pat_complete.search(c) is None:
            m = pat_complete.search(c)
            task_id = int(m.groups()[0])
            handle_update_task_state(tasks, task_id, TASK_COMPLETED)
            print(f"completed task {task_id}")
            handle_view_tasks(tasks)
        elif not pat_ongoing.search(c) is None:
            m = pat_ongoing.search(c)
            task_id = int(m.groups()[0])
            handle_update_task_state(tasks, task_id, TASK_ONGOING)
            print(f"ongoing task {task_id}")
            handle_view_tasks(tasks)
        elif not pat_delete.search(c) is None:
            m = pat_delete.search(c)
            task_id = int(m.groups()[0])
            handle_delete_task(tasks, task_id)
            print(f"deleted task {task_id}")
            handle_view_tasks(tasks)
        else:
            print("unexpected command")
            handle_help()



if __name__ == "__main__":
    loop(get_json())