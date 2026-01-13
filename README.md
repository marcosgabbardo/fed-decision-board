# Fed Decision Board

> AI-powered FOMC meeting simulator using Claude

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

Fed Decision Board is a multi-agent system that simulates Federal Open Market Committee (FOMC) meetings. Each agent represents a real Fed member with a persona based on their historical voting profile, policy preferences, and communication style. The system generates interest rate decision forecasts and meeting minutes in the official Fed format.

---

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Quick Start](#quick-start)
- [CLI Commands](#cli-commands)
- [Cost Management](#cost-management)
- [Architecture](#architecture)
- [Data Sources](#data-sources)
- [Output Formats](#output-formats)
- [FOMC Members](#fomc-members-2024-2025)
- [Examples](#examples)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [Disclaimer](#disclaimer)
- [License](#license)

---

## Features

- **12 FOMC Member Agents** — Realistic personas for all voting members with hawk/dove/neutral stances
- **Economic Data Integration** — Real-time data from FRED API (20+ economic indicators)
- **Trend Analysis** — Visual trend indicators (↑↓→) with historical values for context
- **Official-Format Minutes** — Meeting minutes in Markdown and PDF matching Fed's style
- **Dot Plot Projections** — Generate rate projection charts like the Fed's Summary of Economic Projections
- **Press Conference Simulation** — Q&A session with the Chair after decisions
- **Dissent Analysis** — Detailed analysis when members vote against the majority
- **Market Impact Estimates** — Projected effects on yields, equities, and currency
- **Hawk-Dove Tracker** — Historical stance tracking for each member
- **Cost Transparency** — Estimate API costs before running simulations
- **Smart Caching** — FRED API responses cached to minimize redundant calls

---

## Prerequisites

Before you begin, ensure you have the following installed:

### 1. Python 3.11+

Check your Python version:

```bash
python --version
# Should output: Python 3.11.x or higher
```

If not installed, download from [python.org](https://www.python.org/downloads/) or use your package manager.

### 2. uv (Recommended Package Manager)

[uv](https://github.com/astral-sh/uv) is an extremely fast Python package manager. Install it:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew (macOS)
brew install uv

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Verify installation:

```bash
uv --version
```

### 3. System Dependencies for PDF Generation

WeasyPrint requires system libraries for PDF generation:

**macOS:**
```bash
brew install pango libffi
```

**Ubuntu/Debian:**
```bash
sudo apt-get install libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0
```

**Windows:**
See [WeasyPrint Windows installation guide](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows)

### 4. API Keys

You'll need two API keys:

1. **Anthropic API Key** (required)
   - Go to [console.anthropic.com](https://console.anthropic.com/)
   - Sign up or log in
   - Navigate to API Keys and create a new key
   - Note: Using Claude Opus 4.5 incurs costs (~$2-5 per simulation)

2. **FRED API Key** (required, free)
   - Go to [fred.stlouisfed.org/docs/api/api_key.html](https://fred.stlouisfed.org/docs/api/api_key.html)
   - Create a free account
   - Request an API key (instant approval)

---

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/marcosgabbardo/fed-decision-board.git
cd fed-decision-board
```

### Step 2: Install Dependencies

Using uv (recommended):

```bash
uv sync
```

Or using pip:

```bash
pip install -e .
```

### Step 3: Verify Installation

```bash
# With uv (recommended)
uv run fed-board --help

# Or if you installed with pip and activated venv
fed-board --help
```

You should see the help menu with all available commands.

---

## Configuration

### Step 1: Create Environment File

```bash
cp .env.example .env
```

Or create `.env` manually:

```bash
touch .env
```

### Step 2: Add Your API Keys

Edit `.env` with your favorite editor:

```bash
# Fed Decision Board Configuration

# Anthropic API Key (required)
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# FRED API Key (required)
FRED_API_KEY=your-fred-key-here

# Model Configuration (optional)
# Default: claude-opus-4-5-20251101 (best quality)
# Alternatives: claude-sonnet-4-20250514 (faster, cheaper)
ANTHROPIC_MODEL=claude-opus-4-5-20251101

# Data Directory (optional)
DATA_DIR=./data

# Cache Settings (optional)
FRED_CACHE_TTL_MONTHLY=86400
FRED_CACHE_TTL_DAILY=3600

# Logging (optional)
LOG_LEVEL=INFO
```

### Step 3: Verify Configuration

```bash
uv run fed-board config show
```

---

## Quick Start

### Important: How to Run Commands

**Always use `uv run` before commands:**

```bash
uv run fed-board <command>
```

This ensures the correct Python environment and dependencies are used.

### Your First Simulation

#### 1. Estimate Costs (Recommended First Step)

Before running a simulation, check the estimated cost:

```bash
uv run fed-board estimate --year 2025
```

Output:
```
╭────────────────────── Anthropic API Cost Estimate ───────────────────────╮
│ Cost Estimate                                                            │
│                                                                          │
│ Model: Opus 4.5 (claude-opus-4-5-20251101)                               │
│ Members: 12                                                              │
│                                                                          │
│ Estimated tokens:                                                        │
│   Input:  ~42,000 tokens                                                 │
│   Output: ~21,600 tokens                                                 │
│                                                                          │
│ Estimated cost:                                                          │
│   Input:  $0.630                                                         │
│   Output: $1.620                                                         │
│   Total:  $2.25                                                          │
│                                                                          │
│ * Actual costs may vary based on response length                         │
│ * Use --members to estimate for specific members                         │
╰──────────────────────────────────────────────────────────────────────────╯

          Model Pricing (per 1M tokens)
┏━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┓
┃ Model                   ┃ Input  ┃ Output  ┃ Est. Cost (12 memb.) ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━┩
│ Opus 4.5 (current)      │ $15.00 │ $75.00  │ $2.25                │
│ Sonnet 4                │ $3.00  │ $15.00  │ $0.45                │
│ Haiku 3.5               │ $0.80  │ $4.00   │ $0.12                │
└─────────────────────────┴────────┴─────────┴──────────────────────┘
```

#### 2. Run the Simulation

```bash
uv run fed-board simulate --month 2025-01
```

You'll be prompted to confirm the cost:

```
╭────────────────────────── Anthropic API Cost ────────────────────────────╮
│ Cost Estimate                                                            │
│                                                                          │
│ Model: Opus 4.5                                                          │
│ Members: 12                                                              │
│                                                                          │
│ Estimated tokens:                                                        │
│   Input:  ~42,000 tokens                                                 │
│   Output: ~21,600 tokens                                                 │
│                                                                          │
│ Estimated cost:                                                          │
│   Input:  $0.630                                                         │
│   Output: $1.620                                                         │
│   Total:  $2.25                                                          │
│                                                                          │
│ * Actual costs may vary based on response length                         │
╰──────────────────────────────────────────────────────────────────────────╯
Do you want to proceed with this simulation? [y/N]: y
```

To skip the confirmation (e.g., in scripts):

```bash
uv run fed-board simulate --month 2025-01 --yes
# or
uv run fed-board simulate --month 2025-01 -y
```

**Simulation Output:**

After running a simulation, you'll see economic indicators with **trend analysis** (↑ rising, ↓ falling, → stable) and historical context:

```
╭───────────────────────────── Fed Decision Board ─────────────────────────────╮
│ FOMC Meeting Simulation                                                      │
│                                                                              │
│ Month: 2025-01                                                               │
│ Members: All voting members (12)                                             │
╰──────────────────────────────────────────────────────────────────────────────╯

╭─────────────────── Economic Indicators (as of 2025-01-15) ───────────────────╮
│ Inflation                                                                    │
│   Core PCE: 2.8% ↓ (prev: 2.9, 3.0)                                          │
│   CPI: 3.2% ↓ (prev: 3.4)  |  Core CPI: 3.3% ↓                               │
│                                                                              │
│ Labor Market                                                                 │
│   Unemployment: 4.1% ↑ (prev: 4.0)                                           │
│   Wage Growth: 4.0% ↓  |  Participation: 62.5% →                             │
│                                                                              │
│ Activity                                                                     │
│   GDP Growth: +2.8% ↑ (prev: 2.1, 1.6)                                       │
│   Retail Sales: +0.4% →  |  Industrial: +1.2% ↑                              │
│                                                                              │
│ Markets                                                                      │
│   Fed Funds: 4.25-4.50%  |  10Y: 4.6% ↑  |  2Y: 4.3% →                       │
│                                                                              │
│ Expectations                                                                 │
│   5Y Breakeven: 2.3% →  |  10Y Breakeven: 2.4% →  |  Sentiment: 74.0 ↑       │
╰──────────────────────────────────────────────────────────────────────────────╯

╭─────────────────────────────── Meeting Result ───────────────────────────────╮
│ Decision: HOLD                                                               │
│ New Target Range: 4.25-4.50%                                                 │
│ Vote: Unanimous (12-0)                                                       │
╰──────────────────────────────────────────────────────────────────────────────╯

Simulation saved to: data/simulations/2025-01.json
```

#### 3. Generate Meeting Minutes

```bash
# Markdown format
uv run fed-board minutes --month 2025-01 --format md

# PDF format
uv run fed-board minutes --month 2025-01 --format pdf

# Both formats
uv run fed-board minutes --month 2025-01 --format all
```

#### 4. View Results

```bash
# View markdown minutes
cat data/minutes/2025-01.md

# Open PDF (macOS)
open data/minutes/2025-01.pdf

# Open PDF (Linux)
xdg-open data/minutes/2025-01.pdf
```

---

## CLI Commands

### Command Reference

| Command | Description | Example |
|---------|-------------|---------|
| `simulate` | Run FOMC meeting simulation | `uv run fed-board simulate --month 2025-01` |
| `estimate` | Preview simulation cost without running | `uv run fed-board estimate --year 2025` |
| `minutes` | Generate meeting minutes | `uv run fed-board minutes --month 2025-01 --format pdf` |
| `dotplot` | Create rate projection dot plot | `uv run fed-board dotplot --year 2025` |
| `stance` | View hawk-dove positioning | `uv run fed-board stance --all` |
| `cache clear` | Clear FRED API cache | `uv run fed-board cache clear` |
| `cache stats` | View cache statistics | `uv run fed-board cache stats` |
| `config show` | Display current configuration | `uv run fed-board config show` |

### Detailed Command Usage

#### simulate

```bash
# Full simulation (all 12 voting members)
uv run fed-board simulate --month 2025-01

# Select specific members (faster & cheaper for testing)
uv run fed-board simulate --month 2025-01 --members powell,waller,bowman

# Verbose output (shows progress messages)
uv run fed-board simulate --month 2025-01 --verbose

# Debug mode (shows API call details)
uv run fed-board simulate --month 2025-01 --debug

# Skip cost confirmation
uv run fed-board simulate --month 2025-01 --yes

# Combined options (quick test)
uv run fed-board simulate --month 2025-01 --members powell,waller -y --debug
```

#### estimate

```bash
# Estimate for all voting members of a year
uv run fed-board estimate --year 2025

# Estimate with specific members (lower cost)
uv run fed-board estimate --members powell,waller,bowman
```

#### minutes

```bash
# Markdown only
uv run fed-board minutes --month 2025-01 --format md

# PDF only
uv run fed-board minutes --month 2025-01 --format pdf

# Both formats
uv run fed-board minutes --month 2025-01 --format all
```

#### dotplot

```bash
# Generate dot plot for year
uv run fed-board dotplot --year 2025

# Custom output path
uv run fed-board dotplot --year 2025 --output my-dotplot.png
```

#### cache

```bash
# View cache statistics
uv run fed-board cache stats

# Clear all cached FRED data
uv run fed-board cache clear
```

**Cache stats output:**
```
╭────────────────────────────── FRED Cache ────────────────────────────────╮
│ Cache Statistics                                                         │
│                                                                          │
│ Directory: data/cache/fred                                               │
│ Total files: 45                                                          │
│ Total size: 128.5 KB                                                     │
│ Valid entries: 42                                                        │
│ Expired entries: 3                                                       │
╰──────────────────────────────────────────────────────────────────────────╯
```

---

## Cost Management

### Understanding API Costs

Fed Decision Board uses Claude (Anthropic's AI) which charges per token:

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Quality |
|-------|----------------------|------------------------|---------|
| Claude Opus 4.5 | $15.00 | $75.00 | Highest |
| Claude Sonnet 4 | $3.00 | $15.00 | High |
| Claude Haiku 3.5 | $0.80 | $4.00 | Good |

### Estimated Costs Per Simulation

| Configuration | Estimated Cost |
|---------------|----------------|
| Full simulation (12 members, Opus 4.5) | ~$2.25 |
| Full simulation (12 members, Sonnet 4) | ~$0.45 |
| Partial simulation (2 members, Opus 4.5) | ~$0.38 |
| Partial simulation (4 members, Opus 4.5) | ~$0.75 |

### Cost Control Strategies

1. **Always estimate first:**
   ```bash
   uv run fed-board estimate --year 2025
   ```

2. **Use fewer members for testing:**
   ```bash
   uv run fed-board simulate --month 2025-01 --members powell,waller
   ```

3. **Use a cheaper model for drafts:**
   ```bash
   # In .env
   ANTHROPIC_MODEL=claude-sonnet-4-20250514
   ```

4. **Skip confirmation in scripts:**
   ```bash
   uv run fed-board simulate --month 2025-01 -y
   ```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLI Interface                            │
│                    (Typer + Rich)                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Meeting Orchestrator                         │
│  - Coordinates FOMC meeting flow                                │
│  - Manages member deliberation sequence                         │
│  - Consolidates votes and generates outputs                     │
└─────────────────────────────────────────────────────────────────┘
           │                    │                    │
           ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Data Service   │  │  Agent Service  │  │ Output Service  │
│  - FRED API     │  │  - 12 Members   │  │  - Minutes PDF  │
│  - Caching      │  │  - Claude API   │  │  - Dot Plot     │
│  - Indicators   │  │  - Personas     │  │  - JSON/MD      │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### Directory Structure

```
fed-decision-board/
├── src/fed_board/
│   ├── __init__.py
│   ├── cli.py              # CLI commands with Typer
│   ├── config.py           # Configuration with Pydantic
│   ├── agents/             # FOMC member agents
│   │   ├── base.py         # Base agent class
│   │   ├── personas.py     # 12 member definitions
│   │   ├── orchestrator.py # Meeting coordination
│   │   └── prompts/        # System prompts
│   │       └── system.py
│   ├── data/               # Economic data services
│   │   ├── fred.py         # FRED API client
│   │   ├── indicators.py   # Economic indicators
│   │   └── cache.py        # Caching layer
│   ├── outputs/            # Output generation
│   │   ├── minutes.py      # Markdown minutes
│   │   ├── pdf.py          # PDF generation
│   │   ├── dotplot.py      # Dot plot charts
│   │   └── templates/      # HTML/CSS templates
│   └── models/             # Data models
│       ├── member.py       # FOMC member model
│       └── meeting.py      # Meeting/vote models
├── data/                   # Generated data (gitignored)
│   ├── cache/              # API response cache
│   ├── simulations/        # Raw simulation JSON
│   ├── minutes/            # Generated minutes
│   └── dotplots/           # Generated charts
├── tests/                  # Test suite
├── .env                    # Your API keys (gitignored)
├── .env.example            # Template for .env
├── pyproject.toml          # Project configuration
└── README.md               # This file
```

---

## Data Sources

### FRED API Indicators

The system fetches real-time economic data from the Federal Reserve Economic Data (FRED) API:

| Category | Indicators |
|----------|------------|
| **Inflation** | CPI YoY, Core CPI YoY, PCE YoY, Core PCE YoY |
| **Employment** | Unemployment Rate, Nonfarm Payrolls, Labor Force Participation, Wage Growth |
| **Activity** | GDP Growth, Retail Sales, Industrial Production |
| **Markets** | Fed Funds Rate, 10Y Treasury, 2Y Treasury, Fed Funds Target Range |
| **Expectations** | Consumer Sentiment, 5Y Breakeven Inflation |

Data is cached locally to minimize API calls:
- Monthly data: 24-hour cache
- Daily data: 1-hour cache

---

## Output Formats

### Meeting Minutes (Markdown/PDF)

Generated minutes follow the official FOMC structure:

1. Developments in Financial Markets and Open Market Operations
2. Staff Review of the Economic Situation
3. Staff Economic Outlook
4. Participants' Views on Current Conditions and the Economic Outlook
5. Committee Policy Action

PDF output replicates the official Fed visual style and includes an AI disclaimer.

### Dot Plot

The dot plot shows individual member projections for the federal funds rate:
- Current year
- Next year
- Two years ahead
- Longer run

### Simulation Data (JSON)

Raw simulation data is stored in JSON format for analysis and replay.

---

## FOMC Members (2024-2025)

### Board of Governors (Always Vote)

| Member | Role | Stance | Priorities |
|--------|------|--------|------------|
| Jerome H. Powell | Chair | Neutral | Balanced approach, data-dependent |
| Philip N. Jefferson | Vice Chair | Dove | Employment, financial stability |
| Michelle W. Bowman | Governor | Hawk | Inflation control, banking regulation |
| Christopher J. Waller | Governor | Hawk | Inflation, labor market |
| Lisa D. Cook | Governor | Dove | Employment, inclusive growth |
| Adriana D. Kugler | Governor | Dove | Labor market, international |
| Michael S. Barr | Vice Chair for Supervision | Neutral | Financial stability, regulation |

### Reserve Bank Presidents (Rotating Votes)

| Member | Bank | Stance |
|--------|------|--------|
| John C. Williams | New York (permanent) | Neutral |
| Raphael Bostic | Atlanta | Dove |
| Mary Daly | San Francisco | Dove |
| Beth Hammack | Cleveland | Hawk |
| Alberto Musalem | St. Louis | Hawk |
| Jeffrey Schmid | Kansas City | Hawk |

---

## Examples

### Basic Workflow

```bash
# 1. Check costs
uv run fed-board estimate --month 2025-03

# 2. Run simulation
uv run fed-board simulate --month 2025-03

# 3. Generate all outputs
uv run fed-board minutes --month 2025-03 --format all
uv run fed-board dotplot --year 2025
uv run fed-board impact --month 2025-03

# 4. View results
cat data/minutes/2025-03.md
open data/minutes/2025-03.pdf
open data/dotplots/2025.png
```

### Quick Test (Lower Cost)

```bash
# Test with just 3 members
uv run fed-board simulate --month 2025-03 --members powell,waller,williams -y
```

### Batch Simulation Script

```bash
#!/bin/bash
# simulate-year.sh

for month in 01 03 05 06 07 09 11 12; do
    echo "Simulating 2025-$month..."
    uv run fed-board simulate --month 2025-$month -y
    uv run fed-board minutes --month 2025-$month --format all
done

uv run fed-board dotplot --year 2025
uv run fed-board history --year 2025 --export csv
```

---

## Development

### Setup Development Environment

```bash
# Install with dev dependencies
uv sync --all-extras

# Or with pip
pip install -e ".[dev]"
```

### Run Tests

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=fed_board --cov-report=html

# Specific test file
uv run pytest tests/test_personas.py

# Verbose output
uv run pytest -v
```

### Code Quality

```bash
# Linting
uv run ruff check src/

# Type checking
uv run mypy src/

# Format code
uv run ruff format src/
```

---

## Troubleshooting

### "command not found: fed-board"

You need to use `uv run` to execute commands:

```bash
# Correct
uv run fed-board simulate --month 2025-01

# Incorrect (won't work unless venv is activated)
fed-board simulate --month 2025-01
```

Alternatively, activate the virtual environment:

```bash
source .venv/bin/activate
fed-board simulate --month 2025-01
```

### "ANTHROPIC_API_KEY not set"

Ensure your `.env` file exists and contains your API key:

```bash
cat .env | grep ANTHROPIC_API_KEY
```

### "FRED API error"

Check your FRED API key is valid:

```bash
curl "https://api.stlouisfed.org/fred/series?series_id=GDP&api_key=YOUR_KEY&file_type=json"
```

### PDF generation fails

Ensure WeasyPrint dependencies are installed:

```bash
# macOS
brew install pango libffi

# Ubuntu/Debian
sudo apt-get install libpango-1.0-0 libpangocairo-1.0-0
```

### High API costs

- Use `estimate` command before running simulations
- Select fewer members with `--members`
- Use a cheaper model in `.env` (e.g., `claude-sonnet-4-20250514`)

---

## Disclaimer

**This is a simulation tool for educational and research purposes only.**

- This software does not represent actual Federal Reserve decisions or policy
- Simulated outputs should not be used for trading or investment decisions
- The personas are approximations based on public information and may not accurately reflect actual member views
- All generated content is clearly marked as AI-generated
- API costs are estimates and actual charges may vary

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- Economic data provided by [FRED](https://fred.stlouisfed.org/) (Federal Reserve Economic Data)
- AI capabilities powered by [Claude](https://www.anthropic.com/claude) from Anthropic
- Inspired by the Federal Reserve's commitment to transparency in monetary policy

---

## Support

- **Issues:** [GitHub Issues](https://github.com/marcosgabbardo/fed-decision-board/issues)
- **Discussions:** [GitHub Discussions](https://github.com/marcosgabbardo/fed-decision-board/discussions)
