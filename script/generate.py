import requests
import json
import os
import base64
import random
import string
from datetime import datetime

# -- CONFIGURATION --

# Replace this with your actual Hugging Face model API URL!
HF_API = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3"

# Get tokens from environment variables (make sure these are set)
HF_TOKEN = os.environ.get("HF_TOKEN")
GITHUB_TOKEN = os.environ.get("GH_TOKEN")
GITHUB_USER = "Saichakshukaki"  # Your GitHub username

if not HF_TOKEN:
    raise EnvironmentError("HF_TOKEN environment variable not set")
if not GITHUB_TOKEN:
    raise EnvironmentError("GH_TOKEN environment variable not set")

HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}
GH_HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}

# -- FUNCTIONS --

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
    print("Sending request to Hugging Face API...")
    res = requests.post(HF_API, headers=HEADERS, json={"inputs": prompt})

    print(f"HF API Status Code: {res.status_code}")
    print(f"HF API Response preview:\n{res.text[:500]}")

    if res.status_code != 200:
        raise Exception(f"Hugging Face API error: {res.status_code} - {res.text}")

    try:
        output = res.json()
        # output should be a list with dict containing 'generated_text'
        if not isinstance(output, list) or "generated_text" not in output[0]:
            raise ValueError("Unexpected API response structure")
        return output[0]["generated_text"]
    except Exception as e:
        raise Exception(f"Failed to parse Hugging Face response: {e}\nFull response text: {res.text}")

def parse_output(raw_text):
    files = {}
    current_file = None
    for line in raw_text.splitlines():
        if line.startswith("FILE: "):
            current_file = line[6:].strip()
            files[current_file] = ""
        elif current_file:
            files[current_file] += line + "\n"
    if not files:
        raise ValueError("No files parsed from AI output")
    return files

def generate_unique_repo_name(base_name):
    # Append random 4-char suffix to avoid name collisions
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"{base_name}-{suffix}"

def create_repo(repo_name):
    url = "https://api.github.com/user/repos"
    payload = {"name": repo_name, "auto_init": True}
    print(f"Creating GitHub repo: {repo_name}...")
    response = requests.post(url, headers=GH_HEADERS, json=payload)
    if response.status_code == 422:
        # Repo already exists; try new name
        print("Repo name exists, generating a unique repo name...")
        new_name = generate_unique_repo_name(repo_name)
        return create_repo(new_name)
    elif response.status_code not in [200, 201]:
        raise Exception(f"GitHub repo creation failed: {response.status_code} - {response.text}")
    print("Repo created successfully.")
    return repo_name

def push_files(repo, files):
    # Try branch "main" first, fallback to "master"
    branches_to_try = ["main", "master"]
    for branch in branches_to_try:
        print(f"Trying to push files to branch '{branch}'...")
        all_ok = True
        for filename, content in files.items():
            url = f"https://api.github.com/repos/{GITHUB_USER}/{repo}/contents/{filename}"
            content_b64 = base64.b64encode(content.encode()).decode()
            data = {
                "message": f"Add {filename}",
                "content": content_b64,
                "branch": branch
            }
            response = requests.put(url, headers=GH_HEADERS, json=data)
            if response.status_code not in [200, 201]:
                print(f"Failed to push {filename} to branch {branch}: {response.status_code} - {response.text}")
                all_ok = False
                break
        if all_ok:
            print(f"All files pushed successfully to branch '{branch}'.")
            return
    raise Exception("Failed to push files to both 'main' and 'master' branches.")

def update_dashboard(repo_name):
    url = f"https://{GITHUB_USER}.github.io/{repo_name}/"
    dashboard_dir = "dashboard"
    os.makedirs(dashboard_dir, exist_ok=True)
    path = os.path.join(dashboard_dir, "sites.json")

    if os.path.exists(path):
        with open(path, "r") as f:
            data = json.load(f)
    else:
        data = []

    data.append({"name": repo_name, "url": url})

    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Dashboard updated with {repo_name}.")

# -- MAIN --

if __name__ == "__main__":
    try:
        raw_output = ask_ai()
        files = parse_output(raw_output)
        base_repo_name = f"site-{datetime.now().strftime('%Y%m%d')}"
        repo_name = create_repo(base_repo_name)
        push_files(repo_name, files)
        update_dashboard(repo_name)
        print(f"Workflow complete! Site repo: {repo_name}")
    except Exception as e:
        print("ERROR:", e)
        exit(1)
