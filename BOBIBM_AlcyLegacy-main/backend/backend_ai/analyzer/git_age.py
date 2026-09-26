"""Git age and stagnation inspector for BOB Backend.

Inspects git commit history via `git log -1 --format=%ct -- <file>` using subprocess.run.
Calculates elapsed time since last commit, falling back to os.path.getmtime for untracked/new files.
Returns humanized string in Spanish (e.g., "4.2 años", "6 meses", "15 días") and age_in_years.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
import time
from typing import Dict, Optional, Union


@dataclass
class GitAgeResult:
    """Result of Git commit age inspection."""

    file_path: str
    last_commit_date: Optional[str] = None
    age_in_years: float = 0.0
    age_display: str = "0 días"
    commit_count: int = 0
    is_git_tracked: bool = True

    def to_dict(self) -> Dict[str, Union[str, float, int, bool, Optional[str]]]:
        """Convert result to dictionary representation."""
        return {
            "file_path": self.file_path,
            "last_commit_date": self.last_commit_date,
            "age_in_years": self.age_in_years,
            "age_display": self.age_display,
            "commit_count": self.commit_count,
            "is_git_tracked": self.is_git_tracked,
        }


def format_age_in_spanish(age_in_years: float) -> str:
    """Formats an age in years into a human-readable Spanish string."""
    if age_in_years >= 1.0:
        rounded_years = round(age_in_years, 1)
        if rounded_years == 1.0:
            return "1.0 años"
        return f"{rounded_years} años"

    # Between 1 month and 1 year
    months = int(round(age_in_years * 12.0))
    if months >= 1:
        if months == 1:
            return "1 mes"
        return f"{months} meses"

    # Under 1 month (in days)
    days = int(round(age_in_years * 365.25))
    if days <= 1:
        return "1 día"
    return f"{days} días"


def get_file_age(
    file_path: Union[str, Path],
    repo_path: Optional[Union[str, Path]] = None,
) -> GitAgeResult:
    """Calculates elapsed time since last commit or modification.

    Args:
        file_path: Path or relative path to the file.
        repo_path: Optional root directory of the repository.

    Returns:
        GitAgeResult with age_in_years, age_display in Spanish, and tracking status.
    """
    file_path_str = str(file_path).replace("\\", "/")
    target_path = Path(file_path)

    # Determine full path and working directory for git command
    if repo_path:
        cwd_dir = Path(repo_path)
        if not target_path.is_absolute():
            full_path = cwd_dir / target_path
            rel_git_path = str(target_path).replace("\\", "/")
        else:
            full_path = target_path
            try:
                rel_git_path = str(target_path.relative_to(cwd_dir)).replace("\\", "/")
            except ValueError:
                rel_git_path = str(target_path).replace("\\", "/")
    else:
        full_path = target_path.resolve() if target_path.exists() else target_path
        cwd_dir = full_path.parent if full_path.exists() else Path.cwd()
        rel_git_path = full_path.name

    commit_epoch: Optional[int] = None
    commit_count = 0
    is_git_tracked = False
    last_commit_date_str: Optional[str] = None

    # Attempt to query git log
    try:
        cmd = ["git", "log", "-1", "--format=%ct", "--", rel_git_path]
        proc = subprocess.run(
            cmd,
            cwd=str(cwd_dir),
            capture_output=True,
            text=True,
            timeout=5.0,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            raw_epoch = proc.stdout.strip()
            if raw_epoch.isdigit():
                commit_epoch = int(raw_epoch)
                is_git_tracked = True
                last_commit_date_str = time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ", time.gmtime(commit_epoch)
                )

        if is_git_tracked:
            # Query commit count
            cnt_cmd = ["git", "rev-list", "--count", "HEAD", "--", rel_git_path]
            cnt_proc = subprocess.run(
                cnt_cmd,
                cwd=str(cwd_dir),
                capture_output=True,
                text=True,
                timeout=5.0,
                check=False,
            )
            if cnt_proc.returncode == 0 and cnt_proc.stdout.strip().isdigit():
                commit_count = int(cnt_proc.stdout.strip())
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        is_git_tracked = False

    # Fallback to filesystem mtime if git is untracked or unavailable
    if commit_epoch is None:
        if full_path.exists() and full_path.is_file():
            try:
                mtime = os.path.getmtime(full_path)
                commit_epoch = int(mtime)
                last_commit_date_str = time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ", time.gmtime(commit_epoch)
                )
            except OSError:
                commit_epoch = int(time.time())
        else:
            return GitAgeResult(
                file_path=file_path_str,
                last_commit_date=None,
                age_in_years=0.0,
                age_display="0 días",
                commit_count=0,
                is_git_tracked=False,
            )

    now = time.time()
    delta_seconds = max(0.0, now - float(commit_epoch))
    age_in_years = delta_seconds / (365.25 * 86400.0)
    age_display = format_age_in_spanish(age_in_years)

    return GitAgeResult(
        file_path=file_path_str,
        last_commit_date=last_commit_date_str,
        age_in_years=round(age_in_years, 3),
        age_display=age_display,
        commit_count=commit_count,
        is_git_tracked=is_git_tracked,
    )
