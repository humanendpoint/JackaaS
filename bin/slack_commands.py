class SlackCommands:
    # each entry needs a corresponding elif in
    # the execute_command function in slack_handler
    commands = {
        "appstore": "appstore <all_or_computer_name>",
        "count_group": "count group <group_name> <create_if_missing_true_false>",
        "count_computers": "count computers <category> <subset_info> <count_flag_true_false>",
        "create_group": "create group <group_name> <criterion_name> [and_or] [computers]",
        "checkin": "checkin <computer_name1> [computer_name2] [computer_name3] [computer_name4]",
        "chart": "chart <type> <group_name1_or_model> [group_name2] [group_name3] [group_name4] [group_name5] [group_name6]",
        "details": "details <category> <computer_name1> [computer_name2] [computer_name3] [computer_name4]",
        "devicelock": "devicelock <computer_name> <passcode>",
        "duplicates": "duplicates all",
        "extattr": "extattr <all_or_name_of_extension_attribute>",
        "flush": "flush <computer_name>",
        "lockpass": "lockpass <computer_name>",
        "log": "log <computer_name1> [computer_name2] [computer_name3]",
        "mdmexpiry": "mdmprofiles",
        "mdmcommands": "mdmcommands <computer>",
        "membership": "membership <computer_name>",
        "reboots": "reboots <computer_or_all>",
        "redeploy": "redeploy <computer_name1> [computer_name2] [computer_name3]",
        "recovery": "recovery <computer_name1> [computer_name2] [computer_name3]",
        "show_script": "show script <script_name_or_all>",
        "help": "help",
        "commands": "commands",  # For listing commands
    }
    # each command needs a corresponding permission in JAMF for the user
    # to be able to execute the command on Slack
    cmd_permissions = {
        "appstore": ["Read Computers"],
        "count_group": ["Read Smart Computer Groups"],
        "count_computers": ["Read Computers"],
        "checkin": ["Read Computers"],
        "create_group": ["Create Smart Computer Groups"],
        "details": ["Read Computers"],
        "devicelock": ["Update Computers"],
        "duplicates": ["Read Computers"],
        "extattr": ["Read Computer Extension Attributes"],
        "log": ["Read Computers"],
        "show_script": ["Read Scripts"],
        "chart": ["Read Smart Computer Groups"],
        "flush": ["Update Computers"],
        "reboots": ["Read Computers"],
        "redeploy": ["Update Computers"],
        "recovery": ["Read Computers"],
        "lockpass": ["Read Computers"],
        "mdmcommands": ["Read Computers"],
        "mdmexpiry": ["Read Computers"],
        "membership": ["Read Smart Computer Groups"],
        "report": ["Read Computers"],
        "help": ["Read Computers"],
        "commands": ["Read Computers"],
    }

    helpmessage = {
        "appstore": "list app store apps installed per client or for all (top 10)",
        "count_group": "count members of smart group",
        "count_computers": "count computers that fall under a subset of info.",
        "create_group": "create smart or static group",
        "checkin": "display checkin data for computers",
        "chart": "display a chart image of up to 6 smart groups or by model, processor type and arch",
        "details": "display details of a JAMF category e.g. General",
        "devicelock": "send a device lock command to a client",
        "duplicates": "list all duplicate JAMF client names",
        "extattr": "display a list of all or specific extension attribute",
        "help": "display this help",
        "flush": "flush MDM commands for a client",
        "lockpass": "display the lock password for a client",
        "log": "display log for a client",
        "mdmcommands": "display the completed, pending and failed commands sent to a computer",
        "mdmexpiry": "display a count and a list of all clients with expired MDM profiles",
        "membership": "display group membership for a client",
        "reboots": "display last reboot data for all or specific client",
        "redeploy": "redeploy the JAMF framework",
        "recovery": "display recovery key for a client",
        "show_script": "display a list of all scripts or contents of a script",
    }

    @classmethod
    def get_commands(cls):
        """Return the available commands."""
        return cls.commands
