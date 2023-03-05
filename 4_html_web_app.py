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

from sqlalchemy.orm import sessionmaker, Session

def setup_db_data(session: Session):
    for name, id in [
        ["ongoing", TASK_ONGOING],
        ["completed", TASK_COMPLETED],
        ["deleted", TASK_DELETED],
    ]:
        s = session.query(TaskState_DB).filter(TaskState_DB.id==id).one_or_none()
        if not s:
            session.add(TaskState_DB(id=id, name=name))
    if session.new:
        session.commit()
        
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
    print(tdb.get_task().dict())
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

from flask import Flask, render_template_string, redirect, url_for, request
app = Flask("todo")

@app.route("/")
def route_home():
    return render_template_string(r"""
<h1>TO-DO LIST</h1>
<p>
    <a href="{{ url_for('route_view') }}">List</a>
</p>
    """)

@app.route("/list")
def route_view():
    with sessionmaker(bind=ENGINE)() as session:
        return render_template_string(r"""
<h1>TO-DO LIST</h1>
<p>
    <table>
        {% if tasklist %}

        {% for task in tasklist %}
        <tr>
            <td>
                <form action="{{url_for('route_update_state',task_id=task.id)}}" method="POST">
                    {% if task.state == TASK_COMPLETED %}
                    <input type="submit" style="font-family:Webdings" value="&#97;">
                    {% else %}
                    <input type="submit" value="&nbsp;&nbsp;&nbsp;&nbsp;">
                    {% endif %}
                </form>
            </td>
            <td>
                <div id="task-name-{{task.id}}">
                    <span onclick="show_form_{{task.id}}()">
                        {{task.name}}
                    </span>
                </div>
                <div id="task-name-update-{{task.id}}" style="display:none;">
                    <form id="task-name-update-{{task.id}}-form" action="{{url_for('route_update_name',task_id=task.id)}}"  method="POST">
                        <input type="text" name="name" placeholder="Task Name" value="{{task.name}}" onblur="hide_form_{{task.id}}()" id="task-name-update-{{task.id}}-form-name">
                        <input type="submit" value="Submit" style="display:none;">
                    </form>
                </div>
                <script>
                    function show_form_{{task.id}}(){
                        document.getElementById("task-name-{{task.id}}").style.display = "none";
                        document.getElementById("task-name-update-{{task.id}}").style.display = "block";
                        document.getElementById("task-name-update-{{task.id}}-form-name").focus()

                    }
                    function hide_form_{{task.id}}(){
                        document.getElementById("task-name-{{task.id}}").style.display = "block";
                        document.getElementById("task-name-update-{{task.id}}").style.display = "none";
                    }
                </script>
            </td>
            <td>
                <form action="{{url_for('route_delete',task_id=task.id)}}" method="POST">
                    <input type="submit" style="font-family:Webdings" value='&#114;'>
                </form>
            </td>
        </tr>
        {% endfor %}

        {% else %}

        <tr>
            <td>No items yet</td>
        </tr>

        {% endif %}
    </table>
</p>
<p>
    <form action="{{url_for('route_create')}}" method="POST">
        <input type="text" name="name" placeholder="Task Name">
        <input type="submit" value="Submit">
    </form>
</p>
        """,
        TASK_COMPLETED=TASK_COMPLETED,
        tasklist=handle_read_task_all(session))

@app.route("/list/create", methods=["POST"])
def route_create():
    name = request.form.get("name",None)
    print("name", name)
    if not name is None:
        with sessionmaker(bind=ENGINE)() as session:
            handle_create_task(session, name)
    return redirect(url_for("route_view"))

@app.route("/list/delete/<int:task_id>", methods=["POST"])
def route_delete(task_id):
    with sessionmaker(bind=ENGINE)() as session:
        handle_delete_task(session, task_id)
    return redirect(url_for("route_view"))

@app.route("/list/update/state/<int:task_id>", methods=["POST"])
def route_update_state(task_id):
    with sessionmaker(bind=ENGINE)() as session:
        t: Task_DB = handle_read_task(session, task_id)
        if t.state == TASK_COMPLETED:
            t.state = TASK_ONGOING
        elif t.state == TASK_ONGOING:
            t.state = TASK_COMPLETED
        session.commit()
    return redirect(url_for("route_view"))

@app.route("/list/update/name/<int:task_id>", methods=["POST"])
def route_update_name(task_id):
    name = request.form.get("name",None)
    if not name is None:
        with sessionmaker(bind=ENGINE)() as session:
            handle_update_task_name(session, task_id, name)
    return redirect(url_for("route_view"))

if __name__ == "__main__":
    BASE.metadata.create_all(ENGINE, checkfirst=True)
    SESSION: Session = sessionmaker(bind=ENGINE)()
    setup_db_data(SESSION)
    app.run(debug=True)