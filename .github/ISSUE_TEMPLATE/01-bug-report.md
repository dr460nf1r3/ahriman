---
name: Bug report
about: Create a report to help us improve
title: ''
labels: bug
assignees: ''

---

## Summary

A clear and concise description of what the bug is.

### Steps to reproduce

Steps to reproduce the behavior (commands, environment etc).

### Expected behavior

A clear and concise description of what you expected to happen.

### Logs

Add logs to help explain your problem. By default, the application writes logs into `/dev/log` which is usually default systemd journal and can be accessed by `journalctl` command.

You can also attach any additional information which can be helpful, e.g. configuration used by the application (be aware of passwords and other secrets if any); it can be generated by using `ahriman config` command.

It is also sometimes useful to have information about installed packages which can be accessed by `ahriman version` command.