# Microsoft Certification Exam Prep

A VS Code agent-powered system for structured Microsoft certification exam preparation. Uses GitHub Copilot custom agents to orchestrate research, study planning, and daily drill sessions.

## How It Works

Three custom agents work together:

| Agent | Role |
|-------|------|
| **Microsoft Certification Preparator** | Main orchestrator — handles setup, planning, and session dispatch |
| **CertResearcher** | Subagent — researches exam topics, finds practice questions, verifies exam existence |
| **CertSessionRunner** | Subagent — runs daily study sessions with teaching, quizzes, and progress tracking |

## Quick Start

1. Open this repo in VS Code with GitHub Copilot enabled.
2. Invoke the agent: `@Microsoft Certification Preparator Setup DP-800` (or any exam code).
3. The agent will:
   - Verify the exam exists on Microsoft Learn
   - Fetch all topics/skills measured
   - Find 100+ practice questions
   - Locate the official training course
   - Deploy the CLI quiz runner
4. Say `Make a plan` to generate a personalized study schedule.
5. Say `Start today's session` to begin studying.

## Workspace Structure

```
├── .github/agents/               # Agent definitions (VS Code custom agents)
│   ├── microsoft-certification-preparator.agent.md
│   ├── cert-researcher.agent.md
│   ├── cert-session-runner.agent.md
│   └── quiz_runner.py            # Master copy of the CLI quiz tool
│
├── <Exam> Prep/                  # Per-exam folder (e.g., "DP-800 Prep/")
│   ├── topics.md                 # Exam topic breakdown with domain weights
│   ├── questions.json            # Practice questions (100+ per exam)
│   ├── plan.md                   # Personalized study schedule
│   ├── progress.md               # Session-by-session progress tracker
│   ├── training-course.md        # Official MS Learn course link + learning paths
│   ├── quiz_runner.py            # Deployed copy of the quiz tool
│   ├── session-results.json      # Latest quiz results (read by agent)
│   └── sessions/                 # Per-day reference notes
│       ├── day-01-topic-slug.md
│       └── ...
```

## Quiz Runner

Standalone Python CLI tool (zero external dependencies) for interactive practice drills. Runs in the terminal to save chat context window.

### Usage

```bash
python quiz_runner.py questions.json --domain 1         # All questions from domain 1
python quiz_runner.py questions.json --topic "1.1"      # Questions matching topic prefix
python quiz_runner.py questions.json --ids q001,q005    # Specific question IDs
python quiz_runner.py questions.json --cross 1,2        # Cross-topic review mix
python quiz_runner.py questions.json --all              # Full mock exam mode
python quiz_runner.py questions.json --all --shuffle    # Randomized mock exam
```

### Features

- Interactive Q&A with immediate correct/wrong feedback and explanations
- Supports multiple question types: multiple choice, multi-select, dropdown, yes/no
- Color-coded terminal output with score summary
- Saves results to `session-results.json` for agent analysis
- Filtering by domain, topic, question IDs, or cross-topic mode
- `--shuffle` and `--limit` flags for varied practice

## Study Workflow

1. **Setup** — Agent researches the exam and creates all prep materials
2. **Training Course** — Complete the official Microsoft Learn course (agent reminds you)
3. **Plan** — Agent creates a weighted study schedule based on your availability and weak areas
4. **Daily Sessions** — Agent teaches topics, runs quizzes via CLI, tracks progress, and adapts
5. **Review** — Cross-topic questions from past sessions reinforce retention via spaced repetition

## Requirements

- VS Code with GitHub Copilot (agent mode)
- Python 3.7+ (for quiz runner)
