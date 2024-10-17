from datetime import datetime
import re
import json
import get_chart


class JamfUtils:
    def __init__(self, jamf_client):
        self.jamf = jamf_client
        self.computers = jamf_client.jss_url_api_computers
        self.apiv1 = self.jamf.jss_url_apiv1
        self.computerId = self.jamf.jss_url_api_computerId
        self.json_get_headers = self.jamf.json_get_headers
        self.jss_api = self.jamf.jss_url_api

    def last_check_in(self, id):
        response = self.jamf.jamf_comm(
            f"{self.computerId}/{id}", method="GET", headers=self.json_get_headers
        )
        data = response.json()
        computer_data = data.get("computer", {})
        general = computer_data.get("general", {})
        name = computer_data.get("location", {}).get("real_name", "")
        last_contact_time_str = general.get("last_contact_time", "")
        # Check the last contact time
        if last_contact_time_str:
            last_contact_time = datetime.fromisoformat(
                last_contact_time_str.replace("Z", "+00:00")
            )
            return f"`user`: {name}: {last_contact_time}\n"

    def get_all_computers(self):
        """Get all computer IDs"""
        response = self.jamf.jamf_comm(
            self.computers, method="GET", headers=self.json_get_headers
        )
        json_data = response.json()
        return json_data

    def get_basic_info(self, id):
        response = self.jamf.jamf_comm(
            f"{self.computerId}/{id}/subset/General", headers=self.jamf.text_get_headers
        )
        return response.text

    def get_computer_details(self, id, category="general"):
        # capitalize first letter of category if required
        if "groupMemberships" not in category:
            category = category.lower()
        response = self.jamf.jamf_comm(
            f"{self.apiv1}/computers-inventory-detail/{id}",
            method="GET",
            headers=self.json_get_headers,
        )
        data = response.json()
        if category.lower() == "location":
            category = "userAndLocation"
        if category in data:
            return data[category]
        else:
            raise ValueError(
                f"Category '{category}' not found in the computer details."
            )

    # for now using classic API for this
    def get_specific_info(self, id):
        response = self.jamf.jamf_comm(
            f"{self.jss_api}/computers/id/{id}",
            method="GET",
            headers=self.jamf.json_get_headers,
        )
        json_data = response.json()
        return json_data

    def get_computer_id_from_name(self, name, computers=None):
        if computers is None:
            computers = self.get_all_computers()[
                "computers"
            ]  # Use `computers` from API if not passed
        for laptop in computers:
            if laptop["name"] == name:
                print(f"laptop id: {laptop['id']}")
                return laptop["id"]

    def get_files(self):
        response = self.jamf.jamf_comm(
            f"{self.apiv1}/jcds/files", method="GET", headers=self.json_get_headers
        )
        if response.status_code == 200:
            try:
                response_json = json.loads(response.text)
                print(f"response json for get files: {response_json}")
                return response_json
            except json.JSONDecodeError as e:
                return f"Error: Could not retrieve JSON: {e}"

    def get_file_link(self, filename):
        response = self.jamf.jamf_comm(
            f"{self.apiv1}/jcds/files/{filename}",
            method="GET",
            headers=self.json_get_headers,
        )
        if response.status_code == 200:
            try:
                response_json = json.loads(response.text)
                link = response_json.get("uri")
                return link
            except json.JSONDecodeError as e:
                return f"Error: Could not retrieve JSON: {e}"

    def generate_smart_group_chart(self, group_names, chart_type):
        """Generates a chart of current counts for the given smart groups"""
        current_counts = []
        for group_name in group_names:
            count = self.jamf.groups.count_computers_in_smart_group(
                group_name, create_missing=False
            )
            if count is not None:
                current_counts.append(count)
            else:
                return f"Could not retrieve the count for group `{group_name}`."

        # Generate the chart
        chart_url = get_chart.get_current_chart(
            group_names, current_counts, chart_type, text="Group comparison on request"
        )
        # Send the chart as an image
        return {
            "blocks": [
                {
                    "type": "image",
                    "image_url": chart_url,
                    "alt_text": "Chart comparing smart groups",
                }
            ]
        }

    def generate_other_chart(self, labels, counts, chart_type, text="Comparison chart"):
        """Generates a chart of the given data with the specified chart type"""
        chart_url = get_chart.get_current_chart(labels, counts, chart_type, text)
        print(f"chart url: {chart_url}")
        # Send the chart as an image block
        return {
            "blocks": [
                {
                    "type": "image",
                    "image_url": chart_url,
                    "alt_text": "Chart comparing models or groups",
                }
            ]
        }

    def get_computer_logs(self, id):
        response = self.jamf.jamf_comm(
            f"{self.jss_api}/computerhistory/id/{id}",
            method="GET",
            headers=self.json_get_headers,
        )
        data = response.json()
        history = data.get("computer_history", {})
        policy_logs = history.get("policy_logs", [])
        formatted_logs = []

        for log_entry in policy_logs:
            formatted_logs.append(
                {
                    "policy_name": log_entry.get("policy_name", "Unknown Policy"),
                    "date_time": log_entry.get(
                        "date_completed", "Unknown Date"
                    ),  # Use 'date_completed' instead of 'date_time'
                    "status": log_entry.get("status", "Unknown Status"),
                }
            )

        return formatted_logs

    def redeploy_framework(self, id):
        url = f"{self.jss_api}/computers/id/{id}/redeploy"
        response = self.jamf.jamf_comm(
            url, method="POST", headers=self.json_get_headers
        )
        true_resp = response.json()
        return true_resp

    def get_recovery_key(self, id):
        response = self.jamf.jamf_comm(
            f"{self.apiv1}/computers-inventory/{id}/filevault",
            method="GET",
            headers=self.json_get_headers,
        )
        recovery_data = response.json()
        if recovery_data:
            fv2_key = recovery_data.get("personalRecoveryKey", "No recovery key found.")
            return fv2_key

    def lockpass(self, id):
        response = self.jamf.jamf_comm(
            f"{self.apiv1}/computers-inventory/{id}/view-recovery-lock-password",
            method="GET",
            headers=self.json_get_headers,
        )
        lockpass = response.json()
        if lockpass:
            lock_key = lockpass.get("recoveryLockPassword", "No lock password found.")
            return lock_key
        else:
            return "No lock password found."

    def devicelock(self, id, passcode):
        response = self.jamf.jamf_comm(
            f"{self.jss_api}/computercommands/command/DeviceLock/passcode/{passcode}/id/{id}",
            method="POST",
            headers=self.json_get_headers,
        )
        if response == 201:
            return "Device locked successfully."
        else:
            return f"Failed to lock device: {response.status_code}: {response.text}"

    def get_duplicates(self, duplicate_laptop):
        url = f"{self.jss_api}/computers/match/name/{duplicate_laptop}"
        response = self.jamf.jamf_comm(
            url, method="GET", headers=self.jamf.text_get_headers
        )
        return response.text

    def oldest_newest(self, duplicate_computers):
        records = []
        for comp in duplicate_computers:
            computer_id = comp["id"]
            info = self.get_specific_info(computer_id)
            general_info = info["computer"]["general"]
            last_contact_time = general_info.get("last_contact_time", "N/A")
            last_enrolled_date = general_info.get("last_enrolled_date_utc", "N/A")
            serial_number = general_info.get("serial_number", "N/A")

            # Convert time strings to datetime for comparison
            last_contact_time_dt = (
                datetime.strptime(last_contact_time, "%Y-%m-%d %H:%M:%S")
                if last_contact_time != "N/A"
                else None
            )
            last_enrolled_date_dt = (
                datetime.strptime(last_enrolled_date, "%Y-%m-%dT%H:%M:%S.%f%z")
                if last_enrolled_date != "N/A"
                else None
            )

            records.append(
                {
                    "id": general_info["id"],
                    "serial_number": serial_number,
                    "name": general_info["name"],
                    "last_contact_time": last_contact_time_dt,
                    "last_enrolled_date": last_enrolled_date_dt,
                }
            )

        # Sort by last contact time and then by enrolled date to get the oldest and newest records
        records.sort(key=lambda r: (r["last_contact_time"], r["last_enrolled_date"]))

        oldest_record = records[0]
        newest_record = records[-1]

        return oldest_record, newest_record

    def get_appstore(self, computer_id):
        response = self.jamf.jamf_comm(
            f"{self.jss_api}/computerhistory/id/{computer_id}",
            method="GET",
            headers=self.json_get_headers,
        )
        app_data = response.json()
        # Check if the mac_app_store_applications section exists
        if (
            "computer_history" in app_data
            and "mac_app_store_applications" in app_data["computer_history"]
        ):
            app_store_apps = app_data["computer_history"]["mac_app_store_applications"]
            return app_store_apps
        else:
            return {}

    def get_computerhistory(self, computer_id):
        response = self.jamf.jamf_comm(
            f"{self.jss_api}/computerhistory/id/{computer_id}",
            method="GET",
            headers=self.json_get_headers,
        )
        all_history = response.json()
        completed = all_history["computer_history"]["commands"]["completed"][0:5]
        pending = all_history["computer_history"]["commands"]["pending"]
        failed = all_history["computer_history"]["commands"]["failed"]
        return completed, pending, failed

    def mdm_expiry(self, id):
        response = self.get_computer_details(id, category="general")
        mdm_data = response.json()
        if mdm_data:
            expiry_date = mdm_data.get(
                "mdmProfileExpiration", "No MDM expiry date found."
            )
            return expiry_date

    def get_all_extattrs(self):
        response = self.jamf.jamf_comm(
            f"{self.apiv1}/computer-extension-attributes?page=0&page-size=100&sort=name.asc",
            method="GET",
            headers=self.jamf.text_get_headers,
        )
        json_string = re.search(r"{.*}", response.text, re.DOTALL)
        if json_string:
            response_json = json.loads(json_string.group(0))
            return response_json

    def get_all_extattrs_names(self):
        data = self.get_all_extattrs()
        attributes_list = []
        if data:
            for script in data["results"]:
                attributes_list.append(script["name"])
            return attributes_list

    def get_extattr_by_name(self, extattr_name):
        extattr_name = extattr_name.strip()
        print(f"testing {extattr_name}")
        # Retrieve all scripts, filtering by script name
        data = self.get_all_extattrs()
        if "results" in data:
            for attr in data["results"]:
                if attr["name"] == extattr_name:
                    return attr["scriptContents"]
            return "Extension Attribute not found."
        else:
            return f"Error: Failed to retrieve scripts."
