import os
import random
import subprocess
from datetime import datetime, timedelta

def ask_int(prompt, default):
    val = input(f"{prompt} (default {default}): ").strip()
    try:
        return int(val)
    except ValueError:
        return default

def ask_yes_no(prompt, default="n"):
    val = input(f"{prompt} (y/n, default {default}): ").strip().lower()
    return val if val in ["y", "n"] else default

def is_weekend(date):
    return date.weekday() >= 5

def random_time_on_day(day):
    return day.replace(
        hour=random.randint(9, 22),
        minute=random.randint(0, 59),
        second=random.randint(0, 59),
        microsecond=0
    )

def generate_natural_contributions(
    start_year,
    days_per_week,
    min_commits,
    max_commits,
    weekend_only=False
):
    today = datetime.now()
    start_date = datetime(start_year, 1, 1)

    commits = []
    current = start_date

    while current <= today:

        week_days = []

        for i in range(7):
            day = current + timedelta(days=i)

            if day > today:
                continue

            if weekend_only:
                if is_weekend(day):
                    week_days.append(day)
            else:
                week_days.append(day)

        if week_days:

            active_days = random.sample(
                week_days,
                min(days_per_week, len(week_days))
            )

            for day in active_days:

                daily_commits = random.randint(
                    min_commits,
                    max_commits
                )

                for _ in range(daily_commits):
                    commits.append(
                        random_time_on_day(day)
                    )

        current += timedelta(days=7)

    commits.sort()

    return commits

def generate_single_day_commits(
    start_year,
    total_commits,
    weekend_only=False
):
    today = datetime.now()
    start_date = datetime(start_year, 1, 1)

    total_days = (today - start_date).days

    while True:

        day = start_date + timedelta(
            days=random.randint(0, total_days)
        )

        if not weekend_only or is_weekend(day):
            break

    commits = []

    for _ in range(total_commits):
        commits.append(random_time_on_day(day))

    commits.sort()

    return commits

def get_git_identity(repo):
    """Return (name, email) from git config, falling back to safe defaults."""
    def _get(key, fallback):
        try:
            result = subprocess.run(
                ["git", "config", key],
                cwd=repo, capture_output=True, text=True
            )
            return result.stdout.strip() or fallback
        except Exception:
            return fallback
    name  = _get("user.name",  "GitHub User")
    email = _get("user.email", "user@example.com")
    return name, email


def make_commit(repo, filename, date, message, author_name, author_email):

    filepath = os.path.join(repo, filename)

    with open(filepath, "a", encoding="utf-8") as f:
        f.write(f"{date.isoformat()}\n")

    subprocess.run(
        ["git", "add", filename],
        cwd=repo,
        check=True
    )

    env = os.environ.copy()

    date_str = date.strftime("%Y-%m-%dT%H:%M:%S")

    env["GIT_AUTHOR_DATE"]    = date_str
    env["GIT_COMMITTER_DATE"] = date_str

    result = subprocess.run(
        [
            "git",
            "-c", f"user.name={author_name}",
            "-c", f"user.email={author_email}",
            "commit", "-m", message,
        ],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"git commit failed (exit {result.returncode}):\n"
            f"{result.stderr.strip() or result.stdout.strip()}"
        )

def validate_repo(repo):
    """Ensure the path is a git repository, raise RuntimeError otherwise."""
    result = subprocess.run(
        ["git", "rev-parse", "--git-dir"],
        cwd=repo, capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"'{repo}' is not a git repository.\n"
            "Run  git init  (and  git remote add origin <url>)  first."
        )


def main():

    print("\n🌿 GitHub Contribution Generator 🌿\n")

    repo = input(
        "Repository path (default current): "
    ).strip() or "."

    try:
        validate_repo(repo)
    except RuntimeError as e:
        print(f"\n❌ {e}")
        return

    filename = input(
        "Filename (default data.txt): "
    ).strip() or "data.txt"

    current_year = datetime.now().year

    print("\nAvailable Years:")

    for year in range(current_year, current_year - 5, -1):
        print(f"• {year}")

    start_year = ask_int(
        "\nStart from year",
        current_year - 2
    )

    weekend_only = (
        ask_yes_no(
            "Weekend-only commits?",
            "n"
        ) == "y"
    )

    print("\nCommit Modes:")
    print("1 → Natural contribution graph")
    print("2 → Many commits on one day")

    mode = input(
        "\nChoose mode (1/2): "
    ).strip()

    if mode == "2":

        total_commits = ask_int(
            "Number of commits",
            100
        )

        commit_dates = generate_single_day_commits(
            start_year,
            total_commits,
            weekend_only
        )

    else:

        days_per_week = ask_int(
            "Days per week with commits (1-7)",
            5
        )

        min_commits = ask_int(
            "Minimum commits per active day",
            1
        )

        max_commits = ask_int(
            "Maximum commits per active day",
            4
        )

        commit_dates = generate_natural_contributions(
            start_year,
            days_per_week,
            min_commits,
            max_commits,
            weekend_only
        )

    commit_message = (
        input(
            "Commit message (default update): "
        ).strip()
        or "update"
    )

    print(
        f"\n📊 Total commits to create: "
        f"{len(commit_dates)}\n"
    )

    author_name, author_email = get_git_identity(repo)
    print(f"👤 Committing as: {author_name} <{author_email}>\n")

    for i, commit_date in enumerate(commit_dates, start=1):

        print(
            f"[{i}/{len(commit_dates)}] "
            f"{commit_date}"
        )

        try:
            make_commit(
                repo,
                filename,
                commit_date,
                commit_message,
                author_name,
                author_email,
            )
        except RuntimeError as e:
            print(f"\n❌ {e}")
            return

    push_now = ask_yes_no(
        "\nPush to GitHub now?",
        "y"
    )

    if push_now == "y":

        # ── Step 1: pull remote changes via rebase ──────────────────────────
        print("\n⬇️  Pulling remote changes (rebase)…")
        pull = subprocess.run(
            ["git", "pull", "--rebase", "origin", "main"],
            cwd=repo,
            capture_output=True,
            text=True,
        )

        if pull.returncode != 0:
            print(
                f"⚠️  Rebase failed:\n{pull.stderr.strip() or pull.stdout.strip()}"
            )
            # Abort any partial rebase so the repo stays clean
            subprocess.run(
                ["git", "rebase", "--abort"],
                cwd=repo, capture_output=True
            )
            force = ask_yes_no(
                "\nForce-push instead? (overwrites remote history — use with care)",
                "n"
            )
            if force != "y":
                print(
                    "\nℹ️ Push skipped. Fix conflicts manually, then run:\n"
                    "  git push origin main"
                )
                return
            # Force push
            fp = subprocess.run(
                ["git", "push", "--force", "origin", "main"],
                cwd=repo, capture_output=True, text=True
            )
            if fp.returncode == 0:
                print("\n✅ Force-push succeeded! GitHub graph should update soon.")
            else:
                print(f"\n❌ Force-push failed:\n{fp.stderr.strip()}")
            return

        # ── Step 2: normal push after successful rebase ─────────────────────
        print("⬆️  Pushing…")
        push = subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=repo,
            capture_output=True,
            text=True,
        )

        if push.returncode == 0:
            print(
                "\n✅ Success!"
                "\nGitHub graph should update soon."
            )
        else:
            print(f"\n❌ Push failed:\n{push.stderr.strip()}")

    else:

        print(
            "\nℹ️ Commits created locally."
            "\nRun: git push origin main"
        )

if __name__ == "__main__":
    main()