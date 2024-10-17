import re
import json


class JamfScripts:
    def __init__(self, jamf_client):
        self.jamf_client = jamf_client

    def get_all_scripts(self):
        url = f"{self.jamf_client.jss_url_apiv1}/scripts?page=0&page-size=100&sort=name%3Aasc"
        response = self.jamf_client.jamf_comm(
            url, method="GET", headers=self.jamf_client.json_get_headers
        )
        if response.status_code == 200:
            try:
                json_string = re.search(r"{.*}", response.text, re.DOTALL)
                if json_string:
                    response_json = json.loads(json_string.group(0))
                    return response_json
            except json.JSONDecodeError:
                return "Error: Response is not valid JSON."

    def get_script_by_name(self, script_name):
        script_name = script_name.strip()
        # Retrieve all scripts, filtering by script name
        data = self.get_all_scripts()
        if "results" in data:
            for script in data["results"]:
                if script["name"] == script_name:
                    return script["scriptContents"]
                return "Script not found."
        else:
            return f"Error: Failed to retrieve script."

    def get_all_scripts_content(self):
        data = self.get_all_scripts()
        scripts_list = []
        if "results" in data:
            for script in data["results"]:
                scripts_list.append(script["name"])
            return scripts_list

    def update_script(self, script_id, updated_content):
        url = f"{self.jamf_client.jss_url_apiv1}scripts/{script_id}"
        payload = {"scriptContents": updated_content}
        response = self.jamf_client.jamf_comm(
            url, method="PUT", headers=self.jamf_client.json_post_headers, data=payload
        )

        return response.json()

    def update_message_in_script(self, script_name, new_message):
        # 1. Fetch the script by name
        script = self.get_script_by_name(script_name)
        if script:
            script_id = script["id"]
            # 2. Retrieve the script contents by ID
            script_details = self.get_script_contents_by_id(script_id)
            script_contents = script_details.get("scriptContents", "")
            # 3. Replace the `--message` flag content with the new Slack message
            updated_script = re.sub(
                r'(--message\s*"[^"]*")', f'--message "{new_message}"', script_contents
            )
            # 4. Update the script in Jamf with the new content
            result = self.update_script(script_id, updated_script)
            return result
        else:
            return f"Script {script_name} not found."
