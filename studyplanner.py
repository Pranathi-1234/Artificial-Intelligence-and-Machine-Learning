"""
Smart Study Planner — Pure Python, No APIs
==========================================
Features:
  - Add subjects with exam dates, daily hours, and topics
  - Auto-generate a day-by-day study schedule
  - AI-style smart suggestions (rule-based engine)
  - Pomodoro timer (terminal-based)
  - Progress tracking
  - Save & load plans (JSON)
  - Daily study brief
3
Requirements: Python 3.8+  (zero external libraries)

Run:
    python smart_study_planner.py
"""

import json
import os
import time
import math
from datetime import date, datetime, timedelta
from collections import defaultdict

# ── Constants ────────────────────────────────────────────────────────────────

DATA_FILE = "study_data.json"
DATE_FMT  = "%Y-%m-%d"

TIPS = [
    "Use the Pomodoro Technique: 25 min focus, 5 min break.",
    "Review notes within 24 hours to boost retention by up to 60%.",
    "Teach what you've learned to someone else — it solidifies understanding.",
    "Start with the hardest subject when your energy is highest.",
    "Break large topics into sub-topics and tackle one at a time.",
    "Use active recall instead of re-reading: close your notes and quiz yourself.",
    "Sleep is study time — your brain consolidates memory during sleep.",
    "Spaced repetition beats cramming every time.",
    "Avoid multitasking; single-task for deeper focus.",
    "Set a specific goal for each session, e.g. 'Finish Chapter 3 problems'.",
    "Hydrate! Dehydration reduces concentration and memory.",
    "Short walks between sessions refresh the brain.",
    "Use mind maps to connect ideas visually.",
    "Practice past papers under timed conditions at least once per subject.",
    "Group similar subjects on the same day to stay in the right mindset.",
]

PRIORITY_RULES = {
    0:  "🔴 CRITICAL",
    3:  "🟠 URGENT",
    7:  "🟡 HIGH",
    14: "🟢 MEDIUM",
}

# ── Utilities ────────────────────────────────────────────────────────────────

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def banner():
    print("╔══════════════════════════════════════════════════════╗")
    print("║       📚  SMART STUDY PLANNER  —  Pure Python        ║")
    print("╚══════════════════════════════════════════════════════╝\n")

def sep(char="─", width=56):
    print(char * width)

def pause():
    input("\n  Press Enter to continue...")

def today_str():
    return date.today().strftime(DATE_FMT)

def days_until(exam_date_str: str) -> int:
    try:
        exam = datetime.strptime(exam_date_str, DATE_FMT).date()
        return max((exam - date.today()).days, 0)
    except ValueError:
        return 999

def priority_label(days: int) -> str:
    for threshold in sorted(PRIORITY_RULES):
        if days <= threshold:
            return PRIORITY_RULES[threshold]
    return "🔵 LOW"

def wrap(text: str, width=54, indent="  ") -> str:
    words = text.split()
    lines, current = [], ""
    for word in words:
        if len(current) + len(word) + 1 <= width:
            current += (" " if current else "") + word
        else:
            lines.append(indent + current)
            current = word
    if current:
        lines.append(indent + current)
    return "\n".join(lines)

# ── Data Layer ───────────────────────────────────────────────────────────────

def load_data() -> dict:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"subjects": [], "progress": {}, "created": today_str()}

def save_data(data: dict):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ── AI Engine (Rule-Based) ────────────────────────────────────────────────────

def smart_priority_sort(subjects: list) -> list:
    def score(s):
        days   = days_until(s.get("exam_date", "9999-12-31"))
        hours  = float(s.get("hours_per_day", 2))
        topics = len(s.get("topics", []))
        urgency = days if days > 0 else 0.1
        return urgency / (hours * max(topics, 1))
    return sorted(subjects, key=score)

