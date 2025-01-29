import os
from openai import OpenAI
from pathlib import Path
import argparse
import re

# Environment Variables for OpenAI API Authentication
client = OpenAI(
    api_key=os.getenv("OPEN_AI_API_KEY"),
    organization=os.getenv("OPEN_AI_ORG_ID"),
    project=os.getenv("OPEN_AI_PROJECT_ID"),
)


# Helper function to convert file content
def convert_code(content, source_lang, target_lang, target_snippet):
    """
    Convert code from one language to another using OpenAI API.
    """
    prompt = f"""
    Convert the following {source_lang} code to {target_lang}.
    Please don't add any comments in code. Don't replace constant class properties with it string values.
    Add use statements like in provided snippets in {source_lang}.
    Use the provided {target_lang} code snippet as the basis for the conversion:

    {content}

    Here is a code snippet in {target_lang} to use as a reference:
    
    {target_snippet}
    """
    try:
        print("Start request to OpenAI")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful code conversion assistant."},
                {"role": "user", "content": prompt},
            ],
        )
        print("Getted response")
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error during API call: {e}")
        return None


# Main function to process files
def process_files(folder, source_ext, target_ext, source_lang, target_lang, target_snippet):
    # Pattern to find code snippet in response message
    pattern = f"```{target_lang}((.|\s)*?)```"
    """
    Walk through the folder and convert files with the specified extension.
    """
    for root, _, files in os.walk(folder):
        for file in files:
            # Process only files with the specified source extension
            if file.endswith(source_ext):
                file_path = Path(root) / file
                print(f"Processing file: {file_path}")

                with open(file_path, "r") as f:
                    content = f.read()

                converted_content = convert_code(content, source_lang, target_lang, target_snippet)
                if converted_content:
                    matches = re.findall(pattern, converted_content)
                    if matches:
                        converted_content = matches[0][0].strip()
                    target_file_path = file_path.with_suffix(target_ext)
                    with open(target_file_path, "w") as f:
                        f.write(converted_content)
                    print(f"Converted file saved as: {target_file_path}")
                else:
                    print(f"Failed to convert file: {file_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert source code files between programming languages.")
    parser.add_argument("folder", type=str, help="Path to the folder containing source files.")
    parser.add_argument("source_ext", type=str, help="Source file extension (e.g., .js).")
    parser.add_argument("target_ext", type=str, help="Target file extension (e.g., .py).")
    parser.add_argument("source_lang", type=str, help="Source language (e.g., JavaScript).")
    parser.add_argument("target_lang", type=str, help="Target language (e.g., Python).")
    parser.add_argument("target_snippet_file", type=str, help="File containing a code snippet in the target language.")

    args = parser.parse_args()

    # Read the target snippet from the provided file
    try:
        with open(args.target_snippet_file, "r") as snippet_file:
            target_snippet = snippet_file.read()
    except Exception as e:
        print(f"Error reading target snippet file: {e}")
        exit(1)

    print("Starting code conversion...")
    process_files(args.folder, args.source_ext, args.target_ext, args.source_lang, args.target_lang, target_snippet)

    print("Conversion process completed.")
