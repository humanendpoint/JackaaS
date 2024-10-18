# JackaaS (JAMF Slack as a Service)

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/humanendpoint/JackaaS/main.svg)](https://results.pre-commit.ci/latest/github/humanendpoint/JackaaS/main)
![Actions Status](https://github.com/humanendpoint/JackaaS/actions/workflows/build-function.yml/badge.svg)

This is a Slack app to interact with JAMF, able to obtain data and perform (some) actions relevant to JAMF clients.
It also can display charts of various input.
<br>

### Note

For IT teams that do not frequent GitHub often or code, there is an `example.yml` that can be used instead of `build-function.yml` once you clone this repo. <br>
It acts like a clone/fork auto-updater: <br>
It checks whether **this** repo has been updated with new code (subsequently a new version) or not, runs a checkout and then uploads the new version to google cloud functions for you. <br>
This means you only need to clone/fork this repo, follow the setup steps in the wiki, and it will run once a month and update the code, if required, automatically. <br>
<br>

## Features

- [x] handles authorization to run commands by comparing Slack user with JAMF user permissions
- [x] outputs any GCF handling / python errors to Slack DM window
- [x] device actions
- [x] device info retrieval
- [x] report lists
- [x] charts (pie, bar, doughnut, horizontal bar)
- [x] groups management <br>
- [x] and more!
<br>

## Assumptions

    Slack user emails are identical to JAMF user email
    usernames in JAMF are structured like “u.sername” or by serial number
<br>

## More information

On the wiki!
