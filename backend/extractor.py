import docx
from docx.document import Document
import os
import re


def extract_address(paragraphs: list[str]):
    # Regular expression pattern for address
    address_pattern = r'\n(.+)\n(.+),\s+([A-Z]{2})\s+(\d{5})\n'
    address_text = "\n".join(paragraphs)

    match = re.search(address_pattern, address_text)
    if match:
        street_address = match.group(1)
        city_state_zip = match.group(2) + ", " + match.group(3) + " " + match.group(4)
        return street_address + "\n" + city_state_zip
    else:
        return "Address not found"

def extract_entities(paragraphs: list[str]):
    # Find the start of the table-like section
    start_index = next((i for i, p in enumerate(paragraphs) if "Name of Entity" in p and "Type of Return" in p), None)
    if start_index is None:
        return []

    entities = []
    # Process each line after the header
    for line in paragraphs[start_index + 1:]:
        if line.strip():  # Check if line is not empty
            # Splitting the line using regular expression to handle multiple spaces or tabs
            parts = re.split(r'\s{2,}|\t+', line.strip())
            if len(parts) == 2:
                name_of_entity, type_of_return = parts
                entities.append({"name_of_entity": name_of_entity, "type_of_return": type_of_return})
            else:
                # If the line does not conform to the expected format, assume the end of the entities section
                break

    return entities

def process_document(file_path: str):
    doc: Document = docx.Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs]

    address = extract_address(paragraphs)
    entities = extract_entities(paragraphs)

    return {
        "filename": os.path.basename(file_path),
        "address": address,
        "entities": entities
    }
