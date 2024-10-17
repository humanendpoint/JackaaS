import os
import requests
import jamf_groups, jamf_utils, jamf_orchestra, jamf_scripts


class JamfClient:
    def __init__(self, jss_url="https://catawiki.jamfcloud.com"):
        self.jss_url = jss_url
        self.jss_client_id = os.environ.get("JAMF_CLIENT_ID")
        self.jss_client_secret = os.environ.get("JAMF_CLIENT_SECRET")
        self.jss_token_headers = {"Content-Type": "application/x-www-form-urlencoded"}
        self.jamf_token = self.get_api_token()
        self.jss_url_api = f"{self.jss_url}/JSSResource"
        self.jss_url_apiv1 = f"{self.jss_url}/api/v1"
        self.jss_url_api_grps = f"{self.jss_url_api}/computergroups"
        self.jss_url_api_computers = f"{self.jss_url_api}/computers"
        self.jss_url_api_computername = f"{self.jss_url_api_computers}/name"
        self.jss_url_api_computerId = f"{self.jss_url_api_computers}/id"
        self.jss_url_api_computer_basic = f"{self.jss_url_api_computers}/subset/basic"
        self.json_get_headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.jamf_token}",
        }
        self.xml_post_headers = {
            "Content-Type": "application/xml",
            "Authorization": f"Bearer {self.jamf_token}",
        }
        self.text_get_headers = {"Authorization": f"Bearer {self.jamf_token}"}
        self.groups = jamf_groups.JamfGroups(self)
        self.endpoint_details = jamf_utils.JamfUtils(self)
        self.orchestra = jamf_orchestra.JamfOrchestra(self)
        self.scripts = jamf_scripts.JamfScripts(self)

    def get_api_token(self):
        # jamf_url = f"{self.jss_url}/api/v1/auth/token"
        jamf_url = f"{self.jss_url}/api/oauth/token"
        # headers = {"Accept": "application/json"}
        data = {
            "client_id": f"{self.jss_client_id}",
            "grant_type": "client_credentials",
            "client_secret": f"{self.jss_client_secret}",
        }

        response = self.jamf_comm(
            jamf_url, method="POST", headers=self.jss_token_headers, data=data
        )
        if response.status_code == 200:
            response_json = response.json()
            access_token = response_json.get("access_token")
            return access_token
        else:
            raise Exception(
                f"Failed to get API token. Status code: {response.status_code}"
            )

    def jamf_comm(self, url, method="GET", headers=None, data=None):
        try:
            if method == "GET":
                if headers is None:
                    response = requests.get(url)
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, headers=headers, data=data)
            elif method == "PUT":
                response = requests.put(url, headers=headers, data=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)
            # Add more methods as needed (PUT, DELETE, etc.)
            else:
                raise ValueError("Invalid HTTP method")

            return response
        except requests.exceptions.RequestException as e:
            print(f"Error in API communication: {e}")
            return None
