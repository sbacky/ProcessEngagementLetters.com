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
import docx


def increment_date(match):
    """ Increment the year in a date match by 1. """
    year = int(match.group(1)) + 1
    return f" {year}"

def get_new_filename(base_file, date_pattern):
    """ Generate a new filename with incremented date. """
    nameMatch = re.search(date_pattern, base_file)
    if not nameMatch:
        base, ext = os.path.splitext(base_file)
        return f'{base}_updated{ext}'
    return re.sub(date_pattern, lambda m: increment_date(m), base_file)

def clean_filename(filename):
    """Clean filename by dropping everything after 'Engagement Letter'."""
    pattern = re.compile(r'(.*Engagement Letter).*?(\.docx)$', re.IGNORECASE)
    match = pattern.search(filename)
    if match:
        return f'{match.group(1)}{match.group(2)}'
    return filename

def update_paragraphs(doc, date_pattern, partner_rate_pattern, associate_rate_pattern):
    updated = False
    for para in doc.paragraphs:
        # Update dates
        if date_pattern.search(para.text):
            para.text = re.sub(date_pattern, lambda m: increment_date(m), para.text)
            updated = True

        # Update partner rates
        if partner_rate_pattern.search(para.text):
            para.text = re.sub(partner_rate_pattern, "Partner hourly rates are: Mike Taylor–$275, Bob Maurer–$275. Our Associate hourly rates range from $150-195. Our bookkeeping rate is $65-75 per hour.", para.text)
            updated = True

        # Update associate rates
        if associate_rate_pattern.search(para.text):
            para.text = re.sub(associate_rate_pattern, "Partner hourly rates are: Mike Taylor–$295, Bob Maurer–$295. Our Associate hourly rates range from $150-195.", para.text)
            updated = True

    return updated

def process_engagement_letter(filename: str, processed_file_directory):
    """ Process a single engagement letter. """
    try:
        doc = docx.Document(filename)
        # regex patterns
        date_pattern = re.compile(r"\s(20[0-9][0-9])")
        partner_rate_pattern = re.compile(r"Partner hourly rates are:.*Our Associate hourly rates range from \$\d+-\d+\. Our bookkeeping rate is \$\d+-\d+ per hour\.")
        associate_rate_pattern = re.compile(r"Partner hourly rates are:.*Our Associate hourly rates range from \$\d+-\d+\.")


        updated = update_paragraphs(doc, date_pattern, partner_rate_pattern, associate_rate_pattern)

        if updated:
            # filenames have spaces ' ' replaced with underscores '_'. These need to be converted back to spaces.
            filename = ' '.join(filename.split('_'))

            # Increment year in filename
            new_filename = get_new_filename(os.path.basename(filename), date_pattern)
            # Clean the filename of the previous years tracking info
            cleaned_filename = clean_filename(new_filename)
            new_file_path = os.path.join(processed_file_directory, cleaned_filename)
            doc.save(new_file_path)
            return new_file_path, None
        return None, f'File {filename} was not updated.'

    except Exception as error:
        return None, str(error)
