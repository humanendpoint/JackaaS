import os
import slack_commands
from datetime import datetime, timedelta
from collections import Counter
from slack_bolt import App
from slack_bolt import Ack
from slack_bolt.adapter.flask import SlackRequestHandler
from user_auth import UserAuthorization


class SlackHandler:
    def __init__(self, jamf_client):
        self.jamf_client = jamf_client
        self.jamf_utils = self.jamf_client.endpoint_details
        self.groups = self.jamf_client.groups
        self.commands = slack_commands.SlackCommands.commands
        self.cmd_permissions = slack_commands.SlackCommands.cmd_permissions
        self.help = slack_commands.SlackCommands.helpmessage
        self.user_auth = UserAuthorization()
        self.app = App(
            process_before_response=True,
            token=os.environ.get("SLACK_BOT_TOKEN"),
            signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
        )
        self.handler = SlackRequestHandler(self.app)
        # Register all the commands with the app
        self.app.message()(self.handle_message)

    def handle_slack_event(self, data):
        """Handles Slack events and button interactions"""
        return self.handler.handle(data)

    def handle_message(self, message, say, ack: Ack):
        """Handles incoming messages to check for commands"""
        ack()
        response = say(":processing: Processing the request...")
        text = message["text"].strip()
        print(f"Received command text: {text}")
        user_id = message["user"]
        authorized, cmd_key = self.user_auth.is_user_authorized(
            user_id, text, response, self.app.client
        )
        print(f"User authorized: {authorized}, Command key: {cmd_key}")
        if not authorized:
            return

        if cmd_key in self.commands:
            args = text[len(cmd_key) :].strip()
            bypass_functions = ["files", "help", "commands", "duplicates"]
            if args or bypass_functions in cmd_key:
                self.process_command(cmd_key, args, response)
            else:
                self.app.client.chat_update(
                    channel=response["channel"],
                    ts=response["ts"],
                    text=f"No arguments provided for command '{cmd_key}'.",
                )
        else:
            self.app.client.chat_update(
                channel=response["channel"],
                ts=response["ts"],
                text="Unknown command. Please use one of the following: "
                + ", ".join(self.commands.keys()),
            )

    # Modify process_command to handle long responses
    def process_command(self, cmd_key, args, response):
        """Processes specific commands dynamically based on the key"""
        handler_function = getattr(self, f"handle_{cmd_key}", None)
        try:
            if handler_function:
                result_message = handler_function(args)
                # If the result is a list (indicating multiple message chunks), send them one by one
                if isinstance(result_message, list):
                    for idx, msg_chunk in enumerate(result_message):
                        if idx == 0:
                            # Update the initial processing message with the first chunk
                            self.app.client.chat_update(
                                channel=response["channel"],
                                ts=response["ts"],
                                text=msg_chunk,
                            )
                        else:
                            # Send the remaining chunks as new messages in the thread
                            self.app.client.chat_postMessage(
                                channel=response["channel"],
                                thread_ts=response["ts"],  # Keep in the same thread
                                text=msg_chunk,
                            )
                elif isinstance(result_message, dict) and "blocks" in result_message:
                    # Update the processing message with the actual result
                    self.app.client.chat_update(
                        channel=response["channel"],
                        ts=response["ts"],
                        blocks=result_message["blocks"],  # Use blocks directly
                    )
                else:
                    # Handle single message case
                    self.app.client.chat_update(
                        channel=response["channel"],
                        ts=response["ts"],
                        text=result_message,
                    )
            else:
                self.app.client.chat_update(
                    channel=response["channel"],
                    ts=response["ts"],
                    text="Unknown command. Please use one of the following: "
                    + ", ".join(self.commands.keys()),
                )
        except Exception as e:
            # Catch the exception, log it, and update the message with the error
            error_message = f"An error occurred for '{cmd_key}':\n```\n{str(e)}\n```"
            print(f"Error in process_command: {e}")  # This logs the error to GCP logs
            self.app.client.chat_update(
                channel=response["channel"], ts=response["ts"], text=error_message
            )

    def handle_help(self, *args):
        """Return the list of available commands with description."""
        command_list = "\n".join(
            [f"`{cmd}`: {desc}" for cmd, desc in self.help.items()]
        )
        return f"`Commands and description`:\n{command_list}"

    def handle_commands(self, *args):
        """Return the list of available commands."""
        command_list = "\n".join(
            [f"`{cmd}`: {desc}" for cmd, desc in self.commands.items()]
        )
        return f"`Available commands`:\n{command_list}"

    def handle_count_group(self, args):
        count_cmd = args.split()
        if len(count_cmd) >= 2:
            group_name = " ".join(
                count_cmd[0:-1]
            )  # Join everything except the last part as group name
            create_missing = (
                count_cmd[-1].lower() == "true"
            )  # The last part is the true/false flag
            counted = self.count_computers_in_group(group_name, create_missing)
            return counted
        else:
            return "Please provide a valid type, name, and whether to create if missing (true/false)."

    def handle_details(self, args):
        deets = args.split()
        if len(deets) >= 2:
            category = deets[0]
            computer_names = deets[1:]
            try:
                details = self.jamf_client.orchestra.orchestrate_get_computer_details(
                    computer_names=computer_names, category=category
                )
                if details:
                    details_str = "\n".join(
                        (
                            "\n".join(
                                f"{key}: {value}" for key, value in detail.items()
                            )
                            if isinstance(detail, dict)
                            else str(detail)
                        )
                        for detail in details
                    )
                    details_str_clean = details_str.strip('"')
                    return f"Details for *{category}*:\n```{details_str_clean}```"
                else:
                    return f"No details found for category '{category}' and the provided computer names."
            except ValueError as e:
                # Catch the exception and print out the error message
                return f"Error fetching details: {str(e)}"
        else:
            return "Please provide a category and at least one computer name."

    def handle_create_group(self, args):
        parts = [part.strip() for part in args.split('"') if part.strip()]
        if len(parts) >= 2:
            group_name = parts[0]
            criterion_name = parts[1]
            and_or = (
                parts[2].lower()
                if len(parts) > 2 and parts[2].lower() in ["and", "or"]
                else "and"
            )
            computers = parts[3].split() if len(parts) > 3 else None
            if computers:
                self.groups.create_group(
                    group_name, is_smart="false", computers=computers
                )
                return f"Static group `{group_name}` has been created with the specified computers."
            else:
                self.groups.create_group(
                    group_name, criterion_name, is_smart="true", and_or=and_or
                )
                return f"Smart group `{group_name}` for `{criterion_name}` has been created."
        else:
            return "Please provide both a group name and a criteria name."

    def handle_count_computers(self, args):
        parts = args.split()
        if len(parts) >= 3:  # At least category, subset, and a value
            category = parts[0]  # "general"
            subset = parts[1]  # e.g., "enrolledViaAutomatedDeviceEnrollment"
            value = parts[2]  # true/false or other value
            count = self.jamf_client.orchestra.orchestrate_count_computers_subset(
                category, subset, value
            )
            return f"Count of computers in `{category}` for `{subset}` (value `{value}`): {count}"
        else:
            return "Please provide a valid category, subset, and value."

    def model_chart_helper(self):
        return self.chart_helper(
            self.jamf_client.orchestra.orchestrate_get_computer_models,
            chart_text="Model comparison on request",
        )

    def processor_chart_helper(self):
        return self.chart_helper(
            self.jamf_client.orchestra.orchestrate_get_computer_processors,
            chart_text="Processor comparison on request",
        )

    def arch_chart_helper(self):
        return self.chart_helper(
            self.jamf_client.orchestra.orchestrate_get_computer_architectures,
            chart_text="Architecture comparison on request",
        )

    # unfinished
    def appstore_chart_helper(self):
        top_apps = self.jamf_client.orchestra.orchestrate_get_appstore_apps()
        # Prepare labels and counts for chart_helper
        if not top_apps:
            return "No data found."
        labels, counts = zip(*top_apps)  # Unzip the top apps into labels and counts
        # Use chart_helper to generate the chart
        return self.chart_helper(
            lambda: labels,  # Use a lambda to return labels
            chart_type="horizontalBar",
            chart_text="Appstore apps comparison on request",
            counts=counts,
        )

    def chart_helper(
        self,
        data_source_method,
        chart_type="horizontalBar",
        chart_text="Comparison on request",
        counts=None,
    ):
        # If counts are provided, use them directly
        if counts is not None:
            data_names = data_source_method()  # This should give the labels
            # Generate the chart with counts and labels
            chart_url = self.jamf_utils.generate_other_chart(
                list(data_names), counts, chart_type, text=chart_text
            )
            return chart_url

        # Get the data using the passed data source method
        data_names = data_source_method()
        if not data_names:
            return "No data found."
        # Count occurrences of each item in the data
        data_counts = Counter(data_names)
        labels = list(data_counts.keys())
        counts = list(data_counts.values())
        # Generate the chart with counts and labels
        chart_url = self.jamf_utils.generate_other_chart(
            labels, counts, chart_type, text=chart_text
        )
        return chart_url

    def handle_chart(self, args):
        parts = args.split()
        chart_type = parts[0]
        group_names = parts[1:]
        # check if the chart type is valid
        if chart_type not in ["pie", "bar", "doughnut"]:
            return "Invalid chart type. Please choose `pie`, `bar` or `doughnut`."
        if chart_type == "bar":
            if "model" in group_names:
                return self.model_chart_helper()
            elif "processor" in group_names:
                return self.processor_chart_helper()
            elif "arch" in group_names:
                return self.arch_chart_helper()
            elif "apps" in group_names:
                return self.appstore_chart_helper()
        # check if at least two group names are provided
        if len(group_names) < 2:
            return "Please provide at least two group names."
        elif len(group_names) > 6:
            return "Please provide a maximum of six group names."
        else:
            chart = self.jamf_utils.generate_smart_group_chart(group_names, chart_type)
            return chart

    def handle_show_script(self, args):
        script = args.split()
        if len(script) >= 1:
            if script[0] == "all":
                scripts = self.jamf_client.scripts.get_all_scripts_content()
                if isinstance(scripts, list):
                    # Format the list into a string for display
                    result = "\n".join(scripts)
                    return f"```{result}```"
            else:
                script_name = " ".join(script)
                script_content = self.jamf_client.scripts.get_script_by_name(
                    script_name
                )
                # Format the script content into Slack's code block format
                result_message = f"```{script_content}```"
                # Slack message character limit
                SLACK_MESSAGE_LIMIT = 4000
                # Split the message if necessary
                messages = []
                while result_message:
                    if len(result_message) <= SLACK_MESSAGE_LIMIT:
                        messages.append(result_message)
                        break
                    else:
                        # Find the last newline within the limit to avoid breaking lines awkwardly
                        split_point = result_message.rfind("\n", 0, SLACK_MESSAGE_LIMIT)
                        if split_point == -1:
                            split_point = (
                                SLACK_MESSAGE_LIMIT  # No newline found, just split
                            )
                        messages.append(result_message[:split_point])
                        result_message = result_message[
                            split_point:
                        ].lstrip()  # Continue with the rest of the message

                return messages
        else:
            return "Please provide the script name after `show script`."

    def handle_mdmcommands(self, args):
        mdm_command_log = args.split()
        if len(mdm_command_log) >= 1:
            for computer_name in mdm_command_log:
                computer_id = self.jamf_utils.get_computer_id_from_name(
                    computer_name, computers=None
                )
                mdm_command_log_info = (
                    self.jamf_client.orchestra.orchestrate_mdm_commandhistory(
                        computer_id
                    )
                )
                if mdm_command_log_info:
                    return mdm_command_log_info
                else:
                    return f"Failed to get MDM command log for `{computer_name}`."
        else:
            return "Please enter the proper MDM command log command followed by computernames (or `u.sername`)"

    def handle_appstore(self, args):
        appstoreapps = args.split()
        # Check if the first argument is "all"
        if len(appstoreapps) >= 1 and appstoreapps[0] == "all":
            # If there is a second argument (number), use it, otherwise default to 15
            if len(appstoreapps) > 1 and appstoreapps[1].isdigit():
                number = int(appstoreapps[1])
            else:
                number = 15

            # Get the appstore overview with the specified or default number
            appstore_overview = (
                self.jamf_client.orchestra.orchestrate_get_appstore_overview(number)
            )
            if appstore_overview:
                return appstore_overview

        # Handle cases for specific computer names
        for computer_name in appstoreapps:
            computer_id = self.jamf_utils.get_computer_id_from_name(
                computer_name, computers=None
            )
            appstore_info = self.jamf_client.orchestra.orchestrate_get_appstore(
                str(computer_id)
            )
            if appstore_info:
                return f"Appstore apps for `{computer_name}`:\n{appstore_info}"
            else:
                return f"Failed to get appstore apps for `{computer_name}`."

        # If no valid command, prompt for proper input
        return "Please enter the proper appstore command followed by computernames (or `u.sername`)."

    # untested
    def handle_mdmexpiry(self, args):
        expiry = args.split()
        if len(expiry) >= 1:
            if expiry[0] == "all":
                threshold_date = datetime.now()
                expiry_dates = self.jamf_client.orchestra.orchestrate_mdm_expiry(
                    threshold_date
                )
                return expiry_dates
            for computer_name in expiry:
                computer_id = self.jamf_utils.get_computer_id_from_name(
                    computer_name, computers=None
                )
                expiry_info = self.jamf_utils.mdm_expiry(computer_id)
                if expiry_info:
                    return f"MDM expiry info for `{computer_name}`: {expiry_info}"
                else:
                    return f"Failed to get MDM expiry info for `{computer_name}`."
        else:
            return "Please enter the proper MDM expiry command followed by computernames (or `u.sername` or `all`)"

    def handle_extattr(self, args):
        extattr = args.split()
        if len(extattr) >= 1:
            if extattr[0] == "all":
                extattrs = self.jamf_utils.get_all_extattrs_names()
                if isinstance(extattrs, list):
                    # Format the list into a string for display
                    result = "\n".join(extattrs)
                    return f"```{result}```"
            else:
                extattr_name = " ".join(extattr)
                result = self.jamf_utils.get_extattr_by_name(extattr_name)
                return f"```{result}```"
        else:
            return "Please provide the extattr name after `extattr`."

    def handle_checkin(self, args):
        checkin = args.split()
        if len(checkin) >= 1:
            if checkin[0] == "all":
                checkin_list = []
                jamf_computers = self.jamf_utils.get_all_computers()
                days_threshold = 40
                threshold_date = datetime.now() - timedelta(days=days_threshold)
                checkins = self.jamf_client.orchestra.orchestrate_checkin_all(
                    jamf_computers, threshold_date, checkin_list
                )
                return checkins
            else:
                for computer_name in checkin:
                    computer_id = self.jamf_utils.get_computer_id_from_name(
                        computer_name, computers=None
                    )
                    checkin_info = self.jamf_utils.last_check_in(computer_id)
                    if checkin_info:
                        return f"Check-in info: `{computer_name}`: {checkin_info}"
                    else:
                        return f"No recent check-in info found for `{computer_name}`."
        else:
            return "Please enter the proper checkin command followed by computernames (or `u.sername` or `all`)"

    def handle_log(self, args):
        log = args.split()
        if len(log) >= 1:
            for computer_name in log:
                computer_id = self.jamf_utils.get_computer_id_from_name(
                    computer_name, computers=None
                )
                if computer_id is not None:
                    log_info = self.jamf_client.orchestra.orchestrate_get_computer_logs(
                        [computer_id]
                    )
                    if log_info:
                        # Formatting output for better readability
                        formatted_log_info = "\n".join(
                            f"{entry['policy_name']} *Date run*: {entry['date_time']} *Status*: {entry['status']}"
                            for entry in log_info
                        )
                        return f"`{computer_name}`:\n{formatted_log_info}"
                    else:
                        return f"No logs found for `{computer_name}`."
                else:
                    return f"Computer ID not found for `{computer_name}`."
        else:
            return "Please enter the proper log command followed by computernames (or `u.sername`)"

    def handle_recovery(self, args):
        recovery = args.split()
        if len(recovery) >= 1:
            for computer_name in recovery:
                computer_id = self.jamf_utils.get_computer_id_from_name(
                    computer_name, computers=None
                )
                if computer_id is not None:
                    recovery_info = self.jamf_client.orchestra.orchestrate_recoverykey(
                        computer_id
                    )
                    if recovery_info:
                        return f"Recovery key for `{computer_name}`: {recovery_info}"
                    else:
                        return f"Failed to get recovery key for `{computer_name}`."
                else:
                    return f"Computer record ID not found for `{computer_name}`."
        else:
            return "Please enter the proper recovery command followed by computernames (or `u.sername`)"

    def handle_redeploy(self, args):
        redeploy = args.split()
        if len(redeploy) >= 1:
            for computer_name in redeploy:
                computer_id = self.jamf_utils.get_computer_id_from_name(
                    computer_name, computers=None
                )
                if computer_id is not None:
                    redeploy_info = self.jamf_client.orchestra.orchestrate_redeploy(
                        computer_id
                    )
                    if redeploy_info:
                        return f"Redeployed `{computer_name}`."
                    else:
                        return f"Failed to redeploy `{computer_name}`."
                else:
                    return f"Computer ID not found for `{computer_name}`."
        else:
            return "Please enter the proper redeploy command followed by computernames (or `u.sername`)"

    def handle_lockpass(self, args):
        lockpass = args.split()
        if len(lockpass) >= 1:
            for computer_name in lockpass:
                computer_id = self.jamf_utils.get_computer_id_from_name(
                    computer_name, computers=None
                )
                if computer_id is not None:
                    lockpass_info = self.jamf_utils.lockpass(computer_id)
                    if lockpass_info:
                        return f"Lock and pass command sent to `{computer_name}`."
                    else:
                        return f"Failed to send lock and pass command to `{computer_name}`."

    def handle_devicelock(self, args):
        lock = args.split()
        # make sure we have at least 2 arguments
        if len(lock) >= 2:
            computer = lock[0]
            passcode = lock[1]
            computer_id = self.jamf_utils.get_computer_id_from_name(
                computer, computers=None
            )
            if computer_id is not None:
                lock_info = self.jamf_utils.devicelock(computer_id, passcode)
                if lock_info:
                    return lock_info
                else:
                    return lock_info
            else:
                return f"Computer ID not found for `{computer}`."
        else:
            return "Please enter the proper device lock command followed by computernames (or `u.sername`)"

    def handle_duplicates(self, args):
        dupes = args.split()
        if dupes[0] == "all":
            jamf_computers = self.jamf_utils.get_all_computers()
            duplicate_laptops = []
            seen_laptops = set()
            for laptop in jamf_computers["computers"]:
                name = laptop["name"]
                if name in seen_laptops:
                    if "_" not in name:
                        duplicate_laptops.append(name)
                else:
                    seen_laptops.add(name)
            duplicates = self.jamf_client.orchestra.orchestrate_duplicates(
                duplicate_laptops
            )
            return duplicates

    def handle_files(self, args):
        jcds_files = self.jamf_client.orchestra.orchestrate_files()
        jcds_list = []
        for file in jcds_files:
            filename = file["fileName"]
            filelink = self.jamf_client.orchestra.orchestrate_file_link(filename)
            filelink_formatted = f"<{filelink}|{filename}>"
            jcds_list.append(filelink_formatted)
        result_message = "\n".join(jcds_list)
        # Slack message limit: 4000 characters
        SLACK_MESSAGE_LIMIT = 4000
        # Split the message if necessary
        messages = []
        while result_message:
            if len(result_message) <= SLACK_MESSAGE_LIMIT:
                messages.append(result_message)
                break
            else:
                # Find the last newline within the limit to avoid breaking lines awkwardly
                split_point = result_message.rfind("\n", 0, SLACK_MESSAGE_LIMIT)
                if split_point == -1:
                    split_point = SLACK_MESSAGE_LIMIT  # No newline found, just split
                messages.append(result_message[:split_point])
                result_message = result_message[
                    split_point:
                ].lstrip()  # Continue with the rest of the message

        return messages  # Always return a list of message chunks

    def handle_reboots(self, args):
        startup_data = []
        # get the days threshold from the command arguments, default to 40 if not specified
        days_threshold = 60
        threshold_date = datetime.now() - timedelta(days=days_threshold)
        startup_data = self.jamf_client.orchestra.orchestrate_reboots(
            args, threshold_date, startup_data
        )
        # Prepare and send the output message
        if startup_data:
            # Join the startup data into a single string
            startup_data_str = "\n".join(startup_data)
            return f"Reboot data:\n{startup_data_str}"
        else:
            return (
                "All specified computers have started within the last specified days."
            )

    def handle_membership(self, args):
        users = args.split()
        if len(users) >= 1:
            output = []
            for user in users:
                membership_info = (
                    self.jamf_client.orchestra.orchestrate_get_computer_details(
                        computer_names=[user], category="groupMemberships"
                    )
                )
                if membership_info:
                    # since membership_info is a list, iterate over it to access group details
                    group_names = []
                    for group in membership_info[
                        0
                    ]:  # assuming membership_info[0] is a list of groups
                        group_names.append(group["groupName"])
                    if group_names:
                        output.append(
                            f"Membership info for `{user}`:\n```"
                            + "\n".join(group_names)
                            + "```"
                        )
                    else:
                        output.append(f"No group memberships found for `{user}`.")
                else:
                    output.append(f"Failed to get membership info for `{user}`.")

            return "\n\n".join(output)  # combine the output for each user
        else:
            return "Please enter the proper membership command followed by usernames (or `u.sername`)."

    def count_computers_in_group(self, group_name, create_missing):
        """Counts computers in the specified smart group"""
        count = self.groups.count_computers_in_smart_group(
            group_name, create_missing=create_missing
        )
        if isinstance(count, int):
            return f"The group `{group_name}` has {count} computers."
        else:
            return f"Could not find or count computers in the group `{group_name}`. Did you want to create it as well? Then use the `create group` command."
