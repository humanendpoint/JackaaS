from jamf_client import JamfClient
from slack_handler import SlackHandler 

# Main function
def main(data):
    data_body = data.get_json()
    if "X-Slack-Retry-Num" in data.headers:
        return {'statusCode': 200, 'body': ''}
    if 'type' in data_body:
        if data_body['type'] == 'url_verification':
            challenge = data_body["challenge"]
            return challenge, 200, {'Content-type': 'text/plain'}
        elif data_body['type'] == 'event_callback':
            type_request = data_body["event"]["type"]
            if type_request != "message":
                return 200, {'Content-type': 'text/plain'}
            slack_handler = SlackHandler(JamfClient()) 
            return slack_handler.handle_slack_event(data)

# Entry point
if __name__ == "__main__":
    main()
