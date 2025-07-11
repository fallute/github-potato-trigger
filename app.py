from flask import Flask, request, jsonify
import requests
import os
import time

app = Flask(__name__)

# Load from environment variables
GITHUB_REPO = os.getenv("GITHUB_REPO", "fallute/potato-scraper")
GITHUB_WORKFLOW = os.getenv("GITHUB_WORKFLOW", "scrape.yml")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "master")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# ✅ Store the latest triggered run_id
latest_run_id = None

@app.route("/run_scraper", methods=["POST"])
def run_scraper():
    global latest_run_id

    if not GITHUB_TOKEN:
        return jsonify({"error": "GitHub token not configured"}), 500

    # Step 1: Trigger the workflow_dispatch
    dispatch_url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/{GITHUB_WORKFLOW}/dispatches"
    payload = {"ref": GITHUB_BRANCH}
    trigger_response = requests.post(dispatch_url, headers=headers, json=payload)

    if trigger_response.status_code != 204:
        return jsonify({"status": "error", "details": trigger_response.text}), trigger_response.status_code

    # Step 2: Wait a few seconds for GitHub to register the workflow run
    time.sleep(5)

    # Step 3: Fetch recent workflow runs to extract the latest real run_id
    runs_url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/runs"
    runs_response = requests.get(runs_url, headers=headers)

    if runs_response.status_code != 200:
        return jsonify({"error": "Failed to fetch runs", "details": runs_response.text}), 500

    runs = runs_response.json().get("workflow_runs", [])

    # ✅ Filter by workflow_dispatch and correct branch
    valid_runs = [
        run for run in runs
        if run["event"] == "workflow_dispatch" and run["head_branch"] == GITHUB_BRANCH
    ]

    # ✅ Pick the latest one by timestamp
    if valid_runs:
        latest = sorted(valid_runs, key=lambda r: r["created_at"], reverse=True)[0]
        latest_run_id = latest["id"]

        return jsonify({
            "status": "success",
            "message": "Action triggered",
            "run_id": latest_run_id
        }), 200

    return jsonify({"error": "No recent workflow_dispatch run found"}), 404


@app.route("/latest_run_id", methods=["GET"])
def get_latest_run_id():
    if latest_run_id:
        return jsonify({"run_id": latest_run_id}), 200
    else:
        return jsonify({"error": "No run_id available"}), 404


@app.route("/cancel/<run_id>", methods=["POST"])
def cancel(run_id):
    cancel_url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/runs/{run_id}/cancel"
    cancel_response = requests.post(cancel_url, headers=headers)

    if cancel_response.status_code == 202:
        return jsonify({"status": "cancelled", "run_id": run_id}), 200
    else:
        return jsonify({"status": "error", "details": cancel_response.text}), cancel_response.status_code


@app.route("/status/<run_id>", methods=["GET"])
def status(run_id):
    try:
        status_url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/runs/{run_id}"
        status_response = requests.get(status_url, headers=headers, timeout=10)

        if status_response.status_code != 200:
            return jsonify({
                "status": "unknown",
                "conclusion": None,
                "details": f"GitHub returned {status_response.status_code}"
            }), 200

        run_data = status_response.json()
        return jsonify({
            "status": run_data.get("status"),
            "conclusion": run_data.get("conclusion")
        }), 200

    except requests.exceptions.RequestException as e:
        return jsonify({
            "status": "unknown",
            "conclusion": None,
            "details": str(e)
        }), 200


@app.route("/", methods=["GET"])
def index():
    return "✅ Tracking Live!"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
