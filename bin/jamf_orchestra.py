import concurrent.futures
from collections import Counter
import re
import xml.etree.ElementTree as XML
from datetime import datetime


class JamfOrchestra:
    def __init__(self, jamf_client):
        self.jamf_client = jamf_client
        self.groups = jamf_client.groups
        self.endpoint_details = jamf_client.endpoint_details

    def orchestrate_last_checkin_count(self, computer_names):
        last_checkins = []
        for name in computer_names:
            last_checkin = self.endpoint_details.get_last_checkin(name)
            if last_checkin is not None:
                last_checkins.append(last_checkin)

        return last_checkins

    def orchestrate_checkin_all(self, jamf_computers, threshold_date, checkin_list):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_computer = {
                executor.submit(
                    self.process_checkin, computer, threshold_date
                ): computer
                for computer in jamf_computers["computers"]
                if "_" not in computer["name"]
            }
            for future in concurrent.futures.as_completed(future_to_computer):
                computer = future_to_computer[future]
                try:
                    result = future.result()
                    if result:
                        checkin_list.append(result)
                except Exception as exc:
                    print(f"Error processing computer {computer['name']}: {exc}")

        if checkin_list:
            checkin_list_fixed = "\n".join(checkin_list)
            return checkin_list_fixed
        else:
            return "All computers have checked in within the last 40 days."

    def process_checkin(self, computer, threshold_date):
        """Helper function to process check-in info for a single computer."""
        try:
            if "_" not in computer["name"]:
                computer_id = computer["id"]
                checkin_info = self.endpoint_details.last_check_in(computer_id)
                if checkin_info:
                    date_match = re.search(
                        r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", checkin_info
                    )
                    if date_match:
                        last_contact_time_str = date_match.group()
                        last_contact_time = datetime.strptime(
                            last_contact_time_str, "%Y-%m-%d %H:%M:%S"
                        )
                        # Check if the last contact time is older than the threshold
                        if last_contact_time < threshold_date:
                            return f"`{computer['name']}`: {checkin_info}"
                else:
                    return None
        except Exception as e:
            print(f"Error processing {computer['name']}: {e}")
        return None

    def orchestrate_fetch_computer_details(self, name, computers, category):
        """Helper function to get computer details."""
        computer_id = self.endpoint_details.get_computer_id_from_name(name, computers)
        details = self.endpoint_details.get_computer_details(computer_id, category)
        print(f"details: {details}")
        return details

    def orchestrate_get_computer_details(
        self, computer_names=None, computers=None, category="general"
    ):
        if computer_names:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future_to_name = {
                    executor.submit(
                        self.orchestrate_fetch_computer_details,
                        name,
                        computers,
                        category,
                    ): name
                    for name in computer_names
                }
                computer_details = []
                for future in concurrent.futures.as_completed(future_to_name):
                    name = future_to_name[future]
                    try:
                        details = future.result()
                        if details is not None:
                            computer_details.append(details)
                    except Exception as e:
                        print(f"Exception occurred for {name}: {e}")

            return computer_details

    def orchestrate_get_computer_logs(self, computer_id):
        logs = []
        for id in computer_id:
            log = self.endpoint_details.get_computer_logs(id)
            if log:
                logs.extend(log)  # extend instead of append
        return logs

    def orchestrate_get_computer_processors(self):
        all_computers = self.endpoint_details.get_all_computers()
        processors = []

        def get_processor(computer):
            id = computer["id"]
            processor = self.endpoint_details.get_computer_details(
                id, category="hardware"
            )
            if processor:
                hardware_processor = processor["processorType"]
                print(f"processor: {hardware_processor}")
                return hardware_processor
            return None

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(get_processor, computer): computer
                for computer in all_computers["computers"]
            }
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        processors.append(result)
                except Exception as exc:
                    computer = futures[future]
                    print(
                        f"Error retrieving processor for computer {computer['id']}: {exc}"
                    )

        return processors

    def orchestrate_get_computer_architectures(self):
        all_computers = self.endpoint_details.get_all_computers()
        architectures = []

        def get_architecture(computer):
            id = computer["id"]
            architecture = self.endpoint_details.get_computer_details(
                id, category="hardware"
            )
            if architecture:
                hardware_architecture = architecture["processorArchitecture"]
                print(f"architecture: {hardware_architecture}")
                return hardware_architecture
            return None

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(get_architecture, computer): computer
                for computer in all_computers["computers"]
            }
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        architectures.append(result)
                except Exception as exc:
                    computer = futures[future]
                    print(
                        f"Error retrieving architecture for computer {computer['id']}: {exc}"
                    )

        return architectures

    def orchestrate_get_computer_models(self):
        all_computers = self.endpoint_details.get_all_computers()
        models = []

        def get_model(computer):
            id = computer["id"]
            model = self.endpoint_details.get_computer_details(id, category="hardware")
            if model:
                hardware_model = model["model"]
                print(f"model: {hardware_model}")
                return hardware_model
            return None

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(get_model, computer): computer
                for computer in all_computers["computers"]
            }
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        models.append(result)
                except Exception as exc:
                    computer = futures[future]
                    print(
                        f"Error retrieving model for computer {computer['id']}: {exc}"
                    )

        return models

    def orchestrate_get_appstore_apps(self):
        all_computers = self.endpoint_details.get_all_computers()
        appstore_apps = []

        def get_appstore(computer):
            id = computer["id"]
            appstore = self.endpoint_details.get_appstore(id)
            if appstore:
                return appstore
            return None

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(get_appstore, computer): computer
                for computer in all_computers["computers"]
            }
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        appstore_apps.append(result)
                except Exception as exc:
                    computer = futures[future]
                    print(
                        f"Error retrieving appstore for computer {computer['id']}: {exc}"
                    )

        installed_apps = []
        excluded_apps = [
            "Pages.app",
            "GarageBand.app",
            "iMovie.app",
            "Keynote.app",
            "Numbers.app",
        ]
        for appstore in appstore_apps:
            if "installed" in appstore:
                for app in appstore["installed"]:
                    app_name = app["name"]
                    if app_name not in excluded_apps:
                        installed_apps.append(app_name)
        # Count occurrences of each app name
        app_counts = Counter(installed_apps)
        # Get the top 12 apps based on counts
        top_apps = app_counts.most_common(12)
        # Return the top apps along with their counts as a tuple list
        return top_apps

    def orchestrate_get_appstore(self, computer_id):
        appstore_apps = self.endpoint_details.get_appstore(computer_id)
        print(f"app store apps: {appstore_apps}")

        # Initialize sections
        installed_apps = []
        pending_apps = []
        failed_apps = []

        # Check if appstore_apps contains the expected structure
        if "installed" in appstore_apps:
            for app_info in appstore_apps["installed"]:
                app_name = app_info.get("name", "Unknown App")
                app_version = app_info.get("version", "Unknown Version")
                size = app_info.get("size_mb", "Unknown Size")
                installed_apps.append(f"📥 `{app_name}` (v{app_version}, {size} MB)")

        if "pending" in appstore_apps:
            for app_info in appstore_apps["pending"]:
                app_name = app_info.get("name", "Unknown App")
                app_version = app_info.get("version", "Unknown Version")
                deployed = app_info.get("deployed", "Unknown Deployment Time")
                pending_apps.append(
                    f"🕒 `{app_name}` (v{app_version}) - Deployed: {deployed}"
                )

        if "failed" in appstore_apps:
            for app_info in appstore_apps["failed"]:
                app_name = app_info.get("name", "Unknown App")
                app_version = app_info.get("version", "Unknown Version")
                status = app_info.get("status", "Unknown Status")
                failed_apps.append(
                    f"❌ `{app_name}` (v{app_version}) - Status: {status}"
                )

        # Create final structured message
        message = []
        if installed_apps:
            message.append("*Installed Apps:*")
            message.extend(installed_apps)
        if pending_apps:
            message.append("\n*Pending Apps:*")
            message.extend(pending_apps)
        if failed_apps:
            message.append("\n*Failed Apps:*")
            message.extend(failed_apps)

        # Join sections and return the result
        return "\n".join(message) if message else "No app store data available."

    def orchestrate_get_appstore_overview(self, number):
        all_computers = self.endpoint_details.get_all_computers()
        appstore_apps = []

        def get_appstore(computer):
            id = computer["id"]
            appstore = self.endpoint_details.get_appstore(id)
            if appstore:
                return appstore
            return None

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(get_appstore, computer): computer
                for computer in all_computers["computers"]
            }
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        appstore_apps.append(result)
                except Exception as exc:
                    computer = futures[future]
                    print(
                        f"Error retrieving appstore for computer {computer['id']}: {exc}"
                    )

        # calculate the top insalled apps
        installed_apps = {}
        excluded_apps = [
            "Pages.app",
            "GarageBand.app",
            "iMovie.app",
            "Keynote.app",
            "Numbers.app",
        ]
        for app in appstore_apps:
            if "installed" in app:
                for app in app["installed"]:
                    app_name = app["name"]
                    if app_name not in excluded_apps:
                        if app_name in installed_apps:
                            installed_apps[app_name] += 1
                        else:
                            # initialize the count
                            installed_apps[app_name] = 1
        # sort the installed apps by count
        sorted_apps = sorted(installed_apps.items(), key=lambda x: x[1], reverse=True)
        counted_apps = len(sorted_apps)
        top_apps = sorted_apps[:number]
        if top_apps:
            pretty_output = [f"*Top {number} Installed Apps:*"]
            for rank, (app_name, count) in enumerate(top_apps, start=1):
                pretty_output.append(
                    f"{rank}. `{app_name}`: Installed on `{count}` computers"
                )
            pretty_output.append(
                f"\n*Total unique apps installed*: `{counted_apps}`\n*Excluding*: {', '.join(excluded_apps)}"
            )
            return "\n".join(pretty_output)
        else:
            return "No installed apps data available."

    def orchestrate_mdm_commandhistory(self, computer_id):
        completed, pending, failed = self.endpoint_details.get_computerhistory(
            computer_id
        )
        # base payload
        payload = {
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "*Commands history:*"},
                },
            ]
        }

        # generate section blocks
        def create_command_blocks(title, commands, fields):
            section_blocks = [
                {"type": "section", "text": {"type": "mrkdwn", "text": f"*{title}*"}},
                {"type": "divider"},
            ]
            for command in commands:
                section_blocks.append(
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": "\n".join(
                                    f"*{key}:* `{command[val]}`"
                                    for key, val in fields.items()
                                ),
                            }
                        ],
                    }
                )
            return section_blocks

        # structure for completed, pending, and failed
        if completed:
            payload["blocks"].extend(
                create_command_blocks(
                    "Completed", completed, {"Command": "name", "Date": "completed"}
                )
            )
        if pending:
            payload["blocks"].extend(
                create_command_blocks(
                    "Pending",
                    pending,
                    {"Command": "name", "Date": "issued", "Last Push": "last_push"},
                )
            )
        if failed:
            payload["blocks"].extend(
                create_command_blocks(
                    "Failed",
                    failed,
                    {"Command": "name", "Status": "status", "Date": "completed"},
                )
            )

        return payload

    def orchestrate_mdm_expiry(self, threshold_date):
        all_computers = self.endpoint_details.get_all_computers()
        expiry_list = []

        def get_expiry(computer):
            id = computer["id"]
            expiry = self.endpoint_details.get_computer_details(id, category="general")
            if expiry and "mdmProfileExpiration" in expiry:
                return computer["name"], expiry["mdmProfileExpiration"]
            return None

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(get_expiry, computer): computer
                for computer in all_computers["computers"]
                if "_" not in computer["name"]
            }
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        computer_name, mdm_expiry_str = result
                        print(
                            f"computer name: {computer_name} mdm_expiry_str: {mdm_expiry_str}"
                        )
                        # Remove 'Z' and convert to naive datetime
                        mdm_expiry_time = datetime.strptime(
                            mdm_expiry_str.replace("Z", ""), "%Y-%m-%dT%H:%M:%S"
                        )
                        # check if the expiry is before today
                        if mdm_expiry_time < threshold_date:
                            print(f"expired: {computer_name} {mdm_expiry_time}")
                            expiry_list.append(f"`{computer_name}`: {mdm_expiry_time}")
                except Exception as exc:
                    computer = futures[future]
                    print(
                        f"Error retrieving MDM expiry for computer {computer['id']}: {exc}"
                    )

        return expiry_list

    def orchestrate_redeploy(self, computer_id):
        redeployed = []
        for id in computer_id:
            redeployment = self.endpoint_details.redeploy_framework(id)
            if redeployment and "commandUuid" in redeployment:
                redeployed.append(redeployment)
        return redeployed

    def orchestrate_count_computers_subset(self, category, subset, value):
        count = self.groups.count_computers_subset(category, subset, value)
        return count

    def orchestrate_files(self):
        files = self.endpoint_details.get_files()
        print(f"files: {files}")
        return files

    def orchestrate_file_link(self, filename):
        file_link = self.endpoint_details.get_file_link(filename)
        return file_link

    def orchestrate_recoverykey(self, computer_id):
        if isinstance(computer_id, list):
            recovery_keys = []
            for id in computer_id:
                recovery_key = self.endpoint_details.get_recovery_key(id)
                recovery_keys.append(recovery_key)
            return recovery_keys
        else:
            return self.endpoint_details.get_recovery_key(computer_id)

    def orchestrate_duplicates(self, duplicate_laptops):
        all_computers = []
        # Get all computers from the XML for each duplicate laptop name
        for laptop in duplicate_laptops:
            xml_response = self.endpoint_details.get_duplicates(laptop)
            if xml_response:
                try:
                    xml_tree = XML.fromstring(xml_response)
                    computers = [
                        {
                            "id": int(computer.find("id").text),
                            "name": computer.find("name").text,
                        }
                        for computer in xml_tree.findall("computer")
                    ]
                    all_computers.extend(computers)
                except XML.ParseError as e:
                    print(f"XML parsing error: {e}")

        # Retrieve additional info for each computer to get the serial numbers
        for computer in all_computers:
            basic_info_response = self.endpoint_details.get_basic_info(computer["id"])
            # Parse the XML response to extract the serial number
            try:
                basic_info_tree = XML.fromstring(basic_info_response)
                serial_number = basic_info_tree.find(".//general/serial_number")
                serial_number = (
                    serial_number.text
                )  # Assuming serial_number is directly under the root
                computer[
                    "serial_number"
                ] = serial_number  # Add serial number to the computer record
            except XML.ParseError as e:
                print(f"XML parsing error for ID {computer['id']}: {e}")
            except AttributeError:
                print(f"Serial number not found for ID {computer['id']}.")

        # Group computers by serial number
        name_to_computers = {}
        for comp in all_computers:
            name = comp.get("name")
            if name:
                if name not in name_to_computers:
                    name_to_computers[name] = []
                name_to_computers[name].append(comp)
        # print(f"name to computers: {name_to_computers}")
        # Only keep groups with more than one record (duplicates)
        duplicate_computers = {
            name: comps for name, comps in name_to_computers.items() if len(comps) > 1
        }
        # Debugging information
        # print(f"dupes: {duplicate_computers}")
        if not duplicate_computers:
            print("No duplicates found.")
            return "No duplicates found."

        payload = {
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "*Duplicates:*"},
                },
                {"type": "divider"},
            ]
        }

        # Loop through the duplicate computers, get oldest and newest records for each serial number
        for serial, comps in duplicate_computers.items():
            oldest_record, newest_record = self.endpoint_details.oldest_newest(comps)
            dupe_payload = {
                "blocks": [
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Oldest Record:*\nID: {oldest_record['id']}\nSerial No: {oldest_record['serial_number']}\nName: {oldest_record['name']}\nLast Contact: {oldest_record['last_contact_time']}\nEnrolled: {oldest_record['last_enrolled_date']}",
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Newest Record:*\nID: {newest_record['id']}\nSerial No: {newest_record['serial_number']}\nName: {newest_record['name']}\nLast Contact: {newest_record['last_contact_time']}\nEnrolled: {newest_record['last_enrolled_date']}",
                            },
                        ],
                    },
                ]
            }
            payload["blocks"].extend(dupe_payload["blocks"])

        return payload

    def process_reboots(self, computer, threshold_date):
        """Process a single computer for reboots."""
        name = computer["name"]
        details = self.orchestrate_get_computer_details(
            computer_names=[name], computers=[computer], category="hardware"
        )
        if details:
            ext_attributes = details[0].get("extensionAttributes", [])
            last_startup = next(
                (attr for attr in ext_attributes if attr["definitionId"] == "29"), None
            )
            if last_startup and last_startup.get("values"):
                last_startup_date_str = last_startup["values"][0]
                try:
                    last_startup_date = datetime.strptime(
                        last_startup_date_str, "%Y-%m-%d %H:%M:%S"
                    )
                    if last_startup_date < threshold_date:
                        return f"`{name}`: {last_startup_date}"
                except ValueError:
                    print(f"Invalid date format for `{name}`: {last_startup_date_str}")
                    return None
        else:
            print(f"No valid startup date available for `{name}`.")
            return None

    def orchestrate_reboots(self, args, threshold_date, startup_data):
        reboots = args.split()
        if reboots[0].lower() == "all":
            # If no specific user, check all computers
            computers = self.endpoint_details.get_all_computers()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future_to_computer = {
                    executor.submit(
                        self.process_reboots, computer, threshold_date
                    ): computer
                    for computer in computers["computers"]
                    if "_" not in computer["name"]
                }
                for future in concurrent.futures.as_completed(future_to_computer):
                    computer = future_to_computer[future]
                    try:
                        startup_data_item = future.result()
                        if startup_data_item:
                            startup_data.append(startup_data_item)
                    except Exception as exc:
                        print(f"Error processing computer {computer['name']}: {exc}")
        # Check if specific user(s) are provided
        else:
            computer_names = reboots  # Adjust index to get user names
            details = self.orchestrate_get_computer_details(
                computer_names=computer_names, category="hardware"
            )
            if details:
                for idx, detail in enumerate(details):
                    ext_attributes = detail.get("extensionAttributes", [])
                    last_startup = next(
                        (
                            attr
                            for attr in ext_attributes
                            if attr["definitionId"] == "29"
                        ),
                        None,
                    )
                    if last_startup:
                        last_startup_date_str = last_startup["values"][
                            0
                        ]  # Extract date string
                        last_startup_date = datetime.strptime(
                            last_startup_date_str, "%Y-%m-%d %H:%M:%S"
                        )
                        startup_data.append(
                            f"`{computer_names[idx]}`: {last_startup_date}"
                        )  # Reference name correctly
                    else:
                        startup_data.append(
                            f"No startup data found for `{computer_names[idx]}`."
                        )

        return startup_data
