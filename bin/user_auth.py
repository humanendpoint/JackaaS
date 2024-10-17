import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from jamf_client import JamfClient
import slack_commands

class UserAuthorization:
    def __init__(self):
        self.client = WebClient(token=os.environ.get("SLACK_USER_TOKEN"))
        self.jamf = JamfClient()
        self.cmds = slack_commands.SlackCommands()

    def is_user_authorized(self, user_id, text, response, client, required_group=None):
        """Check if a user is authorized to run commands"""
        try:
            user_info = self.client.users_info(user=user_id)
            email = user_info['user']['profile']['email']
            company_domain = os.environ.get("COMPANY_DOMAIN")
            user = email.replace(f"@{company_domain}", "")
            
            if user:
                privileges, access_level = self.get_user_groups(user)
                if required_group and access_level not in required_group:
                    return False, None  # Return as a tuple
                if text.lower().startswith("count group") or text.lower().startswith("count computers"):
                    text = text.replace("count ", "count_")
                if text.lower().startswith("create group"):
                    text = text.replace("create ", "create_")
                if text.lower().startswith("show script"):
                    text = text.replace("show ", "show_")
                command_found = False
                for cmd_key in self.cmds.commands.keys():
                    if text.lower().startswith(cmd_key):
                        command_found = True
                        if any(perm in privileges for perm in self.cmds.cmd_permissions.get(cmd_key, [])):
                            return True, cmd_key  # Valid user and command
                
                if not command_found:
                    client.chat_update(
                        channel=response['channel'],
                        ts=response['ts'],
                        text="Unknown command received: no permissions needed, but also no output! :cheers:"
                    )
                return False, None  # Return as a tuple

            return False, None  # Return as a tuple

        except SlackApiError as e:
            client.chat_update(
                channel=response['channel'],
                ts=response['ts'],
                text=f"Error fetching user info: {e.response['error']}"
            )
            return False, None  # Return as a tuple

    def get_user_groups(self, user):
        """Fetch groups for a user"""
        jamf_user = self.jamf.jamf_comm(f"{self.jamf.jss_url_api}/accounts/username/{user}", method="GET", headers=self.jamf.json_get_headers)
        if jamf_user:
            user_info = jamf_user.json()
            access_level = user_info["account"].get("access_level", "Unknown")
            privileges = user_info["account"]["privileges"].get("jss_objects", [])
            return privileges, access_level

        return [], "Unknown"
