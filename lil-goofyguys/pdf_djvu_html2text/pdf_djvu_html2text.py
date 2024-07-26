import os
import PyPDF2
import html2text
from bs4 import BeautifulSoup
import subprocess
import markdown

def pdf_to_text(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text

def html_to_text(html_path):
    with open(html_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
        return html2text.html2text(str(soup))

def djvu_to_text(djvu_path):
    result = subprocess.run(['djvutxt', djvu_path], capture_output=True, text=True)
    return result.stdout

def md_to_text(md_path):
    with open(md_path, 'r', encoding='utf-8') as file:
        md_content = file.read()
    html_content = markdown.markdown(md_content)
    return html2text.html2text(html_content)

def process_file(file_path):
    _, ext = os.path.splitext(file_path)
    processors = {
        '.pdf': pdf_to_text,
        '.html': html_to_text,
        '.htm': html_to_text,
        '.djvu': djvu_to_text,
        '.md': md_to_text
    }
    processor = processors.get(ext.lower())
    if processor:
        return processor(file_path)
    else:
        return f"Unsupported file type: {ext}"

def create_training_data(input_dir, output_file):
    with open(output_file, 'w', encoding='utf-8') as out_file:
        for root, _, files in os.walk(input_dir):
            for file in files:
                file_path = os.path.join(root, file)
                print(f"Processing: {file_path}")
                text = process_file(file_path)
                out_file.write(f"### File: {file_path}\n\n")
                out_file.write(text)
                out_file.write("\n\n")

def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        print(f"Directory '{directory}' does not exist. Creating it...")
        os.makedirs(directory)
        print(f"Created directory: {directory}")

def list_directory_contents(directory):
    print(f"Contents of the directory '{directory}':")
    print(os.listdir(directory))

def check_output_file(output_file):
    if os.path.exists(output_file):
        print(f"Output file '{output_file}' has been created successfully.")
        print("First few lines of the output file:")
        with open(output_file, 'r', encoding='utf-8') as f:
            print(f.read(500))  # Print first 500 characters
    else:
        print(f"Output file '{output_file}' was not created.")

def main():
    input_directory = './input_files'
    output_file = 'llm_training_data.txt'

    ensure_directory_exists(input_directory)
    list_directory_contents('.')
    
    create_training_data(input_directory, output_file)
    print(f"Training data has been created and saved to {output_file}")
    
    check_output_file(output_file)

if __name__ == "__main__":
    main()