def generate_schedule(subjects: list) -> dict:
    schedule = defaultdict(list)
    today = date.today()

    for subj in subjects:
        name       = subj["name"]
        exam_date  = subj.get("exam_date", "9999-12-31")
        hours_day  = float(subj.get("hours_per_day", 2))
        topics     = subj.get("topics", ["General Study"])
        days_left  = days_until(exam_date)

        if days_left == 0:
            continue

        mins_per_day   = int(hours_day * 60)
        total_sessions = max(days_left, len(topics))
        mins_per_topic = max(mins_per_day // max(len(topics), 1), 30)

        topic_queue = []
        for i in range(total_sessions):
            topic_queue.append(topics[i % len(topics)])

        session_idx = 0
        for day_offset in range(days_left):
            if session_idx >= len(topic_queue):
                break
            current_date = today + timedelta(days=day_offset)
            date_str = current_date.strftime(DATE_FMT)

            time_left = mins_per_day
            while time_left >= 25 and session_idx < len(topic_queue):
                duration = min(mins_per_topic, time_left)
                schedule[date_str].append({
                    "subject":      name,
                    "topic":        topic_queue[session_idx],
                    "duration_min": duration,
                })
                time_left   -= duration
                session_idx += 1

    return dict(schedule)

def smart_suggestions(subjects: list, progress: dict) -> list:
    suggestions = []
    today = date.today()

    for s in subjects:
        name  = s["name"]
        days  = days_until(s.get("exam_date", "9999-12-31"))
        done  = progress.get(name, {}).get("sessions_done", 0)
        total = progress.get(name, {}).get("sessions_planned", 1)
        pct   = (done / max(total, 1)) * 100

        if days <= 3:
            suggestions.append(f"⚠️  '{name}' exam in {days} day(s)! Focus everything here today.")
        elif days <= 7 and pct < 50:
            suggestions.append(f"📌 '{name}' is only {pct:.0f}% done with {days} days left — increase daily hours.")
        elif pct >= 80:
            suggestions.append(f"✅ '{name}' is {pct:.0f}% done. Shift to revision and past papers.")
        elif done == 0 and days < 30:
            suggestions.append(f"🚀 You haven't started '{name}' yet — begin today!")

    if not suggestions:
        suggestions.append("🎯 You're on track! Keep your current pace and review notes daily.")

    tip_idx = today.toordinal() % len(TIPS)
    suggestions.append(f"💡 Tip of the day: {TIPS[tip_idx]}")

    return suggestions

def estimate_completion(subj: dict, progress: dict) -> str:
    name     = subj["name"]
    done     = progress.get(name, {}).get("sessions_done", 0)
    total    = progress.get(name, {}).get("sessions_planned", 1)
    pct      = (done / max(total, 1)) * 100
    days     = days_until(subj.get("exam_date", "9999-12-31"))
    bar_len  = 20
    filled   = int(bar_len * pct / 100)
    bar      = "█" * filled + "░" * (bar_len - filled)
    return f"[{bar}] {pct:.0f}%  ({done}/{total} sessions)  |  {days}d until exam"

# ── Menu Actions ─────────────────────────────────────────────────────────────

def add_subject(data: dict):
    sep()
    print("  ➕  ADD SUBJECT\n")
    name = input("  Subject name: ").strip()
    if not name:
        print("  ⚠️  Name cannot be empty.")
        return

    exam = ""
    while True:
        exam = input("  Exam date (YYYY-MM-DD): ").strip()
        try:
            datetime.strptime(exam, DATE_FMT)
            break
        except ValueError:
            print("  ⚠️  Invalid date format. Use YYYY-MM-DD.")

    hours = input("  Hours available per day (default 2): ").strip() or "2"
    try:
        float(hours)
    except ValueError:
        hours = "2"

    topics_raw = input("  Topics (comma-separated): ").strip()
    topics = [t.strip() for t in topics_raw.split(",") if t.strip()] or ["General Study"]

    subj = {
        "name": name,
        "exam_date": exam,
        "hours_per_day": hours,
        "topics": topics,
        "added": today_str(),
    }
    data["subjects"].append(subj)

    schedule = generate_schedule([subj])
    total_sessions = sum(len(v) for v in schedule.values())
    data["progress"].setdefault(name, {
        "sessions_done":    0,
        "sessions_planned": total_sessions,
        "last_studied":     None,
    })

    save_data(data)
    print(f"\n  ✅  '{name}' added with {len(topics)} topic(s) and {total_sessions} planned sessions.")
    pause()

def view_plan(data: dict):
    sep()
    print("  📅  STUDY PLAN\n")
    subjects = data.get("subjects", [])
    if not subjects:
        print("  No subjects yet. Add one from the main menu.")
        pause()
        return

    sorted_subjects = smart_priority_sort(subjects)
    for s in sorted_subjects:
        days  = days_until(s.get("exam_date", "9999-12-31"))
        prio  = priority_label(days)
        print(f"  {prio}  {s['name'].upper()}")
        print(f"    Exam: {s.get('exam_date','?')}  |  {days} days left  |  {s.get('hours_per_day','?')} hrs/day")
        print(f"    Topics: {', '.join(s.get('topics', []))}")
        print(f"    Progress: {estimate_completion(s, data.get('progress', {}))}")
        print()
    pause()

def view_schedule(data: dict):
    sep()
    print("  🗓️  WEEKLY SCHEDULE (next 7 days)\n")
    subjects = data.get("subjects", [])
    if not subjects:
        print("  No subjects yet.")
        pause()
        return

    schedule = generate_schedule(subjects)
    today = date.today()

    for offset in range(7):
        day     = today + timedelta(days=offset)
        day_str = day.strftime(DATE_FMT)
        label   = day.strftime("%a %d %b")
        sessions = schedule.get(day_str, [])
        if offset == 0:
            label = f"TODAY  {label}"
        print(f"  📆 {label}")
        if sessions:
            for s in sessions:
                print(f"       • {s['subject']} — {s['topic']}  ({s['duration_min']} min)")
        else:
            print("       • Rest day / Free")
        print()
    pause()

def log_progress(data: dict):
    sep()
    print("  ✅  LOG STUDY SESSION\n")
    subjects = data.get("subjects", [])
    if not subjects:
        print("  No subjects yet.")
        pause()
        return

    for i, s in enumerate(subjects, 1):
        print(f"  {i}. {s['name']}")

    try:
        choice = int(input("\n  Select subject number: ")) - 1
        subj = subjects[choice]
    except (ValueError, IndexError):
        print("  ⚠️  Invalid selection.")
        pause()
        return

    name = subj["name"]
    prog = data["progress"].setdefault(name, {"sessions_done": 0, "sessions_planned": 1, "last_studied": None})
    prog["sessions_done"]  = prog.get("sessions_done", 0) + 1
    prog["last_studied"]   = today_str()
    save_data(data)
    pct = (prog["sessions_done"] / max(prog["sessions_planned"], 1)) * 100
    print(f"\n  🎉  Session logged for '{name}'!  Progress: {pct:.0f}%")
    pause()

def smart_advice(data: dict):
    sep()
    print("  🤖  SMART SUGGESTIONS\n")
    subjects    = data.get("subjects", [])
    progress    = data.get("progress", {})
    suggestions = smart_suggestions(subjects, progress)

    for s in suggestions:
        print(wrap(s))
        print()
    pause()

def daily_brief(data: dict):
    sep()
    today_label = datetime.today().strftime("%A, %B %d %Y")
    print(f"  🌅  DAILY BRIEF — {today_label}\n")

    subjects = data.get("subjects", [])
    if not subjects:
        print("  No subjects added yet. Start by adding your first subject!\n")
        tip_idx = date.today().toordinal() % len(TIPS)
        print(wrap(f"💡 {TIPS[tip_idx]}"))
        pause()
        return

    schedule = generate_schedule(subjects)
    today_sessions = schedule.get(today_str(), [])

    if today_sessions:
        total_min = sum(s["duration_min"] for s in today_sessions)
        print(f"  You have {len(today_sessions)} session(s) totalling {total_min} minutes today:\n")
        for i, s in enumerate(today_sessions, 1):
            print(f"  {i}. {s['subject']}  →  {s['topic']}  ({s['duration_min']} min)")
    else:
        print("  No sessions scheduled for today. Great day to review or rest!")

    print()
    sorted_s = smart_priority_sort(subjects)
    if sorted_s:
        most_urgent = sorted_s[0]
        days = days_until(most_urgent.get("exam_date", "9999-12-31"))
        print(wrap(f"🎯 Most urgent: '{most_urgent['name']}' — {days} day(s) until exam."))
        print()

    tip_idx = date.today().toordinal() % len(TIPS)
    print(wrap(f"💡 {TIPS[tip_idx]}"))
    pause()

def pomodoro_timer():
    sep()
    print("  ⏱️  POMODORO TIMER\n")
    try:
        work_min  = int(input("  Work duration in minutes (default 25): ").strip() or "25")
        break_min = int(input("  Break duration in minutes (default 5): ").strip() or "5")
        rounds    = int(input("  Number of rounds (default 4): ").strip() or "4")
    except ValueError:
        work_min, break_min, rounds = 25, 5, 4

    for r in range(1, rounds + 1):
        print(f"\n  🟢  Round {r}/{rounds} — FOCUS ({work_min} min)  Starting...")
        _countdown(work_min * 60)
        print("  ✅  Work session done!")
        if r < rounds:
            print(f"  ☕  Break time ({break_min} min)...")
            _countdown(break_min * 60)
            print("  🔔  Break over! Get ready for the next round.")

    print("\n  🏆  All rounds complete! Great work.\n")
    pause()

def _countdown(seconds: int):
    start = time.time()
    try:
        while True:
            elapsed   = time.time() - start
            remaining = max(0, seconds - int(elapsed))
            mins, secs = divmod(remaining, 60)
            print(f"\r      ⏳  {mins:02d}:{secs:02d} remaining ", end="", flush=True)
            if remaining == 0:
                break
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n  ⚠️  Timer interrupted.")
    print()

def remove_subject(data: dict):
    sep()
    print("  🗑️  REMOVE SUBJECT\n")
    subjects = data.get("subjects", [])
    if not subjects:
        print("  No subjects to remove.")
        pause()
        return

    for i, s in enumerate(subjects, 1):
        print(f"  {i}. {s['name']}  (exam: {s.get('exam_date','?')})")

    try:
        choice = int(input("\n  Subject number to remove (0 to cancel): "))
        if choice == 0:
            return
        subj = subjects[choice - 1]
    except (ValueError, IndexError):
        print("  ⚠️  Invalid selection.")
        pause()
        return

    confirm = input(f"  Remove '{subj['name']}'? (y/n): ").strip().lower()
    if confirm == "y":
        data["subjects"].pop(choice - 1)
        data["progress"].pop(subj["name"], None)
        save_data(data)
        print(f"  ✅  '{subj['name']}' removed.")
    pause()

# ── Main Loop ────────────────────────────────────────────────────────────────

def main():
    data = load_data()

    while True:
        clear()
        banner()

        subjects = data.get("subjects", [])
        print(f"  Subjects loaded: {len(subjects)}    |    Today: {datetime.today().strftime('%a %d %b %Y')}\n")

        print("  1.  Add Subject")
        print("  2.  View Study Plan")
        print("  3.  View Weekly Schedule")
        print("  4.  Log Study Session")
        print("  5.  Smart Suggestions")
        print("  6.  Daily Brief")
        print("  7.  Pomodoro Timer")
        print("  8.  Remove Subject")
        print("  9.  Exit")
        sep()

        choice = input("  Choose (1-9): ").strip()

        if   choice == "1": add_subject(data)
        elif choice == "2": view_plan(data)
        elif choice == "3": view_schedule(data)
        elif choice == "4": log_progress(data)
        elif choice == "5": smart_advice(data)
        elif choice == "6": daily_brief(data)
        elif choice == "7": pomodoro_timer()
        elif choice == "8": remove_subject(data)
        elif choice == "9":
            print("\n  👋  Good luck with your studies! Bye.\n")
            break
        else:
            print("  ⚠️  Invalid choice.")
            time.sleep(1)

if __name__ == "__main__":
    main()
