import os
import sys
import subprocess
import locale
from google.genai import types

def run_python_file(working_directory, file_path, args=[]):
    """
    Execute a Python file inside `working_directory` and return a formatted
    string containing STDOUT/STDERR and exit-code info.

    - Prevents execution outside working_directory (uses commonpath).
    - Ensures file exists and ends with .py.
    - Runs with a 30s timeout.
    - Captures raw bytes from stdout/stderr and decodes with utf-8 (replace).
    - Sets PYTHONUTF8 and PYTHONIOENCODING in the child env to encourage UTF-8.
    """
    abs_working_dir = os.path.abspath(working_directory)
    abs_file_path = os.path.abspath(os.path.join(working_directory, file_path))

    # Safer check to ensure file is inside working_directory
    try:
        if os.path.commonpath([abs_working_dir, abs_file_path]) != abs_working_dir:
            return f'Error: Cannot execute "{file_path}" as it is outside the permitted working directory'
    except ValueError:
        # commonpath can raise ValueError on different drives on Windows
        return f'Error: Cannot execute "{file_path}" as it is outside the permitted working directory'

    if not os.path.isfile(abs_file_path):
        return f'Error: File "{file_path}" not found.'

    if not abs_file_path.lower().endswith(".py"):
        return f'Error: "{file_path}" is not a Python file.'

    # Prepare environment: force Python to use UTF-8 for stdio and replace errors
    env = {**os.environ}
    env["PYTHONUTF8"] = "1"
    # 'utf-8:replace' means encode/decode with replacement for errors
    env["PYTHONIOENCODING"] = "utf-8:replace"

    cmd = [sys.executable, abs_file_path] + list(args)

    try:
        completed = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,   # capture raw bytes
            stderr=subprocess.PIPE,
            cwd=abs_working_dir,
            timeout=30,
            env=env
        )

        # Decode bytes to text in a safe way (utf-8 with replacement)
        def safe_decode(b):
            if not b:
                return ""
            try:
                return b.decode("utf-8", errors="replace")
            except Exception:
                # fallback to locale preferred encoding
                return b.decode(locale.getpreferredencoding(False), errors="replace")

        stdout_text = safe_decode(completed.stdout).rstrip()
        stderr_text = safe_decode(completed.stderr).rstrip()

        parts = []
        if stdout_text:
            parts.append("STDOUT:\n" + stdout_text)
        if stderr_text:
            parts.append("STDERR:\n" + stderr_text)
        if completed.returncode != 0:
            parts.append(f"Process exited with code {completed.returncode}")
        if not parts:
            return "No output produced."

        return "\n".join(parts)

    except subprocess.TimeoutExpired:
        return "Error: executing Python file: process timed out (30s)"
    except Exception as e:
        return f"Error: executing Python file: {e}"


schema_run_python_file = types.FunctionDeclaration(
    name="run_python_file",
    description="Executes a Python file within the working directory, captures its output, and returns STDOUT/STDERR and exit code information.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The path to the Python file to execute, relative to the working directory."
            ),
            "args": types.Schema(
                type=types.Type.ARRAY,
                description="A list of string arguments to pass to the Python script (optional).",
                items=types.Schema(type=types.Type.STRING)
            ),
        },
        required=["file_path"]  # file_path must always be provided
    ),
)
