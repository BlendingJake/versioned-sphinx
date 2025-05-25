"""Mechanisms for interacting with sphinx like finding the ``conf.py``
file, determining build location, and actually executing the build.
"""

from os import walk
from pathlib import Path
from types import ModuleType
import importlib
import shutil
import subprocess
import sys
from versioned_sphinx.logger import get_logger


LOGGER = get_logger("sphinx")
REDIRECT_HTML = """
<!DOCTYPE html>
<html>
    <head>
        <meta http-equiv="refresh" content="0; url='{primary_version}'" />
    </head>
    <body>
        <p>Redirecting to primary version...</p>
    </body>
</html>
"""


class Sphinx:
    """Mechanisms related to interacting with sphinx like actually
    executing a build, finding the 'conf.py' file, and so forth.
    """

    def __init__(self, repo_path: Path | str, conf_path: Path | str | None = None):
        """Construct a new :class:`Sphinx` instance pointing at
        a project with sphinx already configured.

        :param repo_path: The root folder of the project
        :param conf_path: Optionally, the path of ``conf.py`` if it is in
            a non-standard location. Otherwise, ``repo_path / docs`` will be
            explored to try and find it.
        """
        self._repo_dir = Path(repo_path)
        conf: Path | None = None

        if conf_path:
            conf = Path(conf_path)
            assert conf.exists(), f"'conf.py' path of '{conf}' does not exist"
        else:
            docs_path = self._repo_dir / "docs"
            assert (
                docs_path.exists()
            ), f"'docs' folder does not exist in '{self._repo_dir}'"

            for root, _, filenames in walk(docs_path):
                for filename in filenames:
                    if filename == "conf.py":
                        conf = Path(root) / filename
                        break

                if conf is not None:
                    break

            assert (
                conf is not None
            ), f"Could not find 'conf.py' any where under '{docs_path}'"
            LOGGER.debug("Resolved 'conf.py' to %s", conf)

        self._conf_file = conf
        self._source_dir = conf.parent

    def build(self, output: Path):
        """Build the current sphinx project to a specific folder"""
        LOGGER.debug("Building '%s' to '%s'", self._source_dir, output)
        try:
            response = subprocess.run(
                ["sphinx-build", "-M", "html", str(self._source_dir), str(output)],
                capture_output=True,
                check=True,
            )
        except FileNotFoundError as e:
            LOGGER.error("Error during build. Are you sure sphinx is installed?")
            raise e
        except subprocess.CalledProcessError as e:
            LOGGER.error(
                "Error during build. Are you sure all themes and extensions are installed?"
            )
            raise e

        stdout = response.stdout.decode()
        assert (
            "build succeeded" in stdout
        ), f"Build did not succeed: {stdout.replace('\n', ' ')}"

    @staticmethod
    def consolidate_html_versions(versions: list[Path]):
        """Consolidate from having a ``doctrees`` and ``html`` folder in each
        version to moving all files from ``html`` up to the root of the
        version folder. Going from:
            * v1

                * doctrees
                * html

                    * <files>

        To:
            * v1

                <files>
        """
        for v in versions:
            doctrees =  v / "doctrees"
            LOGGER.debug("Removing '%s'...", doctrees)
            shutil.rmtree(doctrees)

            html = v / 'html'
            LOGGER.debug("Moving '%s' -> '%s'...", html, v)
            for item in html.iterdir():
                if item.is_file():
                    item.rename(v / item.name)
                else:
                    shutil.move(item, v / item.name)

            shutil.rmtree(html)

    def get_conf_path(self) -> Path:
        """Get the filepath of 'conf.py'"""
        return self._conf_file

    def load_conf_file(self) -> ModuleType:
        """Import the 'conf.py' file and get all of the variables
        defined within it.
        """
        initial_path = list(sys.path)
        sys.path = [str(self._source_dir), *sys.path]

        conf = importlib.import_module("conf")
        sys.path = initial_path

        return conf
    
    def write_root_html(self, build_path: Path, primary_version: str):
        with open(build_path / 'index.html', 'w', encoding='utf-8') as file:
            file.write(REDIRECT_HTML.format(
                primary_version=f"{primary_version}/index.html"
            ))
