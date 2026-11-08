"""Tools the agent can call. SENSITIVE tools never act directly: they queue an
action in `pending` that the owner must approve (/approve <id>)."""
import json
import subprocess
import time
from datetime import datetime
from . import config, db

SCHEMAS = [
    {"name": "add_todo", "description": "Add a to-do item.",
     "input_schema": {"type": "object", "properties": {"text": {"type": "string"}, "due": {"type": "string", "description": "ISO date, optional"}}, "required": ["text"]}},
    {"name": "list_todos", "description": "List open to-dos.",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "complete_todo", "description": "Mark a to-do done by id.",
     "input_schema": {"type": "object", "properties": {"id": {"type": "integer"}}, "required": ["id"]}},
    {"name": "set_reminder", "description": "Remind the user at a specific local time.",
     "input_schema": {"type": "object", "properties": {"text": {"type": "string"}, "when": {"type": "string", "description": "ISO datetime, local time, e.g. 2026-11-08T09:00"}}, "required": ["text", "when"]}},
    {"name": "remember", "description": "Store a durable fact/preference about the user (e.g. 'prefers short emails').",
     "input_schema": {"type": "object", "properties": {"key": {"type": "string"}, "value": {"type": "string"}}, "required": ["key", "value"]}},
    {"name": "draft_email", "description": "Draft an email. Requires user approval before it is sent.",
     "input_schema": {"type": "object", "properties": {"to": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"}}, "required": ["to", "subject", "body"]}},
    {"name": "run_coding_task", "description": "Delegate a coding task to the local coding agent (works inside the workspace). Requires user approval.",
     "input_schema": {"type": "object", "properties": {"task": {"type": "string"}}, "required": ["task"]}},
]


def add_todo(text, due=None):
    return {"id": db.x("INSERT INTO todos(text,due) VALUES(?,?)", (text, due))}


def list_todos():
    return db.q("SELECT id,text,due FROM todos WHERE done=0 ORDER BY id")


def complete_todo(id):
    db.x("UPDATE todos SET done=1 WHERE id=?", (id,))
    return {"ok": True}


def set_reminder(text, when):
    ts = datetime.fromisoformat(when).timestamp()
    return {"id": db.x("INSERT INTO reminders(text,fire_at) VALUES(?,?)", (text, ts))}


def remember(key, value):
    db.x("INSERT OR REPLACE INTO memory(key,value) VALUES(?,?)", (key, value))
    return {"ok": True}


def _queue(kind, payload):
    pid = db.x("INSERT INTO pending(kind,payload) VALUES(?,?)", (kind, json.dumps(payload)))
    return {"queued_for_approval": pid, "note": "Tell the user to /approve or /reject this id."}


def draft_email(to, subject, body):
    return _queue("email", {"to": to, "subject": subject, "body": body})


def run_coding_task(task):
    return _queue("coding", {"task": task})


def execute_approved(row):
    """Runs an approved pending action. Returns a result string."""
    p = json.loads(row["payload"])
    from . import tools_ext as ext
    if row["kind"] == "coding":
        return ext.code_agent(p["task"])
    if row["kind"] == "email":
        return ext.send_email(p["to"], p["subject"], p["body"])
    if row["kind"] == "imessage":
        return ext._send_imessage_now(p["to"], p["text"])
    return "unknown action"


def call(name, args):
    from . import tools_ext as ext
    try:
        fn = globals().get(name) or getattr(ext, name)
        return json.dumps(fn(**args), default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


from . import tools_ext as _ext  # noqa: E402
SCHEMAS.extend(_ext.SCHEMAS)
