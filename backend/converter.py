import os
from docx2pdf import convert


def convert_word_to_pdf(doc_path: str, output_dir: str):
    # Convert secured filename back to original filename
    filename = os.path.basename(doc_path)
    converted_filename = ' '.join(filename.split('_'))

    # Construct output path
    pdf_filename = os.path.splitext(converted_filename)[0] + '.pdf'
    output_path = os.path.join(output_dir, pdf_filename)

    try:
        # Convert the Word document to PDF
        convert(doc_path, output_path)
        return pdf_filename, None
    except Exception as e:
        return None, f'Unable to print word document: {converted_filename}: {e}'
