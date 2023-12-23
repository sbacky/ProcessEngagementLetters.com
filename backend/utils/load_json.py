import json
import os
from typing import Any


def load_json_data(file_path: str) -> dict[str, Any]:
    """
    Loads a JSON file and returns the contents as a python object ie list, dict, etc....
    Checks if the file exists, is a file, and has a '.json' extension.

    :param file_path: Path to the JSON file.
    :return: Dictionary containing the JSON contents, or None if an error occurs.
    """
    # Check if the file exists and is a file
    if not os.path.exists(file_path):
        print(f"Error: The file '{file_path}' does not exist.")
        return None
    if not os.path.isfile(file_path):
        print(f"Error: The path '{file_path}' is not a file.")
        return None

    # Check for '.json' extension
    if not file_path.endswith('.json'):
        print(f"Error: The file '{file_path}' does not have a .json extension.")
        return None

    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except json.JSONDecodeError:
        print(f"Error: The file '{file_path}' does not contain valid JSON.")
    except IOError as io_error:
        print(f"I/O Error: {io_error}")
    return None