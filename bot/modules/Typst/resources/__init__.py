from pathlib import Path

# Reuse the Tex module's generic "compilation failed" placeholder image.
from modules.Tex.resources import failed_image_path

__location__ = Path(__file__).parent

# Load default preamble from file
with Path.open(__location__ / "default_preamble.typ") as preamble:
    default_preamble = preamble.read()

staging_root = Path("/dev/shm/typst-staging")  # noqa: S108

# Store the path to the typst compile script
typst_script_path = __location__ / "typst_compiler.sh"

# .typ resource files
importable_resources = (
    __location__ / "unicode-math.typ",
    __location__ / "memdesign.typ",
)
