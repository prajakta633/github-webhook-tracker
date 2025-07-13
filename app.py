from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

client = MongoClient("mongodb://localhost:27017/")
db = client["webhook_db"]
collection = db["github_events"]

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    event_type = request.headers.get('X-GitHub-Event')

    event = {}  # initialize the dictionary to avoid errors

    if event_type == "push":
        author = data["pusher"]["name"]
        to_branch = data["ref"].split("/")[-1]
        timestamp = datetime.utcnow().strftime('%d %B %Y - %I:%M %p UTC')
        event = {
            "type": "PUSH",
            "author": author,
            "to_branch": to_branch,
            "timestamp": timestamp
        }

    elif event_type == "pull_request":
        action = data.get("action")
        if action == "closed" and data["pull_request"].get("merged"):
            # It's a merge
            author = data["pull_request"]["user"]["login"]
            from_branch = data["pull_request"]["head"]["ref"]
            to_branch = data["pull_request"]["base"]["ref"]
            timestamp = datetime.utcnow().strftime('%d %B %Y - %I:%M %p UTC')
            event = {
                "type": "MERGE",
                "author": author,
                "from_branch": from_branch,
                "to_branch": to_branch,
                "timestamp": timestamp
            }
        else:
            # It's a regular pull request
            author = data["pull_request"]["user"]["login"]
            from_branch = data["pull_request"]["head"]["ref"]
            to_branch = data["pull_request"]["base"]["ref"]
            timestamp = datetime.utcnow().strftime('%d %B %Y - %I:%M %p UTC')
            event = {
                "type": "PULL_REQUEST",
                "author": author,
                "from_branch": from_branch,
                "to_branch": to_branch,
                "timestamp": timestamp
            }

    else:
        return jsonify({"msg": "Event not handled"}), 200

    collection.insert_one(event)
    return jsonify({"msg": "Event stored"}), 200

@app.route("/events", methods=["GET"])
def get_events():
    events = list(collection.find({}, {"_id": 0}))
    return jsonify(events)

if __name__ == "__main__":
    app.run(port=5000)
