from pathlib import Path
from sphinx.application import Sphinx
from sphinx.util.typing import ExtensionMetadata
from .version import __version__


def setup(app: Sphinx) -> ExtensionMetadata:
    """The primary hook to make :mod:`versioned_sphinx` an extension.
    This function ensures that the appropriate CSS and JS files get
    added to the build.
    """
    for file in Path(app.outdir).parent.iterdir():
        if file.suffix == ".css":
            app.add_css_file(f"../../{file.name}")
        elif file.suffix == ".js":
            app.add_js_file(f"../../{file.name}")

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
        "version": __version__,
    }
