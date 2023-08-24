import sys
import openai
import fitz
from dotenv import load_dotenv
import os

load_dotenv()

def read_prompt_from_file(prompt_file):
    with open(prompt_file, "r") as f:
        prompt = f.read()
    return prompt

def generate_response_from_pdf(prompt, pdf_text, max_tokens):
    conversation = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": pdf_text},
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation,
        max_tokens=max_tokens
    )
    return response.choices[0].message["content"].strip()

def extract_pdf_text(pdf_path):
    pdf_document = fitz.open(pdf_path)
    pdf_text = ""
    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        pdf_text += page.get_text()
    return pdf_text

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parse.py input_pdf_file.pdf [max_tokens] [output_csv_file]")
        sys.exit(1)
    
    input_pdf_file = sys.argv[1]
    pdf_text = extract_pdf_text(input_pdf_file)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("API key not found in .env file.")
        sys.exit(1)
    
    openai.api_key = api_key

    output_csv_file = (
        "outputs/" + input_pdf_file.replace(".pdf", ".csv")
        if len(sys.argv) < 4
        else sys.argv[3]
    )

    output_directory = os.path.dirname(output_csv_file)
    os.makedirs(output_directory, exist_ok=True)

    prompt = read_prompt_from_file("prompt.txt")
    max_tokens = int(sys.argv[2]) if len(sys.argv) >= 3 else 100
    response = generate_response_from_pdf(prompt, pdf_text, max_tokens)

    with open(output_csv_file, "w") as f:
        # f.write('"Question Text","Question Type","Options"\n')
        f.write(f'{response}\n')

    print(f"Response saved in {output_csv_file}")
