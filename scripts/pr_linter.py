
import sys
import re
import requests
import os

GITHUB_API_URL = "https://api.github.com"

def validate_title(title, branch_name):
    title_clean = title.lower().strip().replace("-", " ").replace("_", " ")
    branch_clean = branch_name.lower().strip().replace("-", " ").replace("_", " ")

    if title_clean == branch_clean:
        return False, "Title must not be identical to the branch name."

    if len(title.strip()) < 10:
        return False, "Title is too short. Add more context."

    if " " not in title:
        return False, "Title must contain multiple words for clarity."

    return True, None

def validate_body_structure(body):
    errors = []
    warnings = []

    sections = {
        "1. Issue": "### 1. Issue",
        "2. Description": "### 2. Description of change",
        "3. Testing": "### 3. Testing that was done",
        "4. Don’t forget": "### 4. Don’t forget",
        "5. Notes": "### 5. Additional Notes"
    }

    # Mandatory: Issue section
    if sections["1. Issue"] not in body:
        errors.append("Missing required section: `### 1. Issue`.")
    else:
        issue_block = body.split(sections["1. Issue"])[1].split("###")[0]
        if "Closes:" not in issue_block and "Related:" not in issue_block:
            errors.append("`Issue` section must include `Closes:` or `Related:` link.")

    # Mandatory: Description section
    if sections["2. Description"] not in body:
        errors.append("Missing required section: `### 2. Description of change`.")
    else:
        desc_block = body.split(sections["2. Description"])[1].split("###")[0]
        desc_lines = [line for line in desc_block.strip().splitlines() if line.strip()]
        if len(desc_lines) < 2:
            errors.append("`Description of change` must contain at least 2 lines.")

    # Optional: Warn if soft sections are missing
    for section in ["3. Testing", "4. Don’t forget", "5. Notes"]:
        if sections[section] not in body:
            warnings.append(f"Recommended section missing: `{sections[section]}`.")

    return errors, warnings

def main():
    pr_number = os.environ["PR_NUMBER"]
    repo = os.environ["GITHUB_REPOSITORY"]
    token = os.environ["GITHUB_TOKEN"]

    headers = {"Authorization": f"Bearer {token}"}
    pr_url = f"{GITHUB_API_URL}/repos/{repo}/pulls/{pr_number}"
    response = requests.get(pr_url, headers=headers)
    if response.status_code != 200:
        print(f":x: Failed to fetch PR info. Status code: {response.status_code}")
        sys.exit(1)

    pr_data = response.json()
    title = pr_data["title"]
    body = pr_data.get("body", "")
    branch_name = pr_data["head"]["ref"]

    errors = []

    is_title_valid, title_error = validate_title(title, branch_name)
    if not is_title_valid:
        errors.append(f":x: {title_error}")

    body_errors, body_warnings = validate_body_structure(body)
    errors.extend(f":x: {err}" for err in body_errors)
    for warn in body_warnings:
        print(f":warning:  {warn}")

    if errors:
        print("\n".join(errors))
        sys.exit(1)

    print(":white_check_mark: PR title and description are valid.")

if __name__ == "__main__":
    main()
