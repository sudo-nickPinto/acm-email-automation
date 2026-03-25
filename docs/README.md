# News Digest — Documentation

Welcome. This folder contains everything you need to understand, maintain, and extend this project.

Read them in order — each document builds on the previous one.

## Table of Contents

| # | Document | What You'll Learn |
|---|----------|-------------------|
| 01 | [Project Overview](01-project-overview.md) | What this project does, file map, how to run it |
| 02 | [System Design](02-system-design.md) | Architecture, data flow, multi-source design, state management |
| 03 | [Stack Rationale](03-stack-rationale.md) | Why Python, why requests, why Gmail SMTP, why bash bootstrap |
| 04 | [Config and Environment](04-config-and-environment.md) | How `.env` works, Gmail App Passwords, config.py walkthrough |
| 05 | [Scraper Deep Dive](05-scraper-deep-dive.md) | Multi-source RSS parsing, HTML cleaning, error handling per source |
| 06 | [Emailer Deep Dive](06-emailer-deep-dive.md) | MIME multipart, multi-section HTML email, SMTP protocol |
| 07 | [Main Orchestrator](07-main-orchestrator.md) | Entry point, CLI flags, duplicate detection, decision flow |
| 08 | [Bootstrap, Setup, and Scheduling](08-automation-and-scheduling.md) | One-line installers, start.sh, setup wizard, scheduler.py, daily scheduling |
| 09 | [Best Practices](09-best-practices.md) | SRP, DRY, fail-fast, idempotency, graceful degradation, extensibility |
| 10 | [Troubleshooting](10-troubleshooting.md) | Diagnosis flowchart, common errors, useful commands |

## Suggested Reading Order

**If you're brand new:** Start at 01 and read straight through.

**If you need to fix a bug:** Jump to 10 (Troubleshooting), then read the deep-dive for the relevant module (05, 06, or 07).

**If you want to understand the "why":** Read 02 (System Design) and 03 (Stack Rationale).

**If you want to change the email format:** Read 06 (Emailer Deep Dive).

**If an RSS feed broke:** Read 05 (Scraper Deep Dive).

**If you want to add a new newspaper:** Read 08 (Bootstrap and Setup) — the "Adding a New Source" section.
