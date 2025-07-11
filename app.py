from flask import Flask, request, jsonify
import requests
import os
import datetime

app = Flask(__name__)

# 🕒 Log when the server starts
print("🚀 GitHub Trigger Server started at:", datetime.datetime.now())

# Load from environment variables for safety
GITHUB_REPO = os.getenv("GITHUB_REPO", "fallute/potato-scraper")
GITHUB_WORKFLOW = os.getenv("GITHUB_WORKFLOW", "scrape.yml")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # 🔐 do not hardcode

# New for Render restart
RENDER_API_KEY = os.getenv("RENDER_API_KEY")            # 🔐 Your personal Render API key
RENDER_SERVICE_ID = os.getenv("RENDER_SERVICE_ID")      # 🔐 ID of this very service

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
        json={"ref": "main"}
    )

    if response.status_code == 204:
        return jsonify({"status": "success", "message": "Action triggered"}), 200
    else:
        return jsonify({"status": "error", "details": response.text}), response.status_code

@app.route("/self_restart", methods=["POST"])
def self_restart():
    if not RENDER_API_KEY or not RENDER_SERVICE_ID:
        return jsonify({"error": "Missing Render credentials"}), 500

    url = f"https://api.render.com/v1/services/{RENDER_SERVICE_ID}/deploys"
    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        r = requests.post(url, headers=headers, json={})
        if r.status_code == 201:
            return jsonify({"status": "success", "message": "Self-restart triggered"}), 200
        else:
            return jsonify({"error": "Failed to restart", "details": r.text}), r.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def index():
    return "✅ Running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Render uses env var PORT
    app.run(host="0.0.0.0", port=port)
