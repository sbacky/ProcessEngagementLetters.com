# Copyright (C) 2023 - Neil Crum (nhc.crum@outlook.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
import os
from pathlib import Path
import re

def directory_check(path, create_dir=False):
    """
    Verifies if a given path exists and is a directory.
    Optionally creates the directory if it does not exist.

    :param path: Path to the directory to check or create.
    :param create_if_not_exists: Flag to create directory if it does not exist.
    :return: True if the directory exists or was created, False otherwise.
    """
    if os.path.isdir(path):
        return True
    elif create_dir:
        try:
            os.makedirs(path)
            return True
        except OSError as e:
            print(f"Error creating directory: {e}")
            return False
    else:
        return False
    
def get_full_path(relative_path):
    """
    Returns the full path of a file given its relative path from the project root.
    The script is assumed to be located in /root/backend/utils/path_utils.py relative to the project root.

    :param relative_path: The relative path from the project root.
    :return: The full (absolute) path of the file as a Path object.
    """
    # Get the path of the current script
    current_script_path = Path(__file__).resolve()

    # Navigate up three levels to get the project root
    project_root = current_script_path.parents[2]

    # Construct the full path
    full_path = project_root.joinpath(relative_path)

    return str(full_path.resolve())

def custom_secure_filename(filename: str):
    """
    Sanitize filename while preserving specific non-alphanumeric characters.
    """
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')

    # Preserve non-alphanumeric characters before '... Engagement Letter'
    preserved_part = ''
    match = re.search(r'(.*Engagement Letter)', filename, re.IGNORECASE)
    if match:
        preserved_part = match.group(1)

    # Sanitize the rest of the filename
    sanitized_part = re.sub(r'[^a-zA-Z0-9._-]', '', filename.replace(preserved_part, ''))
    return preserved_part + sanitized_part