from pathlib import Path
from uuid import uuid4
import tempfile
from versioned_sphinx.sphinx import Sphinx

s = Sphinx(Path(r"C:\Users\Amych\Documents\Projects\sphinx-test"))

print(s.get_conf_path())

temp_dir = Path(tempfile.gettempdir()) / uuid4().hex
print(temp_dir)
s.build(Path(temp_dir))
