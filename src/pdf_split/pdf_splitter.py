import argparse
from PyPDF2 import PdfReader, PdfWriter
import os


def split_pdf(in_pdf, start_page, end_page, output_pdf=None, verbose=False):
    """
    Splits a PDF into a new PDF containing pages from start_page to end_page (inclusive).

    :param in_pdf: The input PDF file path.
    :param start_page: The starting page number (1-based).
    :param end_page: The ending page number (1-based, inclusive).
    :param output_pdf: The output PDF file path (if None, generated automatically).
    :param verbose: If True, prints progress details.
    """
    # Convert to 0-based index for internal use
    start_page = start_page - 1  # Convert to 0-based index
    end_page = end_page - 1      # Convert to 0-based index (inclusive)

    try:
        # Reading the input PDF
        pdf_reader = PdfReader(in_pdf)
        pdf_writer = PdfWriter()

        num_pages = len(pdf_reader.pages)
        if start_page < 0 or end_page >= num_pages or start_page > end_page:
            raise ValueError(f"Invalid page range: {start_page + 1} to {end_page + 1} for PDF with {num_pages} pages.")

        # Automatically generate output filename if not provided
        if output_pdf is None:
            base_name = os.path.splitext(os.path.basename(in_pdf))[0]
            output_pdf = f"{base_name}_pages_{start_page + 1}_to_{end_page + 1}.pdf"

        # Add the pages from start_page to end_page (inclusive)
        for page_num in range(start_page, end_page + 1):
            pdf_writer.add_page(pdf_reader.pages[page_num])
            if verbose:
                print(f"Adding page {page_num + 1} to {output_pdf}")

        # Write the split PDF to the output file
        with open(output_pdf, 'wb') as out_file:
            pdf_writer.write(out_file)

        if verbose:
            print(f"Successfully split pages {start_page + 1} to {end_page + 1} into {output_pdf}")

    except FileNotFoundError as e:
        print(f"Error: The file {in_pdf} was not found.")
        raise e
    except ValueError as e:
        print(f"Error: {e}")
        raise e
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise e




def main():
    parser = argparse.ArgumentParser(description="Split a PDF into smaller sections based on page ranges.")

    # Input PDF file
    parser.add_argument('input_pdf', type=str, help="Path to the input PDF file")

    # Start and end page range
    parser.add_argument('start_page', type=int, help="Start page (0-based index)")
    parser.add_argument('end_page', type=int, help="End page (exclusive, 0-based index)")

    # Optional output file name
    parser.add_argument('-o', '--output', type=str, help="Output PDF file name (optional)", default=None)

    # Verbose mode
    parser.add_argument('-v', '--verbose', action='store_true', help="Print progress information")

    args = parser.parse_args()

    # Call the split function with parsed arguments
    split_pdf(args.input_pdf, args.start_page, args.end_page, args.output, args.verbose)


if __name__ == "__main__":
    main()
