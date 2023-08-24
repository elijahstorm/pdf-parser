import sys
import openai
import fitz
from dotenv import load_dotenv
import os
import csv

load_dotenv()

def generate_response_from_pdf(pdf_text, max_tokens):
    prompt = f"Given the following PDF content:\n{pdf_text}\nGenerate a response in the desired format."
    response = openai.Completion.create(
        engine="davinci",
        prompt=prompt,
        max_tokens=max_tokens
    )
    return response.choices[0].text.strip()

def extract_pdf_text(pdf_path):
    pdf_document = fitz.open(pdf_path)
    pdf_text = ""
    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        pdf_text += page.get_text()
    return pdf_text

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py input_pdf_file.pdf [output_csv_file] [max_tokens]")
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
        if len(sys.argv) < 3
        else sys.argv[2]
    )

    max_tokens = int(sys.argv[3]) if len(sys.argv) >= 4 else 100
    response = generate_response_from_pdf(pdf_text, max_tokens)

    with open(output_csv_file, "w", newline="") as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(["PDF File", "Max Tokens", "Response"])
        csvwriter.writerow([input_pdf_file, max_tokens, response])

    print(f"Response saved in {output_csv_file}")
