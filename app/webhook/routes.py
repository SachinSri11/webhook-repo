
from flask import Blueprint, request, jsonify, render_template
from app.extensions import get_db
from datetime import datetime

webhook_bp = Blueprint('webhook', __name__)

@webhook_bp.route('/')
def index():
    return render_template('index.html')

@webhook_bp.route('/poll', methods=['GET'])
def poll():
    db = get_db()
    events = db.events.find().sort("timestamp", -1).limit(15)
    return jsonify([
        {
            "request_id": e.get("request_id"),
            "author": e.get("author"),
            "action": e.get("action"),
            "from_branch": e.get("from_branch", ""),
            "to_branch": e.get("to_branch", ""),
            "timestamp": e.get("timestamp")
        }
        for e in events
    ])

@webhook_bp.route('/webhook/receiver', methods=['POST'])
def receive_webhook():
    db = get_db()
    event_type = request.headers.get('X-GitHub-Event')
    payload = request.get_json()
    event = {"timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}

    if event_type == "push":
        event["request_id"] = payload["head_commit"]["id"]
        event["author"] = payload["pusher"]["name"]
        event["action"] = "PUSH"
        event["from_branch"] = None
        event["to_branch"] = payload["ref"].split("/")[-1]

    elif event_type == "pull_request":
        pr = payload["pull_request"]
        event["request_id"] = str(pr["id"])
        event["author"] = pr["user"]["login"]
        event["action"] = "PULL_REQUEST"
        event["from_branch"] = pr["head"]["ref"]
        event["to_branch"] = pr["base"]["ref"]

        if payload["action"] == "closed" and pr["merged"]:
            merged_event = dict(event)
            merged_event["action"] = "MERGE"
            merged_event["timestamp"] = datetime.strptime(
                pr["merged_at"], "%Y-%m-%dT%H:%M:%SZ"
            ).strftime("%Y-%m-%d %H:%M:%S UTC")
            db.events.insert_one(merged_event)

    else:
        return "Ignored", 200

    db.events.insert_one(event)
    return jsonify({"status": "success"}), 200
