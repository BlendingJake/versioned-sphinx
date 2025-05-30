from dataclasses import asdict
from os import getcwd
from pathlib import Path
import argparse
import json
import shutil
import re
from versioned_sphinx.config import Config
from versioned_sphinx.git import Git, GitBranch, GitTag
from versioned_sphinx.logger import ROOT_LOGGER as LOGGER
from versioned_sphinx.sphinx import Sphinx
from versioned_sphinx.version import __version__ as version


__version__ = version


def execute(config: Config, git: Git, sphinx: Sphinx):
    """Orchestrate producing all of the versions, joining them
    together, registering additional static files, and otherwise
    generating the versioned docs.
    """
    LOGGER.info("versioned-sphinx v%s starting...", version)
    verify_configuration(config, git, sphinx)

    build_path = config.build_path()
    LOGGER.info("Cleaning build directory '%s'...", build_path)
    if build_path.exists():
        shutil.rmtree(build_path)
    build_path.mkdir(exist_ok=True)

    LOGGER.info("Writing CSS and JS files...")
    to_copy = ["choices.min.css", "choices.min.js", "versioned_sphinx.js"]
    for f in to_copy:
        p = Path(__file__).parent / "static" / f
        shutil.copy(p, build_path / p.name)

    # Handle control CSS
    if config.vs_control_css:
        if isinstance(config.vs_control_css, Path) or ".css" in config.vs_control_css:
            p = Path(config.vs_control_css)
            if not p.is_absolute():
                p = (sphinx.get_conf_path().parent / p).resolve()

            shutil.copy(p, build_path / "versioned_sphinx.css")
        else:
            with open(
                build_path / "versioned_sphinx.css", "w", encoding="utf-8"
            ) as file:
                file.write(config.vs_control_css)
    else:
        shutil.copy(
            # verify_configuration makes sure this path exists
            sphinx.get_theme_css_file(sphinx.load_conf_file().html_theme),  # type: ignore
            build_path / "versioned_sphinx.css",
        )

    branches = git.get_branches(config.vs_pattern, config.vs_git_ref_location)
    LOGGER.info("Matched branches: %s", [b.name for b in branches])

    tags = git.get_tags(config.vs_pattern)
    LOGGER.info("Matched tags: %s", [t.name for t in tags])

    original_branch = git.get_current_branch()
    combined_with_name: list[tuple[str, GitBranch | GitTag]] = [
        (
            (config.vs_display_name(bt) if config.vs_display_name else bt.name),
            bt,
        )
        for bt in sort_branches_and_tags(
            config, filter_branches_and_tags(config, [*branches, *tags])
        )
    ]

    if config.vs_current_version:
        primary_version: str | None = None
        for name, bt in combined_with_name:
            if config.vs_current_version in (name, bt.name):
                primary_version = name

        assert (
            primary_version
        ), f"Not branch or tag found matching '{config.vs_current_version}'"
    else:
        primary_version = combined_with_name[0][0]

    built_paths: list[Path] = []
    for name, bt in combined_with_name:
        LOGGER.info("%s building...", name)
        git.checkout(bt)

        version_path = build_path / name
        built_paths.append(version_path)
        version_path.mkdir(exist_ok=True)

        sphinx.build(version_path)
        LOGGER.info("%s built", name)

    git.checkout_branch(original_branch)

    LOGGER.info("Consolidating HTML versions...")
    sphinx.consolidate_html_versions(built_paths)

    LOGGER.info("Writing root HTML file...")
    sphinx.write_root_html(build_path, primary_version)

    LOGGER.info("Writing version details...")
    with open(build_path / "versioned_sphinx.js", "a", encoding="utf-8") as file:
        file.write("\n\n")

        file.write("FILES_PER_VERSION = ")
        file.write(
            json.dumps(
                {
                    name: sphinx.get_html_file_names(path)
                    for path, (name, _) in zip(built_paths, combined_with_name)
                }
            )
        )
        file.write(";\n")

        file.write("THEME_INJECT_POINT = ")
        if config.vs_inject_selector:
            file.write(repr(config.vs_inject_selector))
        else:
            file.write(
                repr(
                    sphinx.get_theme_inject_location(sphinx.load_conf_file().html_theme)
                )
            )
        file.write(";\n")

        file.write("VERSIONS = ")
        file.write(
            json.dumps(
                [
                    {
                        "display_name": name,
                        "primary": primary_version == name,
                        **asdict(bt),
                    }
                    for name, bt in combined_with_name
                ],
                default=str,
            )
        )
        file.write(";\n")


def filter_branches_and_tags(
    config: Config, bts: list[GitBranch | GitTag]
) -> list[GitBranch | GitTag]:
    """Filter the list of branches and tags using methods provided by the config"""
    if config.vs_filter:
        return list(filter(config.vs_filter, bts))

    return bts


