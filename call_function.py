import os
from google.genai import types

# Import your functions from the functions/ directory
from functions.get_files_info import get_files_info
from functions.get_file_content import get_file_content
from functions.write_file import write_file
from functions.run_python_file import run_python_file

# Map function names -> actual implementations
FUNCTIONS = {
    "get_files_info": get_files_info,
    "get_file_content": get_file_content,
    "write_file": write_file,
    "run_python_file": run_python_file,
}

def call_function(function_call_part, verbose=False):
    """
    Handles function dispatch based on the LLM's request.
    Injects the working_directory automatically.
    """
    function_name = function_call_part.name
    args = dict(function_call_part.args or {})

    # Always add working_directory for safety
    args["working_directory"] = "./calculator"

    if verbose:
        print(f"Calling function: {function_name}({args})")
    else:
        print(f" - Calling function: {function_name}")

    # Dispatch to correct function
    if function_name not in FUNCTIONS:
        return types.Content(
            role="tool",
            parts=[
                types.Part.from_function_response(
                    name=function_name,
                    response={"error": f"Unknown function: {function_name}"},
                )
            ],
        )

    try:
        function_result = FUNCTIONS[function_name](**args)
    except Exception as e:
        function_result = f"Exception while calling {function_name}: {e}"

    # Return result wrapped in types.Content
    return types.Content(
        role="tool",
        parts=[
            types.Part.from_function_response(
                name=function_name,
                response={"result": function_result},
            )
        ],
    )
