from flask import Flask, request, jsonify
import requests
import os
import time

app = Flask(__name__)

GITHUB_REPO = os.getenv("GITHUB_REPO", "fallute/potato-scraper")
GITHUB_WORKFLOW = os.getenv("GITHUB_WORKFLOW", "scrape.yml")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

@app.route("/")
def home():
    return "✅ GitHub Action Webhook is live."

@app.route("/run_scraper", methods=["POST"])
def run_scraper():
    trigger = requests.post(
        f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/{GITHUB_WORKFLOW}/dispatches",
        headers=HEADERS,
        json={"ref": os.getenv("GITHUB_BRANCH", "master")}
    )

    if trigger.status_code != 204:
        return jsonify({"error": "Trigger failed", "details": trigger.text}), 400

    time.sleep(5)  # wait briefly for the run to show up

    run_list = requests.get(
        f"https://api.github.com/repos/{GITHUB_REPO}/actions/runs",
        headers=HEADERS
    )
    if run_list.status_code != 200:
        return jsonify({"error": "Failed to fetch runs"}), 500

    runs = run_list.json().get("workflow_runs", [])
    if not runs:
        return jsonify({"error": "No workflow runs found"}), 404

    run_id = runs[0]["id"]
    return jsonify({"status": "started", "run_id": run_id}), 200

@app.route("/status/<int:run_id>", methods=["GET"])
def check_status(run_id):
    res = requests.get(
        f"https://api.github.com/repos/{GITHUB_REPO}/actions/runs/{run_id}",
        headers=HEADERS
    )
    if res.status_code != 200:
        return jsonify({"error": "Status fetch failed", "details": res.text}), 400

    data = res.json()
    return jsonify({
        "status": data["status"],
        "conclusion": data.get("conclusion")
    })

@app.route("/cancel/<int:run_id>", methods=["POST"])
def cancel_run(run_id):
    cancel = requests.post(
        f"https://api.github.com/repos/{GITHUB_REPO}/actions/runs/{run_id}/cancel",
        headers=HEADERS
    )
    if cancel.status_code == 202:
        return jsonify({"status": "cancelled"}), 200
    else:
        return jsonify({"error": "Cancel failed", "details": cancel.text}), 400

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
