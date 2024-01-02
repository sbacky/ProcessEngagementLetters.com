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
from docx.document import Document


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

def get_partner_rates(partner_rates: list[dict[str, str]]):
    partner1 = f"{partner_rates[0].get('name')}–{partner_rates[0].get('rate')}"
    partner2 = f"{partner_rates[1].get('name')}–{partner_rates[1].get('rate')}"
    return partner1, partner2
    

def update_paragraphs(doc: Document, date_pattern, compliance_rates_pattern, consulting_rates_pattern, **rate_options):
    updated = False
    default_partner_rates = [
        {
            "name": "No name set",
            "rate": "No rate set"
        }, {
            "name": "No name set",
            "rate": "No rate set"
        }
    ]
    for para in doc.paragraphs:
        # Update dates
        if date_pattern.search(para.text):
            para.text = re.sub(date_pattern, lambda m: increment_date(m), para.text)
            updated = True

        # Update compliance rates
        if compliance_rates_pattern.search(para.text):
            # This is a list of dictionaries with each partner and their rate.
            compliance_partner1, compliance_partner2 = get_partner_rates(rate_options.get('COMPLIANCE_PARTNER_RATES', default_partner_rates))
            compliance_associate_rates = rate_options.get('COMPLIANCE_ASSOCIATE_RATES', 'No rate set')
            compliance_bookkeeping_rates = rate_options.get('COMPLIANCE_BOOKKEEPING_RATES', "No rate set")

            para.text = re.sub(compliance_rates_pattern, f"Partner hourly rates are: {compliance_partner1}, {compliance_partner2}. Our Associate hourly rates range from {compliance_associate_rates}. Our bookkeeping rate is {compliance_bookkeeping_rates} per hour.", para.text)
            updated = True
        # Update consulting rates
        elif consulting_rates_pattern.search(para.text):
            # This is a list of dictionaries with each partner and their rate.
            consulting_partner1, consulting_partner2 = get_partner_rates(rate_options.get('CONSULTING_PARTNER_RATES', default_partner_rates))
            consulting_associate_rates = rate_options.get('CONSULTING_ASSOCIATE_RATES', 'No rate set')

            para.text = re.sub(consulting_rates_pattern, f"Partner hourly rates are: {consulting_partner1}, {consulting_partner2}. Our Associate hourly rates range from {consulting_associate_rates}.", para.text)
            updated = True

    return updated

def process_engagement_letter(filename: str, processed_file_directory, **rate_options):
    """ Process a single engagement letter. """
    try:
        doc: Document = docx.Document(filename)
        # regex patterns
        date_pattern = re.compile(r"\s(20[0-9][0-9])")
        compliance_rates_pattern = re.compile(r"Partner hourly rates are:\s*.*Our Associate hourly rates range from \$\d+-\d+\s*\.\s*Our bookkeeping rate is \$\d+-\d+\s*per hour\.")
        consulting_rates_pattern = re.compile(r"Partner hourly rates are:\s*.*Our Associate hourly rates range from \$\d+-\d+\s*\.")

        updated = update_paragraphs(doc, date_pattern, compliance_rates_pattern, consulting_rates_pattern, **rate_options)

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
