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
import re
from typing import Any
import docx


def increment_date(match):
    """ Increment the year in a date match by 1. """
    year = int(match.group(1)) + 1
    return f" {year}"

def precompile_patterns():
    """ Precompile regular expressions for efficiency. """
    patterns = {
        'date_pattern': (re.compile(r"\s(20[0-9][0-9])"), lambda m: increment_date(m)),
        'name_pattern': (re.compile(r"(.\$\d+), (.\$\d+)"), lambda m: f"Mike Taylor{m.group(1)}, Bob Maurer{m.group(2)}"),
        'compliance_rate_pattern': (re.compile(r"(?P<first>[\s\w]+.\$)\d+(?P<second>,[\s\w]+.\$)\d+(?P<third>\.[\s\w]+\$)\d+.\d+(?P<fourth>\.[\w\s]+\$)\d+"), lambda m: r"\g<first>275 \g<second>275 \g<third>150-195 \g<fourth>65-75"),
        'consulting_rate_pattern': (re.compile(r"(?P<first>consulting.*:[\s\w]+.\$)\d+(?P<second>,[\s\w]+.\$)\d+(?P<third>\.[\s\w]+\$)\d+.\d+"), lambda m: r"\g<first>295 \g<second>295 \g<third>150-195")
    }
    return patterns

def update_paragraph(para, patterns: dict[str, Any]):
    """ Update dates and rates in a single paragraph. """
    updated = False
    for pattern, replacement in patterns.values():
        if pattern.search(para.text):
            para.text = re.sub(pattern, replacement, para.text)
            updated = True
    return updated

def process_engagement_letter(filename, processed_file_directory):
    """ Process a single engagement letter called filename and save to processed_file_directory."""
    try:
        doc = docx.Document(filename)
        updated = False

        patterns = precompile_patterns()

        for para in doc.paragraphs:
            if update_paragraph(para, patterns):
                updated = True

        if updated:
            error = None
            date_pattern, increment_method = patterns.get('date_pattern')
            
            new_filename = ''
            nameMatch = re.search(date_pattern, filename)
            if not nameMatch:
                base, ext = os.path.splitext(filename)
                new_filename = f'{base}_updated{ext}'

                error = f'An error occured when trying to increment file name: {filename}. File is now saved as {new_filename}.'
            else:
                new_filename = re.sub(date_pattern, increment_method, filename)

            new_file_path = os.path.join(processed_file_directory, new_filename)
            doc.save(new_file_path)
            return new_file_path, error
        else:
            return None, f'File {filename} was not updated.'
    except Exception as error:
        return None, f'An error occured while processing {filename}: {error}'
