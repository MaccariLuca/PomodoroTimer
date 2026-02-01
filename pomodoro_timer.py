#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║           🍅  POMODORO FOCUS TIMER  🍅                       ║
║  A terminal-based productivity timer with deep analytics     ║
║  Tracks sessions, streaks, and paints your focus history.    ║
╚══════════════════════════════════════════════════════════════╝

Usage:
    python pomodoro_timer.py            → Start interactive menu
    python pomodoro_timer.py start      → Quick-start a focus session
    python pomodoro_timer.py stats      → Show statistics dashboard
    python pomodoro_timer.py config     → Edit configuration

Dependencies: None (pure Python 3.7+ stdlib)
Data stored in: ~/.pomodoro/sessions.json  &  ~/.pomodoro/config.json
"""

import os
import sys
import json
import time
import signal
import math
import random
import argparse
from datetime import datetime, timedelta, date
from pathlib import Path
from collections import defaultdict


# ─────────────────────────────────────────────
#  ANSI COLOUR PALETTE
# ─────────────────────────────────────────────
class C:
    """ANSI escape codes for terminal colours."""
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    # Foreground
    RED     = "\033[38;5;196m"
    ORANGE  = "\033[38;5;208m"
    YELLOW  = "\033[38;5;226m"
    GREEN   = "\033[38;5;46m"
    CYAN    = "\033[38;5;51m"
    BLUE    = "\033[38;5;81m"
    PURPLE  = "\033[38;5;141m"
    PINK    = "\033[38;5;205m"
    WHITE   = "\033[38;5;255m"
    GRAY    = "\033[38;5;245m"
    DARKGRAY= "\033[38;5;236m"
    # Background
    BG_DARK = "\033[48;5;235m"
    BG_RED  = "\033[48;5;52m"
    BG_GREEN= "\033[48;5;22m"


def supports_color() -> bool:
    """Detect if the terminal supports ANSI colours."""
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


# ─────────────────────────────────────────────
#  DATA LAYER  –  persistence via JSON files
# ─────────────────────────────────────────────
DATA_DIR = Path.home() / ".pomodoro"

DEFAULT_CONFIG = {
    "focus_minutes": 25,
    "short_break_minutes": 5,
    "long_break_minutes": 20,
    "sessions_before_long_break": 4,
    "daily_goal_sessions": 8,
    "motivational_quotes": True,
}

SESSION_TYPES = {"focus": "🍅 Focus", "short": "☕ Short Break", "long": "🏖  Long Break"}


def ensure_data_dir():
    DATA_DIR.mkdir(exist_ok=True)


def load_config() -> dict:
    ensure_data_dir()
    path = DATA_DIR / "config.json"
    if path.exists():
        with open(path) as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    return dict(DEFAULT_CONFIG)


def save_config(config: dict):
    ensure_data_dir()
    with open(DATA_DIR / "config.json", "w") as f:
        json.dump(config, f, indent=2)


def load_sessions() -> list:
    ensure_data_dir()
    path = DATA_DIR / "sessions.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return []


def save_sessions(sessions: list):
    ensure_data_dir()
    with open(DATA_DIR / "sessions.json", "w") as f:
        json.dump(sessions, f, indent=2)


def log_session(session_type: str, planned_minutes: int, actual_minutes: int, completed: bool, label: str = ""):
    sessions = load_sessions()
    sessions.append({
        "type": session_type,
        "planned_minutes": planned_minutes,
        "actual_minutes": round(actual_minutes, 2),
        "completed": completed,
        "label": label,
        "started_at": datetime.now().isoformat(),
    })
    save_sessions(sessions)


# ─────────────────────────────────────────────
#  MOTIVATIONAL QUOTES
# ─────────────────────────────────────────────
QUOTES = [
    ("The secret of getting ahead is getting started.", "Mark Twain"),
    ("Focus is the modern rarity.", "Cal Newport"),
    ("Done is better than perfect.", "Google"),
    ("We are what we repeatedly do.", "Will Durant"),
    ("The best time to plant a tree was 20 years ago.", "Chinese Proverb"),
    ("Deep work is rare, valuable, and increasingly rare.", "Cal Newport"),
    ("In the middle of difficulty lies opportunity.", "Albert Einstein"),
    ("It does not matter how slowly you go as long as you do not stop.", "Confucius"),
    ("The only way to do great work is to love what you do.", "Steve Jobs"),
    ("Small steps lead to big changes.", "Unknown"),
    ("Productivity is never an accident.", "J. Willard Marriott"),
    ("Either you run the day or the day runs you.", "Jim Rohn"),
    ("An hour of planning saves 10 hours in execution.", "Benjamin Franklin"),
    ("You don't have to be great to start, but you have to start to be great.", "Zig Ziglar"),
    ("Focus on progress, not perfection.", "Unknown"),
]


def get_quote() -> tuple:
    return random.choice(QUOTES)


# ─────────────────────────────────────────────
#  TERMINAL UTILITIES
# ─────────────────────────────────────────────
def clear():
    os.system("cls" if os.name == "nt" else "clear")


def hr(char="─", width=62):
    print(f"{C.DARKGRAY}{char * width}{C.RESET}")


def center_print(text, width=62):
    print(text.center(width))


def input_prompt(prompt_text: str) -> str:
    print(f"  {C.CYAN}▸{C.RESET} {C.WHITE}{prompt_text}{C.RESET}", end=" ")
    try:
        return input().strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return ""


# ─────────────────────────────────────────────
#  TIMER ENGINE  –  with graceful interrupt
# ─────────────────────────────────────────────
class TimerInterrupt(Exception):
    """Raised when user presses Ctrl+C during a timer."""
    pass


def run_timer(session_type: str, minutes: int, label: str = "") -> bool:
    """
    Run a countdown timer.  Returns True if completed, False if interrupted.
    """
    total_seconds = minutes * 60
    start_time = time.time()
    interrupted = False

    # map type → colour
    colours = {"focus": C.RED, "short": C.GREEN, "long": C.BLUE}
    col = colours.get(session_type, C.WHITE)

    # Signal handler for Ctrl+C
    original_handler = signal.getsignal(signal.SIGINT)

    def _handler(sig, frame):
        raise TimerInterrupt()

    signal.signal(signal.SIGINT, _handler)

    try:
        while True:
            elapsed = time.time() - start_time
            remaining = total_seconds - elapsed

            if remaining <= 0:
                break

            mins, secs = divmod(int(remaining), 60)

            # Progress bar
            progress = 1 - (remaining / total_seconds)
            bar_width = 40
            filled = int(bar_width * progress)
            empty = bar_width - filled

            # Pulse effect – the colour intensity shifts every second
            pulse = "█" * filled + "░" * empty

            # Build the display frame
            clear()
            print()
            print(f"  {C.BOLD}{C.WHITE}{'─' * 58}{C.RESET}")
            print(f"  {C.BOLD}{col}  {SESSION_TYPES[session_type]}{C.RESET}", end="")
            if label:
                print(f"  {C.DIM}{C.GRAY}— {label}{C.RESET}", end="")
            print()
            print(f"  {C.BOLD}{C.WHITE}{'─' * 58}{C.RESET}")
            print()

            # Big time display
            time_str = f"{mins:02d} : {secs:02d}"
            print(f"       {C.BOLD}{col}{time_str}{C.RESET}")
            print()

            # Progress bar
            print(f"       [{col}{pulse}{C.RESET}]  {C.GRAY}{int(progress*100)}%{C.RESET}")
            print()

            # Elapsed
            e_mins, e_secs = divmod(int(elapsed), 60)
            print(f"       {C.DIM}{C.GRAY}Elapsed: {e_mins:02d}:{e_secs:02d}  |  "
                  f"Remaining: {mins:02d}:{secs:02d}{C.RESET}")
            print()
            print(f"       {C.DIM}{C.GRAY}Press Ctrl+C to pause / stop{C.RESET}")
            print()

            sys.stdout.flush()
            time.sleep(1)

    except TimerInterrupt:
        interrupted = True
    finally:
        signal.signal(signal.SIGINT, original_handler)

    actual_minutes = (time.time() - start_time) / 60

    if not interrupted:
        # ✅ Timer completed
        clear()
        print()
        print(f"  {C.BOLD}{C.GREEN}  ✅  Session Complete!{C.RESET}")
        print(f"  {C.GRAY}  You finished {minutes} minutes of {SESSION_TYPES[session_type]}.{C.RESET}")
        print()
        log_session(session_type, minutes, actual_minutes, completed=True, label=label)
        input_prompt("Press Enter to continue…")
        return True
    else:
        # ⏸  Timer interrupted
        clear()
        print()
        print(f"  {C.BOLD}{C.ORANGE}  ⏸  Session Interrupted{C.RESET}")
        print(f"  {C.GRAY}  {int(actual_minutes)}m {int((actual_minutes % 1) * 60)}s completed out of {minutes} min.{C.RESET}")
        print()
        print(f"  What do you want to do?")
        print(f"    {C.GREEN}1{C.RESET}) Continue timer (resume)")
        print(f"    {C.YELLOW}2{C.RESET}) Restart timer from scratch")
        print(f"    {C.RED}3{C.RESET}) Stop & save partial session")
        print()

        choice = input_prompt("Choice [1/2/3]:")

        if choice == "1":
            # Resume: subtract already elapsed time
            remaining_minutes = (total_seconds - (actual_minutes * 60)) / 60
            if remaining_minutes > 0.1:
                return run_timer_simple(session_type, remaining_minutes, label)
            return True

        elif choice == "2":
            return run_timer(session_type, minutes, label)

        else:
            # Save partial
            log_session(session_type, minutes, actual_minutes, completed=False, label=label)
            print(f"  {C.GRAY}  Partial session saved.{C.RESET}")
            input_prompt("Press Enter to continue…")
            return False


def run_timer_simple(session_type: str, minutes: float, label: str = "") -> bool:
    """Simple non-resumable timer used for resumed sessions."""
    total_seconds = minutes * 60
    start_time = time.time()
    colours = {"focus": C.RED, "short": C.GREEN, "long": C.BLUE}
    col = colours.get(session_type, C.WHITE)

    original_handler = signal.getsignal(signal.SIGINT)
    def _handler(sig, frame):
        raise TimerInterrupt()
    signal.signal(signal.SIGINT, _handler)

    try:
        while True:
            elapsed = time.time() - start_time
            remaining = total_seconds - elapsed
            if remaining <= 0:
                break
            mins, secs = divmod(int(remaining), 60)
            progress = 1 - (remaining / total_seconds)
            bar_width = 40
            filled = int(bar_width * progress)
            pulse = "█" * filled + "░" * (bar_width - filled)

            clear()
            print()
            print(f"  {C.BOLD}{col}  {SESSION_TYPES[session_type]} (resumed){C.RESET}")
            print()
            print(f"       {C.BOLD}{col}{mins:02d} : {secs:02d}{C.RESET}")
            print(f"       [{col}{pulse}{C.RESET}]  {C.GRAY}{int(progress*100)}%{C.RESET}")
            print(f"       {C.DIM}{C.GRAY}Ctrl+C to stop{C.RESET}")
            print()
            sys.stdout.flush()
            time.sleep(1)

    except TimerInterrupt:
        actual = (time.time() - start_time) / 60
        log_session(session_type, minutes, actual, completed=False, label=label)
        print(f"\n  {C.ORANGE}  ⏸  Stopped.{C.RESET}")
        input_prompt("Press Enter…")
        return False
    finally:
        signal.signal(signal.SIGINT, original_handler)

    actual = (time.time() - start_time) / 60
    log_session(session_type, minutes, actual, completed=True, label=label)
    clear()
    print(f"\n  {C.GREEN}  ✅  Session Complete!{C.RESET}")
    input_prompt("Press Enter…")
    return True


# ─────────────────────────────────────────────
#  STATISTICS ENGINE
# ─────────────────────────────────────────────
def compute_stats(sessions: list) -> dict:
    """Compute rich analytics from session history."""
    if not sessions:
        return {}

    focus_sessions = [s for s in sessions if s["type"] == "focus"]
    completed_focus = [s for s in focus_sessions if s["completed"]]

    total_focus_minutes = sum(s["actual_minutes"] for s in focus_sessions)
    total_completed_focus = sum(s["actual_minutes"] for s in completed_focus)
    completion_rate = len(completed_focus) / len(focus_sessions) * 100 if focus_sessions else 0

    # Daily breakdown
    daily = defaultdict(lambda: {"sessions": 0, "minutes": 0.0, "completed": 0})
    for s in focus_sessions:
        d = s["started_at"][:10]
        daily[d]["sessions"] += 1
        daily[d]["minutes"] += s["actual_minutes"]
        if s["completed"]:
            daily[d]["completed"] += 1

    # Hourly breakdown (which hours are you most productive?)
    hourly = defaultdict(lambda: {"sessions": 0, "minutes": 0.0})
    for s in focus_sessions:
        hour = int(s["started_at"][11:13])
        hourly[hour]["sessions"] += 1
        hourly[hour]["minutes"] += s["actual_minutes"]

    # Streak calculation (consecutive days with ≥1 completed focus session)
    sorted_days = sorted(daily.keys())
    current_streak = 0
    best_streak = 0
    streak = 0
    today_str = date.today().isoformat()

    for i, day in enumerate(sorted_days):
        if daily[day]["completed"] > 0:
            if i == 0:
                streak = 1
            else:
                prev = sorted_days[i - 1]
                expected_prev = (datetime.strptime(day, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
                streak = streak + 1 if prev == expected_prev else 1
            best_streak = max(best_streak, streak)
        else:
            streak = 0

    # Current streak: count backwards from today
    current_streak = 0
    check_date = date.today()
    for _ in range(365):
        ds = check_date.isoformat()
        if ds in daily and daily[ds]["completed"] > 0:
            current_streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    # Best day
    best_day = max(daily.items(), key=lambda x: x[1]["minutes"]) if daily else (None, None)

    # Weekly totals (last 7 days)
    week_minutes = 0.0
    week_sessions = 0
    for i in range(7):
        d = (date.today() - timedelta(days=i)).isoformat()
        if d in daily:
            week_minutes += daily[d]["minutes"]
            week_sessions += daily[d]["sessions"]

    return {
        "total_focus_minutes": total_focus_minutes,
        "total_completed_minutes": total_completed_focus,
        "total_focus_sessions": len(focus_sessions),
        "completed_focus_sessions": len(completed_focus),
        "completion_rate": completion_rate,
        "current_streak": current_streak,
        "best_streak": best_streak,
        "daily": dict(daily),
        "hourly": dict(hourly),
        "best_day": best_day,
        "week_minutes": week_minutes,
        "week_sessions": week_sessions,
        "first_session_date": sessions[0]["started_at"][:10] if sessions else None,
    }


# ─────────────────────────────────────────────
#  ASCII CHARTS
# ─────────────────────────────────────────────
def render_bar_chart(data: dict, title: str, labels: list, value_key: str,
                     max_bars: int = 24, bar_char="█", width: int = 30, color=C.CYAN) -> str:
    """Generic horizontal bar chart renderer."""
    lines = []
    lines.append(f"  {C.BOLD}{C.WHITE}{title}{C.RESET}")
    lines.append(f"  {C.DARKGRAY}{'─' * 58}{C.RESET}")

    # Filter and sort
    items = [(lbl, data.get(lbl, {}).get(value_key, 0)) for lbl in labels if data.get(lbl, {}).get(value_key, 0) > 0]
    items = items[-max_bars:]  # last N items

    if not items:
        lines.append(f"  {C.GRAY}  No data available.{C.RESET}")
        return "\n".join(lines)

    max_val = max(v for _, v in items) if items else 1

    for label, val in items:
        bar_len = int((val / max_val) * width) if max_val > 0 else 0
        bar = bar_char * bar_len
        lines.append(f"  {C.GRAY}{label:>12}{C.RESET}  {color}{bar}{C.RESET}  {C.WHITE}{val:.1f}{C.RESET}")

    return "\n".join(lines)


def render_weekly_heatmap(daily: dict) -> str:
    """Render a 7-day heatmap of focus minutes."""
    lines = []
    lines.append(f"  {C.BOLD}{C.WHITE}Last 7 Days Heatmap{C.RESET}")
    lines.append(f"  {C.DARKGRAY}{'─' * 58}{C.RESET}")

    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    max_minutes = 120  # cap for colour scaling

    for i in range(6, -1, -1):
        d = (date.today() - timedelta(days=i)).isoformat()
        day_obj = datetime.strptime(d, "%Y-%m-%d")
        day_name = day_names[day_obj.weekday()]
        is_today = (i == 0)
        minutes = daily.get(d, {}).get("minutes", 0)
        completed = daily.get(d, {}).get("completed", 0)

        # Colour intensity based on minutes (0→dim, 120+→bright green)
        intensity = min(minutes / max_minutes, 1.0)
        if minutes == 0:
            block_color = C.DARKGRAY
            block = "░░░░░░░░░░░░░░░░░░░░"
        elif intensity < 0.25:
            block_color = "\033[38;5;22m"   # dark green
            block = "█" * int(intensity * 20 / 0.25)
            block += "░" * (20 - len(block))
        elif intensity < 0.5:
            block_color = "\033[38;5;28m"   # medium green
            block = "█" * int(intensity * 20 / 0.5)
            block += "░" * (20 - len(block))
        elif intensity < 0.75:
            block_color = "\033[38;5;46m"   # bright green
            block = "█" * int(intensity * 20 / 0.75)
            block += "░" * (20 - len(block))
        else:
            block_color = C.GREEN
            block = "████████████████████"

        today_marker = f"{C.YELLOW}◀ today{C.RESET}" if is_today else ""
        lines.append(
            f"  {C.GRAY}{day_name:>4}{C.RESET}  "
            f"{block_color}{block}{C.RESET}  "
            f"{C.WHITE}{minutes:>5.1f}m{C.RESET}  "
            f"{C.GRAY}({completed} done){C.RESET}  {today_marker}"
        )

    return "\n".join(lines)


def render_hourly_chart(hourly: dict) -> str:
    """Bar chart of focus minutes by hour of day."""
    labels = [f"{h:02d}:00" for h in range(24)]
    return render_bar_chart(hourly, "Productivity by Hour", labels, "minutes", max_bars=24, width=24, color=C.PURPLE)


# ─────────────────────────────────────────────
#  SCREENS
# ─────────────────────────────────────────────
def screen_header():
    print()
    print(f"  {C.BOLD}{C.RED}🍅{C.RESET}{C.BOLD}{C.WHITE}  POMODORO FOCUS TIMER{C.RESET}  {C.DIM}{C.GRAY}v1.0{C.RESET}")
    hr()


def screen_main_menu():
    config = load_config()
    sessions = load_sessions()
    stats = compute_stats(sessions)

    clear()
    screen_header()
    print()

    # Quick stats bar
    streak = stats.get("current_streak", 0)
    today_str = date.today().isoformat()
    today_data = stats.get("daily", {}).get(today_str, {"sessions": 0, "completed": 0, "minutes": 0.0})
    goal = config["daily_goal_sessions"]

    print(f"  {C.GRAY}  🔥 Streak: {C.YELLOW}{streak} day{'s' if streak != 1 else ''}{C.RESET}"
          f"    {C.GRAY}📅 Today: {C.WHITE}{today_data['completed']}/{goal}{C.RESET}"
          f"    {C.GRAY}⏱  {C.WHITE}{today_data['minutes']:.0f} min{C.RESET}")
    print()
    hr()
    print()

    # Motivational quote
    if config.get("motivational_quotes", True):
        quote, author = get_quote()
        print(f'  {C.DIM}{C.GRAY}\u201c{quote}\u201d{C.RESET}')
        print(f"  {C.DIM}{C.GRAY}  — {author}{C.RESET}")
        print()

    print(f"  {C.BOLD}{C.WHITE}What do you want to do?{C.RESET}")
    print()
    print(f"    {C.RED}1{C.RESET})  🍅  Start Focus Session       ({config['focus_minutes']} min)")
    print(f"    {C.GREEN}2{C.RESET})  ☕  Short Break              ({config['short_break_minutes']} min)")
    print(f"    {C.BLUE}3{C.RESET})  🏖   Long Break               ({config['long_break_minutes']} min)")
    print(f"    {C.PURPLE}4{C.RESET})  📊  Statistics Dashboard")
    print(f"    {C.CYAN}5{C.RESET})  ⚙️   Configuration")
    print(f"    {C.GRAY}6{C.RESET})  🚪  Exit")
    print()

    return input_prompt("Choice:")


def screen_focus_session():
    """Start a focus session, optionally with a label."""
    config = load_config()
    clear()
    screen_header()
    print()
    print(f"  {C.BOLD}{C.RED}  🍅  New Focus Session{C.RESET}")
    print()

    label = input_prompt("What are you working on? (or press Enter to skip):")
    duration = input_prompt(f"Duration in minutes? (default {config['focus_minutes']}):")

    try:
        minutes = int(duration) if duration else config["focus_minutes"]
        if minutes <= 0:
            minutes = config["focus_minutes"]
    except ValueError:
        minutes = config["focus_minutes"]

    print()
    print(f"  {C.GRAY}  Starting {C.RED}{minutes} min{C.RESET}{C.GRAY} focus session…{C.RESET}")
    input_prompt("Press Enter to begin…")

    return run_timer("focus", minutes, label=label)


def screen_stats():
    """Full statistics dashboard."""
    sessions = load_sessions()
    stats = compute_stats(sessions)

    clear()
    screen_header()
    print()
    print(f"  {C.BOLD}{C.PURPLE}  📊  Statistics Dashboard{C.RESET}")
    print()

    if not stats:
        print(f"  {C.GRAY}  No sessions logged yet. Start a focus session to see stats!{C.RESET}")
        print()
        input_prompt("Press Enter…")
        return

    # ── Top-level KPIs ──
    hr()
    print()
    total_hrs = stats["total_focus_minutes"] / 60
    comp_hrs = stats["total_completed_minutes"] / 60

    print(f"    {C.BOLD}{C.WHITE}Total Focus Time{C.RESET}       "
          f"{C.CYAN}{total_hrs:.1f} hrs{C.RESET}  "
          f"{C.GRAY}({stats['total_focus_sessions']} sessions){C.RESET}")

    print(f"    {C.BOLD}{C.WHITE}Completed Time{C.RESET}         "
          f"{C.GREEN}{comp_hrs:.1f} hrs{C.RESET}  "
          f"{C.GRAY}({stats['completed_focus_sessions']} sessions){C.RESET}")

    print(f"    {C.BOLD}{C.WHITE}Completion Rate{C.RESET}         "
          f"{C.YELLOW}{stats['completion_rate']:.0f}%{C.RESET}")

    print(f"    {C.BOLD}{C.WHITE}Current Streak{C.RESET}          "
          f"{C.ORANGE}🔥 {stats['current_streak']} day{'s' if stats['current_streak'] != 1 else ''}{C.RESET}")

    print(f"    {C.BOLD}{C.WHITE}Best Streak{C.RESET}             "
          f"{C.ORANGE}🏆 {stats['best_streak']} day{'s' if stats['best_streak'] != 1 else ''}{C.RESET}")

    if stats.get("best_day") and stats["best_day"][0]:
        bd_date, bd_data = stats["best_day"]
        print(f"    {C.BOLD}{C.WHITE}Best Day{C.RESET}                "
              f"{C.GREEN}{bd_date}{C.RESET}  "
              f"{C.GRAY}({bd_data['minutes']:.0f} min){C.RESET}")

    print(f"    {C.BOLD}{C.WHITE}This Week{C.RESET}               "
          f"{C.BLUE}{stats['week_minutes']:.0f} min{C.RESET}  "
          f"{C.GRAY}({stats['week_sessions']} sessions){C.RESET}")

    if stats.get("first_session_date"):
        print(f"    {C.BOLD}{C.WHITE}Active Since{C.RESET}            "
              f"{C.GRAY}{stats['first_session_date']}{C.RESET}")

    print()

    # ── Heatmap ──
    print(render_weekly_heatmap(stats.get("daily", {})))
    print()

    # ── Hourly chart ──
    print(render_hourly_chart(stats.get("hourly", {})))
    print()

    # ── Recent sessions log ──
    hr()
    print()
    print(f"  {C.BOLD}{C.WHITE}Recent Sessions{C.RESET}")
    print(f"  {C.DARKGRAY}{'─' * 58}{C.RESET}")

    recent = sessions[-10:][::-1]  # last 10, newest first
    for s in recent:
        ts = s["started_at"][:16].replace("T", " ")
        stype = SESSION_TYPES.get(s["type"], s["type"])
        status = f"{C.GREEN}✓{C.RESET}" if s["completed"] else f"{C.RED}✗{C.RESET}"
        label_str = f" — {s['label']}" if s.get("label") else ""
        print(f"  {status}  {C.GRAY}{ts}{C.RESET}  {C.WHITE}{stype}{C.RESET}{C.DIM}{C.GRAY}{label_str}{C.RESET}  "
              f"{C.GRAY}{s['actual_minutes']:.1f}m / {s['planned_minutes']}m{C.RESET}")

    print()
    input_prompt("Press Enter to return…")


def screen_config():
    """Interactive configuration editor."""
    config = load_config()

    while True:
        clear()
        screen_header()
        print()
        print(f"  {C.BOLD}{C.CYAN}  ⚙️   Configuration{C.RESET}")
        print()
        hr()
        print()

        keys = [
            ("focus_minutes",                  "Focus session length (min)"),
            ("short_break_minutes",            "Short break length (min)"),
            ("long_break_minutes",             "Long break length (min)"),
            ("sessions_before_long_break",     "Sessions before long break"),
            ("daily_goal_sessions",            "Daily goal (sessions)"),
        ]

        for i, (key, desc) in enumerate(keys, 1):
            print(f"    {C.CYAN}{i}{C.RESET})  {C.WHITE}{desc:<40}{C.RESET} {C.YELLOW}{config[key]}{C.RESET}")

        quotes_on = config.get("motivational_quotes", True)
        print(f"    {C.CYAN}6{C.RESET})  {C.WHITE}{'Motivational quotes':<40}{C.RESET} {C.YELLOW}{'ON' if quotes_on else 'OFF'}{C.RESET}")
        print()
        print(f"    {C.GRAY}0{C.RESET})  ← Back to menu")
        print()

        choice = input_prompt("Edit which setting?")

        if choice == "0" or choice == "":
            break

        if choice == "6":
            config["motivational_quotes"] = not quotes_on
            save_config(config)
            continue

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(keys):
                key, desc = keys[idx]
                val = input_prompt(f"New value for {desc} (current: {config[key]}):")
                try:
                    config[key] = int(val)
                    save_config(config)
                    print(f"  {C.GREEN}  ✓ Saved.{C.RESET}")
                    time.sleep(0.6)
                except ValueError:
                    print(f"  {C.RED}  ✗ Invalid number.{C.RESET}")
                    time.sleep(0.6)
        except (ValueError, IndexError):
            pass


# ─────────────────────────────────────────────
#  POMODORO CYCLE  –  auto-advance through sessions
# ─────────────────────────────────────────────
def run_pomodoro_cycle():
    """Run the classic Pomodoro cycle: focus → break → focus → … → long break."""
    config = load_config()
    session_count = 0
    long_break_every = config["sessions_before_long_break"]

    while True:
        clear()
        screen_header()
        print()

        # Decide next session
        if session_count > 0 and session_count % long_break_every == 0:
            # Long break time
            print(f"  {C.BOLD}{C.BLUE}  🏖   Time for a long break!{C.RESET}")
            print(f"  {C.GRAY}  You completed {session_count} focus sessions. Well done!{C.RESET}")
            print()
            choice = input_prompt("Start long break? [y/n]:")
            if choice.lower() == "y":
                run_timer("long", config["long_break_minutes"])
            session_count = 0  # reset cycle
            continue

        # Focus session
        label = input_prompt("What are you working on? (Enter to skip):")
        completed = run_timer("focus", config["focus_minutes"], label=label)

        if completed:
            session_count += 1
            # Short break
            print()
            choice = input_prompt("Start a short break? [y/n]:")
            if choice.lower() == "y":
                run_timer("short", config["short_break_minutes"])
            # Continue cycle?
            print()
            choice = input_prompt("Continue with next focus session? [y/n/q]:")
            if choice.lower() in ("n", "q", ""):
                break
        else:
            # Interrupted – ask to continue cycle
            choice = input_prompt("Continue Pomodoro cycle? [y/n]:")
            if choice.lower() != "y":
                break


# ─────────────────────────────────────────────
#  CLI ARGUMENT PARSER
# ─────────────────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(
        prog="pomodoro_timer",
        description="🍅 Pomodoro Focus Timer – A terminal productivity tool with analytics.",
        epilog="Data is stored in ~/.pomodoro/"
    )
    parser.add_argument("command", nargs="?", default=None,
                        choices=["start", "stats", "config", "cycle"],
                        help="Command to run directly (start / stats / config / cycle)")
    return parser.parse_args()


# ─────────────────────────────────────────────
#  MAIN LOOP
# ─────────────────────────────────────────────
def main():
    args = parse_args()

    # Direct command shortcuts
    if args.command == "start":
        screen_focus_session()
        return
    elif args.command == "stats":
        screen_stats()
        return
    elif args.command == "config":
        screen_config()
        return
    elif args.command == "cycle":
        run_pomodoro_cycle()
        return

    # Interactive menu loop
    while True:
        choice = screen_main_menu()

        if choice == "1":
            screen_focus_session()
        elif choice == "2":
            config = load_config()
            run_timer("short", config["short_break_minutes"])
        elif choice == "3":
            config = load_config()
            run_timer("long", config["long_break_minutes"])
        elif choice == "4":
            screen_stats()
        elif choice == "5":
            screen_config()
        elif choice == "6" or choice == "":
            clear()
            print()
            print(f"  {C.BOLD}{C.GREEN}  👋  Goodbye! Keep focusing.{C.RESET}")
            print()
            break
        else:
            continue


if __name__ == "__main__":
    main()
