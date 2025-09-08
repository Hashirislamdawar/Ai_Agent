import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types
from functions.get_files_info import schema_get_files_info
from functions.get_file_content import schema_get_file_content
from functions.run_python_file import schema_run_python_file
from functions.write_file import schema_write_file
from call_function import call_function  # <-- your dispatcher

def main():
    load_dotenv()

    api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    if len(sys.argv) < 2:
        print("I need a prompt")
        sys.exit(1)
    prompt = sys.argv[1]

    verbose_flag = False
    if len(sys.argv) == 3 and sys.argv[2] == "--verbose":
        verbose_flag = True

    # Conversation history
    messages = [
        types.Content(
            role="user",
            parts=[types.Part(text=prompt)]
        )
    ]

    available_functions = types.Tool(
        function_declarations=[
            schema_get_files_info,
            schema_get_file_content,
            schema_run_python_file,
            schema_write_file,
        ]
    )

    system_prompt = """
    You are a helpful AI coding agent.

    When a user asks a question or makes a request, make a function call plan. 
    You can perform the following operations:

    - List files and directories
    - Read the content of a file
    - Write to a file (create or update)
    - Run a Python file with optional arguments

    when the user asks about the code project - they are referring to the working directory. So you should typically start by looking at the project's file, and figuring out how to run the project's
    files and figuring out how to run the project and how to run its tests, you'll always want to test the tests and the actual process to verify the behaviour is working.

    All paths you provide should be relative to the working directory. 
    You do not need to specify the working directory in your function calls 
    as it is automatically injected for security reasons.
    """

    config = types.GenerateContentConfig(
        tools=[available_functions],
        system_instruction=system_prompt
    )

    # Feedback loop: up to 20 steps
    for step in range(20):
        if verbose_flag:
            print(f"\n=== Step {step+1} ===")

        response = client.models.generate_content(
            model="gemini-2.0-flash-001",
            contents=messages,
            config=config
        )

        # Add model’s response into conversation
        if response.candidates:
            for candidate in response.candidates:
                if candidate.content:
                    messages.append(candidate.content)

        # If the model wants to call a tool
        if response.function_calls:
            for function_call_part in response.function_calls:
                function_call_result = call_function(function_call_part, verbose=verbose_flag)

                # Append tool result to messages so model sees it
                messages.append(function_call_result)

                # Print tool output if verbose
                if verbose_flag:
                    print(f"-> {function_call_result.parts[0].function_response.response}")
        else:
            # No tool calls → model thinks it's done
            print(response.text)
            break
    else:
        print("Stopped after 20 steps (max iterations reached).")

    if verbose_flag and response.usage_metadata:
        print("\n=== Token Usage ===")
        print(f"Prompt tokens: {response.usage_metadata.prompt_token_count}")
        print(f"Candidates tokens: {response.usage_metadata.candidates_token_count}")
        print(f"Total tokens: {response.usage_metadata.total_token_count}")


if __name__ == "__main__":
    main()
