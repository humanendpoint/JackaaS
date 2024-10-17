# JackaaS (JAMF Slack as a Service)

This is a Slack app to interact with JAMF, able to obtain data and perform (some) actions relevant to JAMF clients. 
It also can display charts of various input.
<br>

#### Note

There is an `example.yml` that can be used instead of `build-function.yml` once you clone this repo.
It checks whether *this* repo has been updated with new code (subsequently a new version) or not, and then uploads the new version to google cloud functions for you.
<br>

## Features

- [x] handles authorization to run commands by comparing Slack user with JAMF user permissions
- [x] outputs any handling / python errors directly to Slack

#### device actions
#### device info retrieval
#### report lists
#### charts (pie, bar, doughnut, horizontal bar)
#### groups management
#### other
<br>

## Assumptions

    assumes Slack user emails are identical to JAMF user email
    assumes usernames in JAMF are structured like “u.sername” or a serial number (will be adjusted to be user determined for client naming style)
<br>

## More information

On the wiki!