# Lesson 00 — How to Use This Course

## Who this course is for

You are a curious person who wants to understand how a real software project works from the inside out. Maybe you are a student learning to code. Maybe you are a friend who received this tool and wants to know what it does under the hood. Maybe you are an experienced developer studying how to structure a cross-platform CLI tool.

Whatever your background, this course assumes **zero prior Python knowledge**. Every concept — from what a virtual environment is, to how SMTP email works, to why SHA-256 checksums matter — is explained the first time it appears.

## What you will know by the end

After completing all 18 lessons you will be able to:

1. **Explain the full user journey** — from pasting one command into a terminal to receiving a daily email digest
2. **Read every line of the codebase** and explain what it does and why it was written that way
3. **Trace data** from an RSS feed through parsing, filtering, formatting, and delivery
4. **Understand cross-platform design** — how the same project supports macOS, Linux, and Windows with platform-specific scheduling, paths, and installers
5. **Reason about security** — what secrets exist, how they are protected, how HTML injection is prevented, why checksums are verified
6. **Modify the project** — add a new newspaper source, change the email format, or add a new scheduling backend
7. **Debug problems** — trace error messages back to their source, understand what went wrong, and fix it

## Reading order

The lessons are numbered 00 through 18 and are designed to be read in order. Each lesson builds on vocabulary and concepts introduced in earlier lessons.

**Suggested reading path:**

| Phase | Lessons | What you learn |
|-------|---------|---------------|
| Orientation | 00-03 | What the project is, what users experience, where every file lives |
| Installation | 04-07 | How the tool gets onto a user's computer and configures itself |
| Core pipeline | 08-11 | How news is fetched, formatted, deduplicated, and sent |
| Management | 12-13 | How users manage settings and automate daily delivery |
| Engineering | 14-18 | Security, testing, release packaging, troubleshooting, extending |

## Time estimate

- **Quick skim** (reading headers and summaries): ~2 hours
- **Thorough read** (following every code walkthrough): ~6-8 hours
- **Deep study** (reading + completing all labs): ~10-12 hours

You do not need to finish in one sitting. Each lesson is self-contained enough to pick up where you left off.

## Supplementary materials

After (or alongside) the numbered lessons, use these resources:

- **appendices/** — Quick-reference tables you can print or keep open in a tab
  - `command-reference.md` — Every command you can run, with flags and examples
  - `file-reference.md` — Every file in the repo with a one-line description
  - `glossary.md` — Definitions of technical terms used throughout the course
  - `security-checklist.md` — A checklist of every security measure in the project
- **diagrams/** — Visual flowcharts that complement the text
  - `install-flow.md` — What happens when a user runs the one-line installer
  - `runtime-flow.md` — What happens when main.py runs
  - `scheduling-flow.md` — How daily scheduling is installed on each OS
- **labs/** — Hands-on exercises
  - `01-run-a-dry-run.md` — Run the tool without sending an email
  - `02-trace-an-email-send.md` — Follow data from RSS to inbox
  - `03-follow-an-installer-run.md` — Watch the installer in action
  - `04-add-a-new-source.md` — Add a newspaper to the registry
  - `05-simulate-a-failure.md` — Break something on purpose and diagnose it

## Conventions used in this course

- **File paths** are written relative to the project root: `newsdigest/scraper.py` means the file at `<project-root>/newsdigest/scraper.py`
- **Code blocks** contain the actual source code from the repository, with commentary explaining each section
- **"Why?"** callouts explain the design decision behind a particular choice
- **"What if?"** callouts explore what would happen if the code were written differently
- **Key terms** are bolded the first time they appear and defined in the glossary
