import time
import re
from concurrent.futures import ThreadPoolExecutor


class JamfGroups:
    def __init__(self, jamf_client):
        self.jamf = jamf_client  # JamfClient orchestration instance
        self.jss_url = self.jamf.jss_url
        self.json_get_headers = self.jamf.json_get_headers
        self.xml_post_headers = self.jamf.xml_post_headers
        self.jss_url_api_grps = self.jamf.jss_url_api_grps

    def create_group(
        self,
        group_name,
        is_smart="true",
        computers=None,
        criterion_name=None,
        priority="0",
        and_or="and",
    ):
        response = self.jamf.jamf_comm(
            self.jss_url_api_grps, method="GET", headers=self.json_get_headers
        )
        if response.status_code == 200:
            data = response.json()
            computer_groups = data.get("computer_groups", [])
            # Get the ID for the new group
            new_group_id = max(group["id"] for group in computer_groups) + 1
        else:
            print(f"Failed to get computer groups: {response.text}")
            return None

        if is_smart == "true":
            # Create XML for the new group
            xml_template = f"""
            <computer_group>
                <name>{group_name}</name>
                <is_smart>{is_smart}</is_smart>
                <criteria>
                    <criterion>
                        <name>{criterion_name}</name>
                        <priority>{priority}</priority>
                        <and_or>{and_or}</and_or>
                        <search_type>is</search_type>
                        <value>{group_name}</value>
                        <opening_paren>false</opening_paren>
                        <closing_paren>false</closing_paren>
                    </criterion>
                </criteria>
            </computer_group>
            """
        else:
            if computers:
                xml_template = self.create_static_group_template(
                    group_name, computers, is_smart="false"
                )
            else:
                print("No computers specified for the static group.")
                return None
        url = f"{self.jss_url_api_grps}/id/{new_group_id}"
        response = self.jamf.jamf_comm(
            url, method="POST", headers=self.xml_post_headers, data=xml_template
        )
        if response and response.status_code == 201:
            print(f"Smart group '{group_name}' created successfully.")
            return response
        else:
            print(f"Failed to create smart group '{group_name}': {response.text}")
            return None

    def create_static_group_template(self, group_name, computers, is_smart="false"):
        computer_entries = "\n".join(
            f"""
            <computer>
                <serial_number>{serial_number}</serial_number>
            </computer>
            """
            for serial_number in enumerate(computers, start=1)
        )
        xml_template = f"""
        <computer_group>
            <name>{group_name}</name>
            <is_smart>{is_smart}</is_smart>
            <computers>
                {computer_entries}
            </computers>
        </computer_group>
        """
        return xml_template

    def count_computers_in_smart_group(self, group_name, create_missing):
        url = f"{self.jss_url_api_grps}/name/{group_name}"
        response = self.jamf.jamf_comm(url, method="GET", headers=self.json_get_headers)
        if response.status_code == 200:
            data = response.json()
            computers = data.get("computer_group", {}).get("computers", [])
            return len(computers)
        else:
            if create_missing:
                print(f"Testing to create smart group {group_name}")
                time.sleep(2)
                try:
                    criterion_name = "Operating System Version"
                    resp2 = self.create_group(
                        group_name, is_smart="true", criterion_name=criterion_name
                    )
                    if resp2 and resp2.status_code == 200:
                        response = self.jamf.jamf_comm(
                            url, method="GET", headers=self.json_get_headers
                        )
                        if response.status_code == 200:
                            data = response.json()
                            computers = data.get("computer_group", {}).get(
                                "computers", []
                            )
                            return len(computers)
                except Exception as e:
                    return (
                        f"Failed to count computers in smart group '{group_name}': {e}"
                    )
            else:
                return f"Failed to count computers in smart group '{group_name}': {response.text}"

    def fetch_computer_details(self, id, category):
        return self.jamf.endpoint_details.get_computer_details(id, category)

    def count_computers_subset(self, category, key, value_to_check):
        """Counts computers in the specified category where the key has the value_to_check"""
        count = 0
        all_computers = self.jamf.endpoint_details.get_all_computers()
        all_computer_ids = [
            comp["id"] for comp in all_computers["computers"] if "_" not in comp["name"]
        ]
        if value_to_check.lower() == "true":
            value_to_check = True
        elif value_to_check.lower() == "false":
            value_to_check = False
        if key == "ade":
            key = "enrolledViaAutomatedDeviceEnrollment"
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(self.fetch_computer_details, id, category)
                for id in all_computer_ids
            ]

            for future in futures:
                computer_details = future.result()
                print(f"computer details: {computer_details}")
                if computer_details and key in computer_details:
                    if computer_details[key] == value_to_check:
                        count += 1

        print(f"We're returning count: {count}")
        return count

    def extract_group_names(self, command):
        """Extracts multiple group names from the command, expecting quotes"""
        matches = re.findall(r'"([^"]+)"', command)
        return matches if matches else None
