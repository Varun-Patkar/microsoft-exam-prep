"""
Quiz Runner CLI — Interactive practice question drill for Microsoft certification prep.

Usage:
    python quiz_runner.py questions.json --domain 1         # All questions from domain 1
    python quiz_runner.py questions.json --topic "1.1"      # Questions matching topic prefix "1.1"
    python quiz_runner.py questions.json --ids q001,q005    # Specific question IDs
    python quiz_runner.py questions.json --cross 1,2        # Cross-topic: mix domains 1 and 2
    python quiz_runner.py questions.json --all              # All questions (mock exam mode)

Results saved to session-results.json after completion.
"""

import json
import sys
import os
import argparse
import random
import time
from datetime import datetime

# ── ANSI color helpers (works on Windows 10+ and all Unix terminals) ──

def _enable_ansi_windows():
    """Enable ANSI escape sequences on Windows terminal."""
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        # STD_OUTPUT_HANDLE = -11, ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_ulong()
        kernel32.GetConsoleMode(handle, ctypes.byref(mode))
        kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        pass

if os.name == "nt":
    _enable_ansi_windows()

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
UNDERLINE = "\033[4m"


def load_questions(filepath):
    """Load questions.json and return the parsed dict."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def filter_questions(data, domain_id=None, topic_prefix=None, question_ids=None, cross_domains=None, all_mode=False):
    """
    Filter questions from the dataset based on criteria.

    Args:
        data: Parsed questions.json dict
        domain_id: Single domain ID string (e.g., "1")
        topic_prefix: Topic prefix to match (e.g., "1.1")
        question_ids: List of specific question IDs
        cross_domains: List of domain IDs to mix together
        all_mode: If True, return all questions

    Returns:
        List of question dicts with domainName injected
    """
    selected = []

    for domain in data.get("domains", []):
        d_id = str(domain["domainId"])
        d_name = domain["domainName"]

        for q in domain["questions"]:
            q_copy = dict(q)
            q_copy["domainName"] = d_name
            q_copy["domainId"] = d_id

            if all_mode:
                selected.append(q_copy)
            elif question_ids and q["id"] in question_ids:
                selected.append(q_copy)
            elif domain_id and d_id == str(domain_id):
                if topic_prefix:
                    if q.get("topic", "").startswith(topic_prefix):
                        selected.append(q_copy)
                else:
                    selected.append(q_copy)
            elif cross_domains and d_id in [str(x) for x in cross_domains]:
                selected.append(q_copy)
            elif topic_prefix and not domain_id:
                if q.get("topic", "").startswith(topic_prefix):
                    selected.append(q_copy)

    return selected


def display_question(q, index, total):
    """Display a single question with formatted options. Handles mc, dropdown, yesno, multi types."""
    qtype = q.get("type", "mc")
    print(f"\n{'─' * 60}")
    print(f"{CYAN}{BOLD}Question {index}/{total}{RESET}  {DIM}[{q['domainName']}]{RESET}")
    print(f"{DIM}Topic: {q.get('topic', 'N/A')} | Difficulty: {q.get('difficulty', 'N/A')} | ID: {q['id']}{RESET}")
    print(f"{'─' * 60}")
    print(f"\n{q['question']}\n")

    if qtype == "mc":
        for opt in q["options"]:
            print(f"  {opt}")
        print()
    elif qtype == "multi":
        # Multi-select: show options, indicate how many to pick
        num_correct = len(q.get("correctAnswers", []))
        print(f"  {YELLOW}(Select {num_correct} answers){RESET}\n")
        for opt in q["options"]:
            print(f"  {opt}")
        print()
    elif qtype == "dropdown":
        # Show each dropdown slot with numbered options
        for di, dd in enumerate(q.get("dropdowns", []), 1):
            print(f"  {BOLD}[Slot {di}] {dd['label']}{RESET}")
            for oi, opt in enumerate(dd["options"], 1):
                print(f"    {oi}. {opt}")
        print()
    elif qtype == "yesno":
        # Show numbered statements
        for si, stmt in enumerate(q.get("statements", []), 1):
            print(f"  {BOLD}Statement {si}:{RESET} {stmt}")
        print()


def _get_mc_answer(valid_options):
    """Get single-choice answer (mc type). Returns (answer, skipped, quit)."""
    while True:
        try:
            raw = input(f"{YELLOW}Your answer ({'/'.join(valid_options)}) [s=skip, q=quit]: {RESET}").strip().upper()
        except (EOFError, KeyboardInterrupt):
            return None, False, True
        if raw == "Q":
            return None, False, True
        if raw == "S":
            return None, True, False
        if raw in valid_options:
            return raw, False, False
        print(f"{RED}  Invalid. Enter one of: {', '.join(valid_options)}, s, or q{RESET}")


def _get_multi_answer(valid_options, num_required):
    """Get multi-select answer. Returns (sorted list of letters, skipped, quit)."""
    while True:
        try:
            raw = input(f"{YELLOW}Your answers (comma-separated, e.g. A,C) [s=skip, q=quit]: {RESET}").strip().upper()
        except (EOFError, KeyboardInterrupt):
            return None, False, True
        if raw == "Q":
            return None, False, True
        if raw == "S":
            return None, True, False
        parts = sorted(set(p.strip() for p in raw.split(",")))
        if all(p in valid_options for p in parts) and len(parts) == num_required:
            return parts, False, False
        print(f"{RED}  Enter exactly {num_required} valid options from {', '.join(valid_options)}, comma-separated.{RESET}")


def _get_dropdown_answers(dropdowns):
    """Get answers for each dropdown slot. Returns (list of chosen indices, skipped, quit)."""
    answers = []
    for di, dd in enumerate(dropdowns, 1):
        num_opts = len(dd["options"])
        while True:
            try:
                raw = input(f"{YELLOW}  Slot {di} — {dd['label']} (1-{num_opts}) [s=skip, q=quit]: {RESET}").strip().upper()
            except (EOFError, KeyboardInterrupt):
                return None, False, True
            if raw == "Q":
                return None, False, True
            if raw == "S":
                return None, True, False
            if raw.isdigit() and 1 <= int(raw) <= num_opts:
                answers.append(int(raw) - 1)  # zero-based index
                break
            print(f"{RED}    Enter a number between 1 and {num_opts}.{RESET}")
    return answers, False, False


def _get_yesno_answers(statements):
    """Get Yes/No answer per statement. Returns (list of 'Yes'/'No', skipped, quit)."""
    answers = []
    for si, stmt in enumerate(statements, 1):
        while True:
            try:
                raw = input(f"{YELLOW}  Statement {si} — Yes or No? [s=skip, q=quit]: {RESET}").strip().upper()
            except (EOFError, KeyboardInterrupt):
                return None, False, True
            if raw == "Q":
                return None, False, True
            if raw == "S":
                return None, True, False
            if raw in ("YES", "Y"):
                answers.append("Yes")
                break
            elif raw in ("NO", "N"):
                answers.append("No")
                break
            print(f"{RED}    Enter Yes/Y or No/N.{RESET}")
    return answers, False, False


def get_answer_for_question(q):
    """
    Route to the correct input handler based on question type.

    Returns:
        Tuple of (user_answer, skipped, quit_early)
        user_answer type varies by question type:
          mc: str (letter)
          multi: list of str (letters)
          dropdown: list of int (zero-based indices)
          yesno: list of str ('Yes'/'No')
    """
    qtype = q.get("type", "mc")

    if qtype == "mc":
        valid = []
        for opt in q.get("options", []):
            letter = opt.strip()[0].upper()
            if letter.isalpha():
                valid.append(letter)
        if not valid:
            valid = ["A", "B", "C", "D"]
        return _get_mc_answer(valid)

    elif qtype == "multi":
        valid = []
        for opt in q.get("options", []):
            letter = opt.strip()[0].upper()
            if letter.isalpha():
                valid.append(letter)
        if not valid:
            valid = ["A", "B", "C", "D", "E"]
        num_required = len(q.get("correctAnswers", []))
        return _get_multi_answer(valid, num_required)

    elif qtype == "dropdown":
        return _get_dropdown_answers(q.get("dropdowns", []))

    elif qtype == "yesno":
        return _get_yesno_answers(q.get("statements", []))

    else:
        # Fallback: treat as mc
        return _get_mc_answer(["A", "B", "C", "D"])


def check_correct(q, user_answer):
    """
    Check if user_answer is correct for the given question type.
    Returns True/False.
    """
    qtype = q.get("type", "mc")

    if qtype == "mc":
        return user_answer == q["correctAnswer"].strip().upper()

    elif qtype == "multi":
        correct_set = sorted(a.strip().upper() for a in q.get("correctAnswers", []))
        return user_answer == correct_set

    elif qtype == "dropdown":
        dropdowns = q.get("dropdowns", [])
        for i, dd in enumerate(dropdowns):
            if user_answer[i] != dd["correctIndex"]:
                return False
        return True

    elif qtype == "yesno":
        expected = q.get("statementAnswers", [])
        return user_answer == expected

    return False


def get_correct_display(q):
    """Return a human-readable string of the correct answer for any question type."""
    qtype = q.get("type", "mc")

    if qtype == "mc":
        return q["correctAnswer"].strip().upper()

    elif qtype == "multi":
        return ", ".join(sorted(a.strip().upper() for a in q.get("correctAnswers", [])))

    elif qtype == "dropdown":
        parts = []
        for dd in q.get("dropdowns", []):
            parts.append(f"{dd['label']} {dd['correctAnswer']}")
        return " | ".join(parts)

    elif qtype == "yesno":
        expected = q.get("statementAnswers", [])
        return ", ".join(f"S{i+1}={a}" for i, a in enumerate(expected))

    return "?"


def get_user_display(q, user_answer):
    """Return a human-readable string of the user's answer for any question type."""
    qtype = q.get("type", "mc")

    if user_answer is None:
        return "—"

    if qtype == "mc":
        return str(user_answer)

    elif qtype == "multi":
        return ", ".join(user_answer)

    elif qtype == "dropdown":
        dropdowns = q.get("dropdowns", [])
        parts = []
        for i, dd in enumerate(dropdowns):
            chosen = dd["options"][user_answer[i]] if i < len(user_answer) else "?"
            parts.append(f"{dd['label']} {chosen}")
        return " | ".join(parts)

    elif qtype == "yesno":
        return ", ".join(f"S{i+1}={a}" for i, a in enumerate(user_answer))

    return str(user_answer)