def main():
    parser = argparse.ArgumentParser(
        "versioned-sphinx",
        description=(
            "Generate versioned documentation using sphinx. Each version "
            + "is defined by a branch or tag. The docs are built for every "
            + "matching branch/tag and then combined together. Several of "
            + "these attributes can also be defined in conf.py."
        ),
    )

    parser.add_argument(
        "-p",
        "--pattern",
        type=str,
        help=(
            "The glob-style pattern which branches and tags must match "
            + "to use when generating the versioned docs. Can also be "
            + "defined in conf.py with 'vs_pattern'. "
        ),
    )

    parser.add_argument(
        '-l',
        '--location',
        type=str,
        choices=["all", "local", "remote"],
        default='remote',
        help=(
            "The location of branches/tags to use for the versions. By default, only "
            + "remote branches or tags will be included. To build documentation "
            + "from a branch or tag which only exists locally, make sure to update "
            + "this to 'all' or 'local'."
        )
    )

    parser.add_argument(
        "-r",
        "--repo",
        type=Path,
        help=(
            "The path of the repository containing the project to document. "
            + "If not provided, the current working path will be used."
        ),
    )

    parser.add_argument(
        "-c",
        "--conf",
        type=Path,
        help=(
            "The path of the sphinx project's conf.py file, if it is in "
            + "a non-standard location. By default, 'repo' / docs will be "
            + "searched."
        ),
    )

    parser.add_argument(
        "-b",
        "--build-path",
        type=Path,
        help=(
            "The path of sphinx's build folder, either as a path relative to "
            + "'repo' or an absolute path. By default, this will be root / 'docs' "
            + "/ 'build'."
        ),
    )

    parser.add_argument(
        "-v",
        "--version",
        type=str,
        help=(
            "The name of the branch or tag representing the current version. "
            + "This can also be defined with 'vs_current_version' in conf.py. "
            + "Defaults to the 'newest' version after sorting."
        ),
    )

    args = parser.parse_args()

    if args.repo:
        assert args.repo.exists(), f"Provided repo path '{args.repo}' does not exist"
        repo: Path = args.repo
    else:
        repo = Path(getcwd())

    if args.conf:
        assert args.conf.exists(), f"Provided conf.py path '{args.conf}' does not exist"
        conf: Path | None = args.conf
    else:
        conf = None

    if args.build_path:
        assert (
            args.build_path.exists()
        ), f"Provided build path '{args.build_path}' does not exist"
        build: Path = args.build_path
    else:
        build = repo / "docs" / "build"

    git = Git(repo)
    sphinx = Sphinx(repo, conf)
    config = Config.parse(
        sphinx.load_conf_file(),
        {
            "vs_build_path": build,
            "vs_current_version": args.version,
            "vs_git_ref_location": args.location,
            "vs_pattern": args.pattern,
        },
    )

    LOGGER.info("Will operate in '%s'", repo)
    execute(config, git, sphinx)


NAT_SORT_PATTERN = re.compile(r"(\d+)")


def natural_sort_tuple(key: str) -> list[str | int]:
    """Turn a string key into a tuple which can be sorted to
    apply a natural sort. To do this, any numeric parts are split
    into their own value in the tuple, turning something like ``v1.0``
    into ``('v', 1, '.', 0)``, which will then sort correctly when compared
    with something like ``v10.0`` which gets converted to ``('v', 10, '.', 0)``.
    """
    return [int(v) if v.isdigit() else v for v in NAT_SORT_PATTERN.split(key)]


def sort_branches_and_tags(
    config: Config, bts: list[GitBranch | GitTag]
) -> list[GitBranch | GitTag]:
    """Sort the list of branches and tags using either
    :attr:`~versioned_sphinx.config.Config.vs_sort` or a natural sort
    performed on the name of the branch or tag (or the result of applying
    :attr:`~versioned_sphinx.config.Config.vs_display_name` if present).
    """
    if config.vs_sort:
        return config.vs_sort(bts)

    if config.vs_display_name:
        key_to_value = [(config.vs_display_name(bt), bt) for bt in bts]
    else:
        key_to_value = [
            (natural_sort_tuple(bt.name if isinstance(bt, GitBranch) else bt.name), bt)
            for bt in bts
        ]

    sort = sorted(key_to_value, key=lambda x: x[0], reverse=True)
    return [kv[1] for kv in sort]


def verify_configuration(config: Config, git: Git, sphinx: Sphinx):
    """Verify via assertions that required parameters are available"""

    conf = sphinx.load_conf_file()
    assert hasattr(conf, "html_theme"), "'html_theme' must be defined in 'conf.py'"
    theme = conf.html_theme
    assert (
        config.vs_inject_selector is not None
        or sphinx.get_theme_inject_location(theme) is not None
    ), (
        f"Theme '{theme}' does not have a pre-defined inject "
        + "location and none was provided via 'vs_inject_selector'"
    )
    LOGGER.info(
        "Theme '%s' inject location: '%s'",
        theme,
        config.vs_inject_selector or sphinx.get_theme_inject_location(theme),
    )

    assert config.vs_control_css is not None or sphinx.get_theme_css_file(theme), (
        f"Theme '{theme}' does not have a pre-defined CSS file "
        + "and none was provided via 'vs_control_css'"
    )

    assert git.get_branches(config.vs_pattern, config.vs_git_ref_location) or git.get_tags(
        config.vs_pattern
    ), "No branches or tags found meeting requirements"


if __name__ == "__main__":
    main()
