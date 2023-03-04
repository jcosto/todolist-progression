from common import Task, TASK_ONGOING, TASK_COMPLETED, TASK_DELETED
TASK_COUNTER = 0

TASK_JSON_PATH = "tasks.json"

from db_json import get_json as _get_json, set_json as _set_json
def get_json():
    return _get_json(TASK_JSON_PATH)
def set_json(tasks):
    return _set_json(TASK_JSON_PATH, tasks)

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base
ENGINE = create_engine("sqlite:///tasks.sqlite")
BASE = declarative_base()
class TaskState_DB(BASE):
    __tablename__ = "TaskState"
    id = Column(Integer,primary_key=True)
    name = Column(String(100))
class Task_DB(BASE):
    __tablename__ = "Task"
    id = Column(Integer,primary_key=True)
    name = Column(String(200))
    state = Column(Integer, ForeignKey(TaskState_DB.id))
    def get_task(self):
        return Task(id=self.id, name=self.name, state=self.state)

BASE.metadata.create_all(ENGINE, checkfirst=True)

from sqlalchemy.orm import sessionmaker, Session
SESSION: Session = sessionmaker(bind=ENGINE)()
for name, id in [
    ["ongoing", TASK_ONGOING],
    ["completed", TASK_COMPLETED],
    ["deleted", TASK_DELETED],
]:
    s = SESSION.query(TaskState_DB).filter(TaskState_DB.id==id).one_or_none()
    if not s:
        SESSION.add(TaskState_DB(id=id, name=name))
if SESSION.new:
    SESSION.commit()
        
def set_json_from_db(session: Session):
    tasks = {
        task.id: task.get_task() for task in
        session.query(Task_DB).order_by(Task_DB.id.asc()).all()
    }
    set_json(tasks)

def handle_create_task(session: Session, name):
    """create task, default state TASK_ONGOING"""
    tdb = Task_DB(
        name=name,
        state=session.query(TaskState_DB.id).filter(TaskState_DB.id==TASK_ONGOING),
    )
    session.add(tdb)
    session.commit()
    set_json_from_db(session)
    return tdb.id

def handle_update_task_name(session: Session, task_id, name):
    tdb = handle_read_task(session, task_id)
    tdb.name = name
    session.commit()
    
    set_json_from_db(session)
    
def handle_update_task_state(session: Session, task_id, state: int):
    tdb = handle_read_task(session, task_id)
    tdb.state = state
    session.commit()

    set_json_from_db(session)

def handle_read_task(session: Session, task_id):
    tdb: Task_DB = session.query(Task_DB).filter(Task_DB.id==task_id).one_or_none()
    return tdb

def handle_read_task_all(session: Session):
    for taskdb in session.query(Task_DB).order_by(Task_DB.id.asc()).all():
        yield taskdb.get_task()

def handle_delete_task(session: Session, task_id):
    taskdb = handle_read_task(session, task_id)
    session.delete(taskdb)
    session.commit()
    set_json_from_db(session)

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

def handle_view_tasks(session: Session):
    global TASK_ONGOING
    global TASK_COMPLETED
    global TASK_DELETED
    
    print("------")
    print("YOUR TASKS")
    found_tasks = False
    for t_ in handle_read_task_all(session):
        found_tasks = True
        t: Task = t_
        state_str = " "
        if t.state == TASK_COMPLETED:
            state_str = "/"

        print(f"[{state_str}] {t.id}: {t.name}")
    if not found_tasks:
        print("-- none found --")
    print("------")

import re
pat_create = re.compile(r"create (.*)")
pat_update = re.compile(r"update (\d*) (.*)")
pat_complete = re.compile(r"complete (\d*)")
pat_ongoing = re.compile(r"ongoing (\d*)")
pat_delete = re.compile(r"delete (\d*)")
def loop(session: Session):
    print("### CLI IN-MEMORY TO-TO LIST ###")
    print("##   To-do's are persistent! It's in a file   ##")
    handle_view_tasks(session)
    while True:
        c = input("enter command: ")
        if c.lower().startswith("help"):
            handle_help()
        elif c.lower().startswith("exit"):
            break
        elif c.lower().startswith("view"):
            handle_view_tasks(session)
        elif not pat_create.search(c) is None:
            m = pat_create.search(c)
            name = m.groups()[0]
            task_id = handle_create_task(session, name)
            handle_read_task(session, task_id)
            print(f"created task {task_id}: {name}")
            handle_view_tasks(session)
        elif not pat_update.search(c) is None:
            m = pat_update.search(c)
            task_id, name = m.groups()
            task_id = int(task_id)
            handle_update_task_name(session, task_id, name)
            print(f"updated task {task_id}: {name}")
            handle_view_tasks(session)
        elif not pat_complete.search(c) is None:
            m = pat_complete.search(c)
            task_id = int(m.groups()[0])
            handle_update_task_state(session, task_id, TASK_COMPLETED)
            print(f"completed task {task_id}")
            handle_view_tasks(session)
        elif not pat_ongoing.search(c) is None:
            m = pat_ongoing.search(c)
            task_id = int(m.groups()[0])
            handle_update_task_state(session, task_id, TASK_ONGOING)
            print(f"ongoing task {task_id}")
            handle_view_tasks(session)
        elif not pat_delete.search(c) is None:
            m = pat_delete.search(c)
            task_id = int(m.groups()[0])
            handle_delete_task(session, task_id)
            print(f"deleted task {task_id}")
            handle_view_tasks(session)
        else:
            print("unexpected command")
            handle_help()



if __name__ == "__main__":
    loop(SESSION)