import requests
import json
import os
from datetime import datetime
import base64

# ✅ Hugging Face Inference API setup
HF_API = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"
HEADERS = {"Authorization": f"Bearer {os.environ['HF_TOKEN']}"}

# ✅ GitHub details
GITHUB_USER = "Saichakshukaki"
GITHUB_TOKEN = os.environ["GH_TOKEN"]

def ask_ai():
    prompt = """
Come up with a unique, human-useful website idea (like a game, calculator, visualizer, or productivity tool).
Then give the full working code in this format:

FILE: index.html
<html>
<!-- html here -->
</html>

FILE: style.css
/* css here */

FILE: script.js
// js here
"""

    res = requests.post(HF_API, headers=HEADERS, json={"inputs": prompt})

    print("Status Code:", res.status_code)
    print("Response Preview:", res.text[:500])

    if res.status_code != 200:
        raise Exception(f"Hugging Face API error: {res.status_code} - {res.text}")

    try:
        output = res.json()
        return output[0]["generated_text"]
    except Exception as e:
        print("Failed to parse Hugging Face response:", e)
        raise

def parse_output(raw):
    files = {}
    current_file = None
    for line in raw.splitlines():
        if line.startswith("FILE: "):
            current_file = line[6:].strip()
            files[current_file] = ""
        elif current_file:
            files[current_file] += line + "\n"
    return files

def create_repo(name):
    url = "https://api.github.com/user/repos"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    payload = {"name": name, "auto_init": True}
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code not in [200, 201]:
        raise Exception(f"GitHub repo creation failed: {response.status_code} - {response.text}")

def push_files(repo, files):
    for filename, content in files.items():
        url = f"https://api.github.com/repos/{GITHUB_USER}/{repo}/contents/{filename}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        content_b64 = base64.b64encode(content.encode()).decode()

        data = {
            "message": f"Add {filename}",
            "content": content_b64,
            "branch": "main"
        }

        response = requests.put(url, headers=headers, json=data)
        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to push file {filename}: {response.status_code} - {response.text}")

def update_dashboard(repo_name):
    url = f"https://{GITHUB_USER}.github.io/{repo_name}/"
    path = "dashboard/sites.json"

    if os.path.exists(path):
        with open(path, "r") as f:
            data = json.load(f)
    else:
        data = []

    data.append({"name": repo_name, "url": url})

    os.makedirs("dashboard", exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    raw_output = ask_ai()
    files = parse_output(raw_output)
    repo_name = f"site-{datetime.now().strftime('%Y%m%d')}"
    create_repo(repo_name)
    push_files(repo_name, files)
    update_dashboard(repo_name)

