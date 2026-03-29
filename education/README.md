# Education Course — News Digest Email Automation

Welcome! This is a structured, self-paced course that teaches you how every part of the News Digest tool works — from the one-line installer a friend pastes into their terminal, through the Python modules that fetch RSS feeds and send formatted emails, all the way to the CI pipeline that validates every commit across macOS, Linux, and Windows.

No prior Python or programming experience is required. Each lesson builds on the last, explains every concept as it appears, and walks through the actual source code line by line so you understand not just *what* the code does but *why* it was written that way.

## How to use this course

Start with [00-how-to-use-this-course.md](00-how-to-use-this-course.md) — it explains the reading order, prerequisites, time estimates, and what you'll know by the end.

## Lesson index

| # | Lesson | What you'll learn |
|---|--------|------------------|
| 00 | [How to use this course](00-how-to-use-this-course.md) | Reading order, prerequisites, time estimate |
| 01 | [What this project is](01-what-this-project-is.md) | Purpose, goals, version history, target audience |
| 02 | [End-to-end user journey](02-end-to-end-user-journey.md) | What a user experiences from install to daily email |
| 03 | [Repo map](03-repo-map.md) | Every file and folder with its purpose |
| 04 | [Architecture and data flow](04-architecture-and-data-flow.md) | How components connect, how data moves through the pipeline |
| 05 | [Install flow and release artifacts](05-install-flow-and-release-artifacts.md) | How install.sh and install.ps1 download, verify, and extract |
| 06 | [Bootstrap and start.sh](06-bootstrap-and-start-sh.md) | How start.sh detects Python, creates the venv, and launches the wizard |
| 07 | [Setup wizard and .env](07-setup-wizard-and-env.md) | How setup_wizard.py guides configuration and writes .env |
| 08 | [Source registry and config](08-source-registry-and-config.md) | How sources.py defines feeds and config.py loads settings |
| 09 | [Scraper deep dive](09-scraper-deep-dive.md) | How RSS feeds are fetched, parsed, cleaned, and filtered by freshness |
| 10 | [Emailer deep dive](10-emailer-deep-dive.md) | How the digest email is formatted (HTML + plain text) and sent via SMTP |
| 11 | [Main orchestrator and dedup](11-main-orchestrator-and-dedup.md) | How main.py ties it all together with duplicate detection |
| 12 | [CLI management layer](12-cli-management-layer.md) | How the interactive menu lets users manage their installation |
| 13 | [Scheduling and automation](13-scheduling-and-automation.md) | How daily delivery works on macOS, Linux, and Windows |
| 14 | [Security model and threats](14-security-model-and-threats.md) | How secrets, inputs, and email content are protected |
| 15 | [Testing strategy](15-testing-strategy.md) | How the 155-test suite is organized and why every test exists |
| 16 | [Release process and maintenance](16-release-process-and-maintenance.md) | How build_release.py creates distributable assets |
| 17 | [Debugging and troubleshooting](17-debugging-and-troubleshooting.md) | How to diagnose common problems across all platforms |
| 18 | [How to extend the project](18-how-to-extend-the-project.md) | How to add sources, features, and platform support |

## Supplementary material

- **[Appendices](appendices/)** — Quick-reference tables (commands, files, glossary, security checklist)
- **[Diagrams](diagrams/)** — Visual flowcharts of install, runtime, and scheduling flows
- **[Labs](labs/)** — Hands-on exercises to reinforce what you've learned

