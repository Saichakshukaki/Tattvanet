import os
import requests
import json
import base64
from datetime import datetime

def ask_ai(prompt):
    HF_TOKEN = os.getenv("HF_TOKEN")
    if not HF_TOKEN:
        raise Exception("Hugging Face token (HF_TOKEN) not found in environment variables.")

    # You can set HF_MODEL in your environment, defaults to StarCoder2 (good for code generation)
    HF_MODEL = os.getenv("HF_MODEL", "bigcode/starcoder2-3b")
    API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {"inputs": prompt}

    print(f"[DEBUG] Sending POST to {API_URL} with payload: {payload}")
    try:
        res = requests.post(API_URL, headers=headers, data=json.dumps(payload))
        print(f"[DEBUG] Hugging Face API returned status code {res.status_code}")
        print(f"[DEBUG] Response preview: {res.text[:200]}")
        if res.status_code == 404:
            raise Exception(f"Model not found at {API_URL} (404). Check model name and endpoint. See https://huggingface.co/models for valid models.")
        elif res.status_code == 401:
            raise Exception("Unauthorized (401). Check HF_TOKEN.")
        elif res.status_code != 200:
            raise Exception(f"API returned status code {res.status_code}: {res.text}")

        try:
            response_json = res.json()
        except Exception as e:
            raise Exception(f"Failed to parse JSON response: {e}")

        # Typical response: [{'generated_text': '...'}]
        if isinstance(response_json, list) and 'generated_text' in response_json[0]:
            return response_json[0]['generated_text']
        elif isinstance(response_json, dict) and 'generated_text' in response_json:
            return response_json['generated_text']
        else:
            # Try to extract first string value
            for v in response_json.values():
                if isinstance(v, str):
                    return v
            raise Exception(f"Unexpected response format: {response_json}")
    except Exception as e:
        print(f"[ERROR] {e}")
        raise

def create_github_repo(repo_name, files):
    GH_TOKEN = os.getenv("GH_TOKEN")
    if not GH_TOKEN:
        raise Exception("GitHub token (GH_TOKEN) not found in environment variables.")

    api_url = "https://api.github.com/user/repos"
    headers = {
        "Authorization": f"token {GH_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "name": repo_name,
        "auto_init": False,
        "private": False
    }

    print(f"[DEBUG] Creating GitHub repo: {repo_name}")
    resp = requests.post(api_url, headers=headers, json=data)
    print(f"[DEBUG] GitHub API returned status code {resp.status_code}")
    print(f"[DEBUG] Response preview: {resp.text[:200]}")
    if resp.status_code != 201:
        raise Exception(f"Failed to create repo: {resp.status_code} {resp.text}")

    repo_info = resp.json()
    owner = repo_info["owner"]["login"]
    repo = repo_info["name"]

    # Create files by committing directly to the default branch (main)
    for fname, content in files.items():
        file_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{fname}"
        file_data = {
            "message": f"Add {fname}",
            "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
            "branch": "main"
        }
        print(f"[DEBUG] Creating file {fname} in repo {repo}")
        file_resp = requests.put(file_url, headers=headers, json=file_data)
        print(f"[DEBUG] Status: {file_resp.status_code}, Preview: {file_resp.text[:200]}")
        if file_resp.status_code not in [201, 200]:
            raise Exception(f"Failed to create file {fname}: {file_resp.status_code} {file_resp.text}")
    return f"https://github.com/{owner}/{repo}"

def update_dashboard(repo_url):
    dashboard_path = "dashboard/sites.json"
    print(f"[DEBUG] Updating dashboard {dashboard_path} with new repo URL: {repo_url}")
    if os.path.exists(dashboard_path):
        with open(dashboard_path, "r") as f:
            try:
                sites = json.load(f)
            except Exception:
                sites = []
    else:
        sites = []

    sites.append({"url": repo_url, "date": datetime.utcnow().strftime("%Y-%m-%d")})
    with open(dashboard_path, "w") as f:
        json.dump(sites, f, indent=2)

def main():
    print("[INFO] Starting autonomous site builder")
    prompt = """
Come up with a unique, human-useful website idea (game, tool, visualizer, or productivity app). Then give the full working code for the website clearly separated as files named index.html, style.css, and script.js.
"""
    website_code = ask_ai(prompt)

    # Basic parser for files, adapt if needed
    index_html, style_css, script_js = "", "", ""
    if "<html" in website_code and "<style" in website_code and "<script" in website_code:
        index_html = website_code.split("<style")[0]
        style_css = "<style" + website_code.split("<style")[1].split("</style>")[0] + "</style>"
        script_js = "<script" + website_code.split("<script")[1].split("</script>")[0] + "</script>"
    else:
        index_html = website_code  # fallback all in html

    files = {
        "index.html": index_html.strip(),
        "style.css": style_css.replace("<style>", "").replace("</style>", "").strip(),
        "script.js": script_js.replace("<script>", "").replace("</script>", "").strip(),
    }

    repo_name = "site-" + datetime.utcnow().strftime("%Y%m%d")
    repo_url = create_github_repo(repo_name, files)
    update_dashboard(repo_url)
    print(f"[INFO] Successfully created site repo: {repo_url}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR] Script failed: {e}")
        exit(1)
