# JackaaS (JAMF Slack as a Service)

This is a Slack app to interact with JAMF, able to obtain data and perform (some) actions relevant to JAMF clients. 
It also can display charts of various input.
<br>

### Note

There is an `example.yml` that can be used instead of `build-function.yml` once you clone this repo.
It checks whether *this* repo has been updated with new code (subsequently a new version) or not, and then uploads the new version to google cloud functions for you.
<br>

## Features

- [x] handles authorization to run commands by comparing Slack user with JAMF user permissions
- [x] outputs any GCF handling / python errors to Slack DM window
- [x] device actions
- [x] device info retrieval
- [x] report lists
- [x] charts (pie, bar, doughnut, horizontal bar)
- [x] groups management
      and more!
- [ ] handles any "computer name" type for validation
<br>

## Assumptions

    Slack user emails are identical to JAMF user email
    usernames in JAMF are structured like “u.sername” or by serial number
<br>

## More information

On the wiki!
