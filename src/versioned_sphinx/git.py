"""Mechanisms for interacting with git to determine branches and
tags which should be used when generating the various versions
of the documentation.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal
import subprocess
from versioned_sphinx.logger import get_logger


__all__ = ["Git", "GitBranch", "GitTag"]
LOGGER = get_logger("git")


class Git:
    """Class for interacting with git repository to list branches/tags
    and change to specific branches or tags to allow generating the docs.
    """

    def __init__(self, repo_path: Path | str):
        self._repo = Path(repo_path).expanduser().resolve()
        LOGGER.debug("Looking for git repo in %s", self._repo)
        self._verify_repo()

    def checkout(self, branch_or_tag: "GitBranch | GitTag"):
        """Checkout the current repository to a specific branch or tag"""
        assert isinstance(
            branch_or_tag, (GitBranch, GitTag)
        ), "Argument must be GitBranch or GitTag"

        if isinstance(branch_or_tag, GitBranch):
            self.checkout_branch(branch_or_tag)
        else:
            self.checkout_tag(branch_or_tag)

    def checkout_branch(self, branch: "GitBranch | str"):
        """Checkout the current repository to specific branch"""
        self._verify_nothing_pending()

        name = branch.name if isinstance(branch, GitBranch) else branch
        branches = self.get_branches(location="local")
        args: list[str] = ["checkout"]

        if any(b.name == name for b in branches):
            args.append(name)
        else:
            args.extend(("-b", name))

        self._execute_git_command(args)

    def checkout_tag(self, tag: "GitTag | str"):
        """Checkout the current repository to a specific tag"""
        self._verify_nothing_pending()

        name = tag.name if isinstance(tag, GitTag) else tag
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

    def get_current_hash(self) -> str:
        """Get the hash of the most recent commit of the currently
        checked-out point of the repository.

        >>> git.get_current_hash()
        'cff3eba74bf40e62331be14a9cafe2b152cb16bb'
        """
        response = self._execute_git_command(["rev-parse", "HEAD"])
        return response.strip()

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
            args.append(pattern)

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
                    name=branch_name,
                    date=datetime.strptime(time_string, "%Y-%m-%dT%H:%M:%S%z"),
                    remote=remote,
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
            args.append(pattern)

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
                "command 'git %s' in '%s' yielded '%s'",
                " ".join(args),
                self._repo,
                stdout.replace("\n", " "),
            )
            return stdout
        except UnicodeDecodeError as e:
            LOGGER.error("git command '%s' failed with error %s", " ".join(args), e)
            raise RuntimeError("Execution of git command failed")

    def _verify_nothing_pending(self):
        """Raise an error if the repo has any uncommitted changes"""
        response = self._execute_git_command(["status"])
        assert (
            "nothing to commit, working tree clean" in response
        ), f"Repository has uncommitted changes: {response}"

    def _verify_repo(self):
        """Raise an error if the current path isn't actually a git repository"""
        response = self._execute_git_command(["status"])
        assert "not a git repository" not in response, "Folder is not a git repository"


@dataclass
class GitBranch:
    """Details about a branch in a git repository"""

    date: datetime
    """The date and time when the branch was created"""
    name: str
    """The name of the branch (including the origin)"""
    remote: bool
    """Whether the branch is remote or not"""


@dataclass
class GitTag:
    """Details about a tag in the repo"""

    date: datetime
    """The date and time when the tag was created"""
    name: str
    """The name of the tag"""
