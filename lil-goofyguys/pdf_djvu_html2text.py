#Thanks Julius
import os
import PyPDF2
import html2text
from bs4 import BeautifulSoup

def pdf_to_text(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\
"
    return text

def html_to_text(html_path):
    with open(html_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
        return html2text.html2text(str(soup))

def djvu_to_text(djvu_path):
    # For DjVu files, we'll use a system command to convert to text
    # This requires djvulibre-bin to be installed on the system
    import subprocess
    result = subprocess.run(['djvutxt', djvu_path], capture_output=True, text=True)
    return result.stdout

def process_file(file_path):
    _, ext = os.path.splitext(file_path)
    if ext.lower() == '.pdf':
        return pdf_to_text(file_path)
    elif ext.lower() in ['.html', '.htm']:
        return html_to_text(file_path)
    elif ext.lower() == '.djvu':
        return djvu_to_text(file_path)
    else:
        return f"Unsupported file type: {ext}"

def create_training_data(input_dir, output_file):
    with open(output_file, 'w', encoding='utf-8') as out_file:
        for root, _, files in os.walk(input_dir):
            for file in files:
                file_path = os.path.join(root, file)
                print(f"Processing: {file_path}")
                text = process_file(file_path)
                out_file.write(f"### File: {file_path}\
\
")
                out_file.write(text)
                out_file.write("\
\
")

# Example usage
input_directory = './input_files'
output_file = 'llm_training_data.txt'

# Check if the input directory exists
if not os.path.exists(input_directory):
    print(f"Input directory '{input_directory}' does not exist. Creating it...")
    os.makedirs(input_directory)
    print(f"Created directory: {input_directory}")

# List the contents of the current directory
print("Contents of the current directory:")
print(os.listdir('.'))

create_training_data(input_directory, output_file)
print(f"Training data has been created and saved to {output_file}")

# Check if the output file was created
if os.path.exists(output_file):
    print(f"Output file '{output_file}' has been created successfully.")
    print("First few lines of the output file:")
    with open(output_file, 'r', encoding='utf-8') as f:
        print(f.read(500))  # Print first 500 characters
else:
    print(f"Output file '{output_file}' was not created.")
