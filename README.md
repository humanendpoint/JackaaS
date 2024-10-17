# JackaaS (JAMF Slack as a Service)

Simply put this is a Slack app to interact with JAMF, able to obtain data and perform (some) actions relevant to JAMF clients. 
It also can display charts of various input.

#### Note

There is an `example.yml` that can be used instead of `build-function.yml` once you clone this repo.
It checks whether *this* repo has been updated with new code (subsequently a new version) or not, and then uploads the new version to google cloud functions for you.

## What you need

- A `Google Cloud Platform` project with access to admin Google Cloud Functions
- A `Slack app` with access to:
    - On behalf of users:
        - View information about a user’s identity
        - View people in a workspace
        - View email addresses of people in a workspace
    - On behalf of the app:
        - Send messages as @jackaas with a customized username and avatar
        - Send messages as @jackaas
        - View messages and other content in direct messages that JackaaS has been added to

    - add the secrets and tokens as GitHub secrets with the following names:
        - `SLACK_BOT_TOKEN`
        - `SLACK_SIGNING_SECRET`
        - `SLACK_USER_TOKEN`
- A `JAMF API role and client` with privileges:
    Create Device Name Patterns
    Read Computer Check-In
    Read Computers
    Read Jamf Content Distribution Server Files
    Read Device Name Patterns
    Send Computer Remote Lock Command
    Read Smart Computer Groups
    Read Computer Inventory Collection
    View Disk Encryption Recovery Key
    Create Smart Computer Groups
    Read Computer Extension Attributes
    Read Accounts
    Read Scripts

    this is used as `JAMF_CLIENT_ID` and `JAMF_CLIENT_SECRET` respectively.
- A few more GitHub secrets:
    `GCF_NAME`
    `GCF_REGION`
    `GCF_PROJECT`
    `PROJECT_ID`
    `GCF_SERVICE_ACCOUNT`
    `JAMF_CLIENT_ID`
    `JAMF_CLIENT_SECRET`
    `SLACK_BOT_TOKEN`
    `SLACK_SIGNING_SECRET`
    `SLACK_USER_TOKEN`
- And a secret for `COMPANY_DOMAIN` as well.

## Features

- [x] handles authorization to run commands by comparing Slack user with JAMF user permissions
- [x] outputs any handling / python errors directly to Slack

#### device actions
#### device info retrieval
#### report lists
#### charts (pie, bar, doughnut, horizontal bar)
#### groups management
#### other


## Assumptions

    - assumes Slack user emails are identical to JAMF user email
    - assumes usernames in JAMF are structured like “u.sername” or a serial number (will be adjusted to be user determined for client naming style)


## More information

On the wiki!