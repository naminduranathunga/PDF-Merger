def merge_pdfs(pdf_list, output_path):
    from PyPDF2 import PdfWriter, PdfReader

    pdf_writer = PdfWriter()

    for pdf in pdf_list:
        pdf_reader = PdfReader(pdf)
        for page in range(len(pdf_reader.pages)):
            pdf_writer.add_page(pdf_reader.pages[page])

    with open(output_path, 'wb') as out_file:
        pdf_writer.write(out_file)


def split_pdf(pdf_path, start_page, end_page, output_path):
    from PyPDF2 import PdfReader, PdfWriter

    pdf_reader = PdfReader(pdf_path)
    pdf_writer = PdfWriter()

    for page in range(start_page - 1, end_page):  # Adjust for zero-based index
        pdf_writer.add_page(pdf_reader.pages[page])

    with open(output_path, 'wb') as out_file:
        pdf_writer.write(out_file)


def add_pdf_to_list(pdf_list, pdf_path):
    if pdf_path not in pdf_list:
        pdf_list.append(pdf_path)


def remove_pdf_from_list(pdf_list, pdf_path):
    if pdf_path in pdf_list:
        pdf_list.remove(pdf_path)


def move_pdf_in_list(pdf_list, current_index, new_index):
    if 0 <= current_index < len(pdf_list) and 0 <= new_index < len(pdf_list):
        pdf_list.insert(new_index, pdf_list.pop(current_index))