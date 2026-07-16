import os
from pathlib import Path

__location__ = Path(__file__).parent

# Load default preamble from file
with Path.open(__location__ / "default_preamble.tex") as preamble:
    default_preamble = preamble.read()

# Load list of whitelisted packages from file
with Path.open(__location__ / "whitelist.txt") as pw:
    whitelisted_packages = [line.strip() for line in pw]

# Store the path to the failed image
failed_image_path = __location__ / "failed.png"
failed_dir = __location__.parents[3] / "tex" / "failed"
staging_root = Path("/dev/shm/tex-staging")  # noqa: S108

# Store the path to the latex compile script
pdflatex_script_path = __location__ / "pdflatex_compiler.sh"
pdftex_script_path = __location__ / "pdftex_compiler.sh"

lualatex_script_path = __location__ / "lualatex_compiler.sh"
luatex_script_path = __location__ / "luatex_compiler.sh"
xelatex_script_path = __location__ / "xelatex_compiler.sh"
pythontex_script_path = __location__ / "pythontex_compiler.sh"
