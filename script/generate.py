import requests
import json
import os
from datetime import datetime
import base64

# ✅ Hugging Face API setup — using working model
HF_API = "https://api-inference.huggingface.co/models/google/flan-t5-large"
HEADERS = {"Authorization": f"Bearer {os.environ['HF_TOKEN']}"}

# ✅ GitHub setup
GITHUB_USER = "Saichakshukaki"
GITHUB_TOKEN = os.environ["GH_TOKEN"]

# ✅ Ask Hugging Face AI to generate a website idea + code
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
    try:
        res = requests.post(HF_API, headers=HEADERS, json={"inputs": prompt})
        print("Status Code:", res.status_code)
        print("Response Preview:", res.text[:500])
        res.raise_for_status()
        output = res.json()
        if isinstance(output, list) and "generated_text" in output[0]:
            return output[0]["generated_text"]
        elif isinstance(output, dict) and "generated_text" in output:
            return output["generated_text"]
        elif isinstance(output, dict) and "text" in output:
            return output["text"]
        else:
            raise ValueError(f"Unexpected Hugging Face API response structure: {output}")
    except requests.exceptions.RequestException as e:
        print("RequestException:", e)
        print("Full Response Text:", res.text if 'res' in locals() else '')
        raise
    except Exception as e:
        print("Exception:", e)
        print("Full Response Text:", res.text if 'res' in locals() else '')
        raise

# ✅ Parse the AI's output into separate code files
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

# ✅ Create new GitHub repository
def create_repo(name):
    url = "https://api.github.com/user/repos"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    payload = {"name": name, "auto_init": True}
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code not in [200, 201]:
        raise Exception(f"GitHub repo creation failed: {response.status_code} - {response.text}")

# ✅ Push files into that repo
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

# ✅ Update your GitHub Pages dashboard
def update_dashboard(repo_name):
    url = f"https://{GITHUB_USER}.github.io/{repo_name}/"
    path = "dashboard/sites.json"

    os.makedirs("dashboard", exist_ok=True)

    if os.path.exists(path):
        with open(path, "r") as f:
            data = json.load(f)
    else:
        data = []

    data.append({"name": repo_name, "url": url})

    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# ✅ Main script runner
if __name__ == "__main__":
    raw_output = ask_ai()
    files = parse_output(raw_output)
    repo_name = f"site-{datetime.now().strftime('%Y%m%d')}"
    create_repo(repo_name)
    push_files(repo_name, files)
    update_dashboard(repo_name)