def show_result(q, user_answer, skipped):
    """Show whether user was correct, with explanation. Handles all question types."""
    correct_display = get_correct_display(q)

    if skipped:
        print(f"{YELLOW}  ⏭  SKIPPED{RESET} — Correct answer: {GREEN}{correct_display}{RESET}")
    elif check_correct(q, user_answer):
        print(f"{GREEN}{BOLD}  ✓  CORRECT!  Nice one!{RESET}")
    else:
        user_display = get_user_display(q, user_answer)
        print(f"{RED}{BOLD}  ✗  WRONG.{RESET}  You chose {RED}{user_display}{RESET}")
        print(f"  Correct: {GREEN}{correct_display}{RESET}")
        print(f"{YELLOW}  📝  Note this one down — review it later!{RESET}")

    # Show explanation
    explanation = q.get("explanation", "")
    if explanation:
        print(f"\n{DIM}  Explanation: {explanation}{RESET}")


def show_summary(results, total_time_sec):
    """Print final score summary."""
    total = len(results)
    correct = sum(1 for r in results if r["correct"])
    wrong = sum(1 for r in results if not r["correct"] and not r["skipped"])
    skipped = sum(1 for r in results if r["skipped"])
    pct = (correct / total * 100) if total > 0 else 0
    minutes = int(total_time_sec // 60)
    seconds = int(total_time_sec % 60)

    print(f"\n{'═' * 60}")
    print(f"{BOLD}{CYAN}  QUIZ COMPLETE — RESULTS{RESET}")
    print(f"{'═' * 60}\n")

    # Score bar
    bar_len = 30
    filled = int(bar_len * pct / 100)
    bar = "█" * filled + "░" * (bar_len - filled)
    color = GREEN if pct >= 70 else YELLOW if pct >= 50 else RED
    print(f"  Score: {color}{BOLD}{correct}/{total} ({pct:.0f}%){RESET}  [{color}{bar}{RESET}]")
    print(f"  Time:  {minutes}m {seconds}s")
    print(f"  {GREEN}✓ Correct: {correct}{RESET}  |  {RED}✗ Wrong: {wrong}{RESET}  |  {YELLOW}⏭ Skipped: {skipped}{RESET}")

    # Encouragement based on score
    print()
    if pct >= 90:
        print(f"  {GREEN}{BOLD}🏆  Outstanding! You're exam-ready on these topics!{RESET}")
    elif pct >= 70:
        print(f"  {GREEN}👍  Solid performance! Review the ones you missed and you'll nail it.{RESET}")
    elif pct >= 50:
        print(f"  {YELLOW}💪  Getting there! Focus on the wrong answers — understanding WHY helps most.{RESET}")
    else:
        print(f"  {RED}📚  Needs more study. Re-read the topic explanations and try again tomorrow.{RESET}")

    # Show wrong/skipped questions for review
    missed = [r for r in results if not r["correct"] or r["skipped"]]
    if missed:
        print(f"\n{'─' * 60}")
        print(f"{BOLD}  Questions to review:{RESET}\n")
        for r in missed:
            status = f"{YELLOW}SKIPPED{RESET}" if r["skipped"] else f"{RED}WRONG (you: {r['userAnswer']}, correct: {r['correctAnswer']}){RESET}"
            print(f"  • {r['questionId']}: {status}")
            print(f"    {DIM}{r['question'][:80]}...{RESET}" if len(r["question"]) > 80 else f"    {DIM}{r['question']}{RESET}")

    print(f"\n{'═' * 60}\n")


def save_results(results, data, total_time_sec, output_path="session-results.json"):
    """
    Save session results to JSON for agent to read back.

    Args:
        results: List of per-question result dicts
        data: Original questions.json data
        total_time_sec: Total quiz duration in seconds
        output_path: Where to save results
    """
    total = len(results)
    correct = sum(1 for r in results if r["correct"])
    skipped = sum(1 for r in results if r["skipped"])

    # Per-topic breakdown
    topic_stats = {}
    for r in results:
        topic = r.get("topic", "Unknown")
        if topic not in topic_stats:
            topic_stats[topic] = {"total": 0, "correct": 0, "wrong": 0, "skipped": 0}
        topic_stats[topic]["total"] += 1
        if r["skipped"]:
            topic_stats[topic]["skipped"] += 1
        elif r["correct"]:
            topic_stats[topic]["correct"] += 1
        else:
            topic_stats[topic]["wrong"] += 1

    # Per-domain breakdown
    domain_stats = {}
    for r in results:
        d_name = r.get("domainName", "Unknown")
        if d_name not in domain_stats:
            domain_stats[d_name] = {"total": 0, "correct": 0, "wrong": 0, "skipped": 0}
        domain_stats[d_name]["total"] += 1
        if r["skipped"]:
            domain_stats[d_name]["skipped"] += 1
        elif r["correct"]:
            domain_stats[d_name]["correct"] += 1
        else:
            domain_stats[d_name]["wrong"] += 1

    output = {
        "timestamp": datetime.now().isoformat(),
        "examCode": data.get("examCode", ""),
        "examName": data.get("examName", ""),
        "summary": {
            "totalQuestions": total,
            "correct": correct,
            "wrong": total - correct - skipped,
            "skipped": skipped,
            "accuracy": round(correct / total * 100, 1) if total > 0 else 0,
            "timeSeconds": round(total_time_sec, 1)
        },
        "domainBreakdown": domain_stats,
        "topicBreakdown": topic_stats,
        "wrongQuestions": [
            {
                "questionId": r["questionId"],
                "question": r["question"],
                "userAnswer": r["userAnswer"],
                "correctAnswer": r["correctAnswer"],
                "explanation": r.get("explanation", ""),
                "topic": r.get("topic", ""),
                "domainName": r.get("domainName", "")
            }
            for r in results if not r["correct"] and not r["skipped"]
        ],
        "skippedQuestions": [r["questionId"] for r in results if r["skipped"]],
        "allResults": results
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"{DIM}Results saved to: {output_path}{RESET}")
    return output_path


def run_quiz(questions, data):
    """
    Main quiz loop — present questions one-by-one, collect answers, show results.

    Args:
        questions: List of question dicts to ask
        data: Original questions.json data (for metadata in results)

    Returns:
        Path to saved results file
    """
    total = len(questions)
    if total == 0:
        print(f"{RED}No questions matched your filter criteria.{RESET}")
        sys.exit(1)

    print(f"\n{BOLD}{CYAN}{'═' * 60}{RESET}")
    print(f"{BOLD}{CYAN}  QUIZ SESSION — {data.get('examName', 'Certification Prep')}{RESET}")
    print(f"{BOLD}{CYAN}  {total} questions | Type answer letter | 's' to skip | 'q' to quit{RESET}")
    print(f"{BOLD}{CYAN}{'═' * 60}{RESET}")

    results = []
    start_time = time.time()

    for i, q in enumerate(questions, 1):
        display_question(q, i, total)

        user_answer, skipped, quit_early = get_answer_for_question(q)

        if quit_early:
            print(f"\n{YELLOW}Quitting early after {i - 1} questions.{RESET}")
            break

        is_correct = check_correct(q, user_answer) if not skipped else False

        show_result(q, user_answer, skipped)

        results.append({
            "questionId": q["id"],
            "question": q["question"],
            "userAnswer": get_user_display(q, user_answer) if not skipped else None,
            "correctAnswer": get_correct_display(q),
            "correct": is_correct,
            "skipped": skipped,
            "topic": q.get("topic", ""),
            "domainName": q.get("domainName", ""),
            "domainId": q.get("domainId", ""),
            "difficulty": q.get("difficulty", ""),
            "explanation": q.get("explanation", "")
        })

    elapsed = time.time() - start_time

    if results:
        show_summary(results, elapsed)
        return save_results(results, data, elapsed)
    else:
        print(f"{YELLOW}No questions answered.{RESET}")
        return None


def main():
    """Entry point — parse args, filter questions, run quiz."""
    parser = argparse.ArgumentParser(
        description="Interactive quiz runner for Microsoft certification exam prep"
    )
    parser.add_argument("questions_file", help="Path to questions.json")
    parser.add_argument("--domain", type=str, help="Filter by domain ID (e.g., 1, 2, 3)")
    parser.add_argument("--topic", type=str, help="Filter by topic prefix (e.g., '1.1', '2.3')")
    parser.add_argument("--ids", type=str, help="Comma-separated question IDs (e.g., q001,q005,q010)")
    parser.add_argument("--cross", type=str, help="Cross-topic: comma-separated domain IDs to mix (e.g., 1,2)")
    parser.add_argument("--all", action="store_true", help="All questions (mock exam mode)")
    parser.add_argument("--shuffle", action="store_true", help="Randomize question order")
    parser.add_argument("--limit", type=int, help="Limit number of questions")
    parser.add_argument("--output", type=str, default="session-results.json", help="Output results file path")

    args = parser.parse_args()

    # Load questions
    data = load_questions(args.questions_file)

    # Parse filter criteria
    q_ids = args.ids.split(",") if args.ids else None
    cross = args.cross.split(",") if args.cross else None

    questions = filter_questions(
        data,
        domain_id=args.domain,
        topic_prefix=args.topic,
        question_ids=q_ids,
        cross_domains=cross,
        all_mode=args.all
    )

    if args.shuffle:
        random.shuffle(questions)

    if args.limit and args.limit < len(questions):
        questions = questions[:args.limit]

    # Run the quiz
    result_path = run_quiz(questions, data)

    if result_path:
        # Print path for agent to pick up
        print(f"\n{DIM}[AGENT_RESULT_PATH:{result_path}]{RESET}")


if __name__ == "__main__":
    main()
