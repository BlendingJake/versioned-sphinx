from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from types import ModuleType
from typing import Callable
from .git import GitBranch, GitTag


@dataclass
class Config:
    """Configuration parameters that can be specified in conf.py
    to modify how :mod:`versioned_sphinx` behaves.
    """

    vs_build_path: Path | str | None = None
    """The location of the build folder, as a path relative to the root
    of the repository. By default, this will be ``root / 'docs' / 'build'``.
    """

    vs_current_version: str | None = None
    """The branch or tag name of the current version. Aka, the one
    which should be displayed by default.
    """

    vs_display_name: Callable[[GitBranch | GitTag], str] | None = None
    """A function which takes a branch or tag and returns a name
    which will be used in the final documentation and for sorting, unless
    :attr:`vs_sort` is otherwise supplied.
    
    .. code-block:: python
    
        def vs_display_name(branch_or_tag):
            if isinstance(branch_or_tag, GitBranch):
                # remove 'release/' and 'rc/'
                return branch_or_tag.branch.split('/')[-1]
            else:
                # remove 'v'
                return branch_or_tag.name[1:]
    """

    vs_filter: Callable[[GitBranch | GitTag], bool] | None = None
    """A filter applied to branches and tags found matching :attr:`vs_pattern`
    to produce the final list of versions for which documentation will be
    generated.

    .. code-block:: python
    
        def vs_filter(branch_or_tag):
            if isinstance(branch, GitBranch):
                return (branch_or_tag.branch.startswith('release/') 
                    or branch_or_tag.branch.startswith('rc/')
                )
            else:
                return re.match(r'v\d+\.\d+\.\d+', branch_or_tag.name)
    
    """

    vs_pattern: str | None = None
    """A glob-style pattern to use when searching for branches and tags.
    Basic pattern matching like wildcards can be used here. For more complex
    matching, use :attr:`vs_filter`.
    """

    vs_sort: Callable[[list[GitBranch | GitTag]], list[GitBranch | GitTag]] | None = (
        None
    )
    """A custom sorter indicating the order of the versions. If this is
    not provided, then a natural sort will be performed on the branch/tag
    name directly, or on the result of :attr:`vs_display_name`. The sort
    should have the most recent version sorted first (descending sort).
    """

    @staticmethod
    def parse(conf: ModuleType, command_line: dict[str, Path | str]) -> "Config":
        """Parse the imported 'conf.py' file and any command-line arguments for
        any attributes related to configuring :mod:`versioned_sphinx`. 'conf.py'
        attributes take precedence.
        """
        c = Config()

        def get_attr(name: str):
            if hasattr(conf, name):
                return getattr(conf, name)
            if name in command_line:
                return command_line[name]

            return None

        if (vs_build_path := get_attr("vs_build_path")) is not None:
            assert isinstance(
                vs_build_path, (Path, str)
            ), "'vs_build_path' must be a Path or string"
            c.vs_build_path = vs_build_path

        if (vs_current_version := get_attr("vs_current_version")) is not None:
            assert isinstance(
                vs_current_version, str
            ), "'vs_current_version' must be a string"
            c.vs_current_version

        if (vs_display_name := get_attr("vs_display_name")) is not None:
            assert callable(vs_display_name), "'vs_display_name' must be callable"
            c.vs_display_name = vs_display_name

        if (vs_filter := get_attr("vs_filter")) is not None:
            assert callable(vs_filter), "'vs_filter' must be callable"
            assert isinstance(
                vs_filter(GitTag(datetime.now(), "test")), bool
            ), "'vs_filter' must return a bool"
            c.vs_filter = vs_filter

        if (vs_pattern := get_attr("vs_pattern")) is not None:
            assert isinstance(vs_pattern, str), "'vs_pattern' must be a string"
            c.vs_pattern = vs_pattern

        if (vs_sort := get_attr("vs_sort")) is not None:
            assert callable(vs_sort), "'vs_sort' must be callable"
            c.vs_sort = vs_sort

        return c
