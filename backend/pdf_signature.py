import os

from PyPDF2 import PdfReader, PdfWriter, Transformation
import pdfplumber


def find_signature_position(pdf_path):
    """
    Find the position to place the signature based on the specified lines.
    Returns the page number and y-coordinate for the signature.
    """
    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                lines = text.split('\n')
                for i, line in enumerate(lines):
                    if "Very truly yours," in line:
                        for j in range(i+1, len(lines)):
                            if lines[j].strip():  # Find the first non-empty line after "Very truly yours,"
                                return page_number, page.height - page.extract_words()[-1]['bottom']

    return None, None  # Return None if the position is not found

def extract_name(pdf_path):
    """
    Extract the name following "Very truly yours,".
    Returns the extracted name.
    """
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines = text.split('\n')
                for i, line in enumerate(lines):
                    if "Very truly yours," in line:
                        for j in range(i+1, len(lines)):
                            name_line = lines[j].strip()
                            if name_line:  # Find the first non-empty line after "Very truly yours,"
                                return name_line
    return None

def add_signature(pdf_path, output_path, signature_path, position):
    """
    Add the signature to the PDF at the specified position.
    """
    pdf_reader = PdfReader(pdf_path)
    pdf_writer = PdfWriter()
    signature_reader = PdfReader(signature_path)

    try:
        for i in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[i]
            # Add signature on the specified page
            if i == position[0] and len(signature_reader.pages) > 0:
                signature_page = signature_reader.pages[0]

                # Calculate the scale based on the signature size and desired line height (20pt)
                desired_height_in_inches = 20 / 72
                # convert points to inches
                signature_height = signature_page.mediabox.height / 72
                scale = desired_height_in_inches / signature_height

                # Calculate translation values
                # 1.25 inches from the left, converted to points
                tx = 1.25 * 72
                # y position adjusted for the scaled signature height
                ty = position[1] - (desired_height_in_inches * 72)

                # Scale and position the signature
                signature_page.add_transformation(Transformation().scale(scale).translate(tx, ty))
                page.merge_page(signature_page)

            pdf_writer.add_page(page)

        with open(output_path, 'wb') as output_file:
            pdf_writer.write(output_file)

        return os.path.basename(output_path), None
    except Exception as e:
        return None, f'An error has occurred adding signature stamp to {os.path.basename(output_path)}: {e}'
    finally:
        # Close writer
        pdf_writer.close()
