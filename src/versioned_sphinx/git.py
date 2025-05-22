"""Mechanisms for interacting with git to determine branches and
tags which should be used when generating the various versions
of the documentation.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal
import subprocess
from .logger import get_logger


LOGGER = get_logger("git")


class Git:
    """Class for interacting with git repository to list branches/tags
    and change to specific branches or tags to allow generating the docs.
    """

    def __init__(self, repo_path: Path | str):
        self._repo = Path(repo_path).expanduser().resolve()
        LOGGER.debug("Looking for git repo in %s", self._repo)
        self._verify_repo()

    def checkout_branch(self, branch: "GitBranch | str"):
        """Checkout the current repository to specific branch"""
        self._verify_nothing_pending()

        name = branch.branch if isinstance(branch, GitBranch) else branch
        branches = self.get_branches(location="local")
        args: list[str] = ["checkout"]

        if any(b.branch == name for b in branches):
            args.append(name)
        else:
            args.extend(("-b", name))

        self._execute_git_command(args)

    def checkout_tag(self, tag: "GitTag | str"):
        """Checkout the current repository to a specific tag"""
        self._verify_nothing_pending()

        name = tag.tag if isinstance(tag, GitTag) else tag
        self._execute_git_command(["checkout", name])

    def get_current_branch(self) -> str:
        """Get the name of the current branch in the repo"""
        response = self._execute_git_command(["status"]).strip()
        first_line = response.splitlines()[0]
        if first_line.startswith("On branch "):
            return first_line.split("On branch ")[-1].strip()
        elif first_line.startswith("HEAD detached at "):
            return first_line.split("HEAD detached at ")[-1].strip()
        else:
            LOGGER.error("Unknown checkout: '%s'", first_line)
            raise ValueError("Unknown checkout point")

    def get_branches(
        self,
        pattern: str | None = None,
        location: Literal["all", "local", "remote"] = "remote",
    ) -> list["GitBranch"]:
        """Get all of the branches in the current repo (or just those
        which match ``pattern``).
        """
        spaces = 5
        args = [
            "branch",
            f"--format='%(creatordate:iso-strict){' ' * spaces}%(refname:strip=2){' ' * spaces}%(upstream:strip=2)'",
        ]
        if location == "all":
            args.append("-a")
        elif location == "remote":
            args.append("-r")

        if pattern:
            args.append("-l")
            args.append(f"'{pattern}'")

        response = self._execute_git_command(args)
        branches: list[GitBranch] = []
        for line in response.splitlines():
            if line[0] == "'":
                line = line[1:]
            if line[-1] == "'":
                line = line[:-1]

            parts = line.strip().split(" " * spaces)
            time_string, branch_name = parts[:2]
            remote = len(parts) == 2

            branches.append(
                GitBranch(
                    branch_name,
                    datetime.strptime(time_string, "%Y-%m-%dT%H:%M:%S%z"),
                    remote,
                )
            )

        return branches

    def get_tags(self, pattern: str | None = None) -> list["GitTag"]:
        """Get all of the tags in the current repo (or just those which
        match ``pattern``).
        """
        spaces = 5
        args = [
            "tag",
            f"--format='%(creatordate:iso-strict){' ' * spaces}%(refname:strip=2)'",
        ]
        if pattern:
            args.append("-l")
            args.append(f"'{pattern}")

        response = self._execute_git_command(args)
        tags: list[GitTag] = []
        for line in response.splitlines():
            if line[0] == "'":
                line = line[1:]
            if line[-1] == "'":
                line = line[:-1]

            time_string, tag_name = line.strip().split(" " * spaces)
            tags.append(
                GitTag(datetime.strptime(time_string, "%Y-%m-%dT%H:%M:%S%z"), tag_name)
            )

        return tags

    def _execute_git_command(self, args: list[str]) -> str:
        """Execute a git command in the current repo, returning stdout."""
        response = subprocess.run(
            ["git", *args], capture_output=True, check=True, cwd=self._repo
        )

        try:
            stdout = response.stdout.decode().strip()
            LOGGER.debug(
                "command 'git %s' yielded '%s'",
                " ".join(args),
                stdout.replace("\n", " "),
            )
            return stdout
        except UnicodeDecodeError as e:
            LOGGER.error("git command '%s' failed with error %s", " ".join(args), e)
            raise RuntimeError("Execution of git command failed")

    def _verify_nothing_pending(self):
        """Raise an error if the repo has any uncomitted changes"""
        response = self._execute_git_command(["status"])
        assert (
            "nothing to commit, working tree clean" in response
        ), "Repository has uncommitted changes"

    def _verify_repo(self):
        """Raise an error if the current path isn't actually a git repository"""
        response = self._execute_git_command(["status"])
        assert "not a git repository" not in response, "Folder is not a git repository"


@dataclass
class GitBranch:
    """Details about a branch in a git repository"""

    branch: str
    """The name of the branch (including the origin)"""
    date: datetime
    """The date and time when the branch was created"""
    remote: bool
    """Whether the branch is remote or not"""


@dataclass
class GitTag:
    """Details about a tag in the repo"""

    date: datetime
    """The date and time when the tag was created"""
    tag: str
    """The name of the tag"""
