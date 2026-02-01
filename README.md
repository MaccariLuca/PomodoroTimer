# 🍅 Pomodoro Focus Timer

A **terminal-based Pomodoro timer** built in pure Python with deep analytics, session tracking, streaks, and a colourful TUI — no dependencies required.

![Python](https://img.shields.io/badge/Python-3.7%2B-blue?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Dependencies](https://img.shields.io/badge/Dependencies-None-brightgreen?style=flat-square)

---

## ✨ Features

- **Full Pomodoro cycle** — Focus → Short Break → Long Break, auto-managed
- **Live countdown timer** with animated progress bar and percentage
- **Graceful interrupts** — Ctrl+C lets you pause, resume, or restart (no lost work)
- **Session labelling** — Tag what you're working on for each session
- **Persistent storage** — All sessions saved to `~/.pomodoro/` as JSON
- **Rich statistics dashboard:**
  - Total focus hours & completion rate
  - 🔥 Current & best streaks (consecutive days)
  - 7-day heatmap with colour-coded intensity
  - Hourly productivity chart (when are you most focused?)
  - Recent session log with status
- **Fully configurable** — Adjust all durations and daily goals interactively
- **Motivational quotes** — A random quote on every menu screen (toggleable)
- **CLI shortcuts** — Run commands directly from the terminal

---

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/yourusername/pomodoro-timer.git
cd pomodoro-timer

# Run
python pomodoro_timer.py
```

That's it. No `pip install`, no virtual environment needed.

---

## 📖 Usage

### Interactive Menu (default)

```bash
python pomodoro_timer.py
```

Launches the main menu where you can start sessions, view stats, and configure settings.

### CLI Shortcuts

| Command | Description |
|---|---|
| `python pomodoro_timer.py start` | Quick-start a focus session |
| `python pomodoro_timer.py stats` | Open the statistics dashboard |
| `python pomodoro_timer.py config` | Edit configuration |
| `python pomodoro_timer.py cycle` | Run a full Pomodoro cycle (focus → break → repeat) |

### During a Timer

| Key | Action |
|---|---|
| `Ctrl+C` | Pause the timer — choose to resume, restart, or stop |
| `Enter` | Confirm / continue after a session ends |

---

## ⚙️ Configuration

All settings are edited interactively via the menu (`5 → Config`), or you can manually edit `~/.pomodoro/config.json`:

```json
{
  "focus_minutes": 25,
  "short_break_minutes": 5,
  "long_break_minutes": 20,
  "sessions_before_long_break": 4,
  "daily_goal_sessions": 8,
  "motivational_quotes": true
}
```

---

## 📊 Data Storage

All data lives in `~/.pomodoro/`:

| File | Purpose |
|---|---|
| `config.json` | User configuration |
| `sessions.json` | Full history of all logged sessions |

Each session record stores the type, planned & actual duration, completion status, label, and timestamp — giving the stats engine everything it needs to compute streaks, heatmaps, and hourly breakdowns.

---

## 🏗️ Architecture

The app is structured as a single-file script for simplicity and portability:

| Section | Responsibility |
|---|---|
| `Data Layer` | JSON read/write, session logging |
| `Timer Engine` | Countdown loop, signal handling, resume logic |
| `Statistics Engine` | Streak calculation, daily/hourly aggregation |
| `ASCII Charts` | Heatmaps, bar charts rendered in the terminal |
| `Screens` | Menu, stats dashboard, config editor |
| `Pomodoro Cycle` | Orchestrates the focus → break loop |

---

## 📋 Requirements

- **Python 3.7+** (uses only the standard library)
- A terminal that supports ANSI escape codes (macOS Terminal, Windows Terminal, Linux)

> On older Windows `cmd.exe`, colours may not render. Use **Windows Terminal** or **PowerShell** for the best experience.

---

## 📝 License

MIT — do whatever you want, just don't blame me if you become too productive.
