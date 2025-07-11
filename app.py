from flask import Flask, request, jsonify
import requests
import os
import time

app = Flask(__name__)

# Load from environment variables for safety
GITHUB_REPO = os.getenv("GITHUB_REPO", "fallute/potato-scraper")
GITHUB_WORKFLOW = os.getenv("GITHUB_WORKFLOW", "scrape.yml")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # 🔐 do not hardcode

@app.route("/run_scraper", methods=["POST"])
def run_scraper():
    if not GITHUB_TOKEN:
        return jsonify({"error": "GitHub token not configured"}), 500

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    response = requests.post(
        f"https://api.github.com/repos/{GITHUB_REPO}/actions/workflows/{GITHUB_WORKFLOW}/dispatches",
        headers=headers,
        json={"ref": "master"}
    )

    if response.status_code == 204:
        return jsonify({
            "status": "success",
            "message": "Action triggered",
            "run_id": int(time.time())
        }), 200
    else:
        return jsonify({"status": "error", "details": response.text}), response.status_code

@app.route("/", methods=["GET"])
def index():
    return "✅ GitHub Trigger Webhook is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Render sets this automatically
    app.run(host="0.0.0.0", port=port)

