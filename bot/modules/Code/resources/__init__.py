from pathlib import Path

__location__ = Path(__file__).parent

staging_root = Path("/dev/shm/code-staging")  # noqa: S108

# Standalone runner scripts, one per supported language.
python_script_path = __location__ / "python_compiler.sh"
r_script_path = __location__ / "r_compiler.sh"
