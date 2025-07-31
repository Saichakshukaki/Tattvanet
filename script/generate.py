import requests
import json
import os
from datetime import datetime

# ✅ Updated model (smaller and free-tier friendly)
HF_API = "https://api-inference.huggingface.co/models/google/flan-t5-large"
HEADERS = {"Authorization": f"Bearer {os.environ['HF_TOKEN']}"}

GITHUB_USER = "Saichakshukaki"
GITHUB_TOKEN = os.environ['GH_TOKEN']

def ask_ai():
    prompt = """
Come up with a useful, human-friendly website idea (like a game, calculator, visualizer, productivity tool, etc.).
Then build the entire code in HTML, CSS, and JS. Provide in this format:
FILE: index.html
<code>
FILE: style.css
<code>
FILE: script.js
<code>
"""
    res = requests.post(HF_API, headers=HEADERS, json={"inputs": prompt})
    
    try:
        output = res.json()
        return output[0]['generated_text']
    except Exception as e:
        print("Hugging Face API error:", e)
        print("Raw response:", res.text)
        raise

def parse_output(raw):
    files = {}
    current = None
    for line in raw.splitlines():
        if line.startswith("FILE: "):
            current = line[6:].strip()
            files[current] = ""
        elif current:
            files[current] += line + "\n"
    return files

def create_repo(name):
    requests.post(
        "https://api.github.com/user/repos",
        headers={"Authorization": f"token {GITHUB_TOKEN}"},
        json={"name": name, "auto_init": True}
    )

def push_files(repo, files):
    for name, content in files.items():
        import base64
        content_bytes = content.encode("utf-8")
        content_b64 = base64.b64encode(content_bytes).decode("utf-8")
        requests.put(
            f"https://api.github.com/repos/{GITHUB_USER}/{repo}/contents/{name}",
            headers={"Authorization": f"token {GITHUB_TOKEN}"},
            json={
                "message": f"Add {name}",
                "content": content_b64,
                "branch": "main"
            }
        )

def update_dashboard(repo_name):
    url = f"https://{GITHUB_USER}.github.io/{repo_name}/"
    path = "dashboard/sites.json"
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
    else:
        data = []
    data.append({"name": repo_name, "url": url})
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    output = ask_ai()
    files = parse_output(output)
    repo = f"site-{datetime.now().strftime('%Y%m%d')}"
    create_repo(repo)
    push_files(repo, files)
    update_dashboard(repo)
