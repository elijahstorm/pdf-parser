import os
import sys
import fitz
import boto3
import openai
import shutil
import argparse
import pytesseract
from PIL import Image as PILImage
from wand.image import Image as WandImage
from wand.color import Color
from dotenv import load_dotenv


IMAGE_OUTPUT_DIR = "image_outputs/"
parser = argparse.ArgumentParser()
parser.add_argument("--text-only", type=str, help="Do not parse with image generation")
parser.add_argument(
    "--lang", type=str, default="eng", help="Language for OCR (default: eng)"
)
args, _ = parser.parse_known_args()
pytesseract.pytesseract.tesseract_cmd = r"/usr/local/Cellar/tesseract/5.3.2_1"


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
        model="gpt-3.5-turbo", messages=conversation, max_tokens=max_tokens
    )
    return response.choices[0].message["content"].strip()


def pdf_to_image(
    pdf_path, image_path, resolution=300, background_color="white", file_type=".jpg"
):
    os.makedirs(os.path.dirname(image_path), exist_ok=True)
    with WandImage(filename=pdf_path, resolution=resolution) as img:
        img.background_color = Color(background_color)
        img.alpha_channel = "remove"
        img.save(filename=f"{image_path}{file_type}")
        return (
            [f"{image_path}-{i}{file_type}" for i in range(len(img.sequence))]
            if len(img.sequence) > 1
            else [f"{image_path}{file_type}"]
        )


def extract_pdf_text(pdf_path):
    pdf_document = fitz.open(pdf_path)
    pdf_text = ""
    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        pdf_text += page.get_text()
    return pdf_text


def get_output_file(input_pdf_file):
    return (
        "outputs/" + input_pdf_file.replace(".pdf", ".csv")
        if len(sys.argv) < 4
        else sys.argv[3]
    )


def upload_temp_file(local_image_path, aws_access_key, aws_secret_key, bucket_name):
    s3 = boto3.client(
        "s3", aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key
    )

    image_key = os.path.basename(local_image_path)
    s3.upload_file(local_image_path, bucket_name, image_key)

    temp_url = s3.generate_presigned_url(
        "get_object", Params={"Bucket": bucket_name, "Key": image_key}, ExpiresIn=3600
    )

    def delete_uploaded_image():
        s3.delete_object(Bucket=bucket_name, Key=image_key)
        os.remove(local_image_path)

    return temp_url, delete_uploaded_image


def write_solution(output_csv_file, structured_text):
    output_directory = os.path.dirname(output_csv_file)
    os.makedirs(output_directory, exist_ok=True)

    with open(output_csv_file, "w") as f:
        f.write('"Question Text","Question Type","Options"\n')
        f.write(f"{structured_text}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: python parse.py input_pdf_file.pdf [max_tokens] [output_csv_file]"
        )
        sys.exit(1)

    api_key = os.getenv("OPENAI_API_KEY")
    aws_access_key = os.getenv("AWS_ACCESS_KEY")
    aws_secret_key = os.getenv("AWS_SECRET_KEY")
    bucket_name = os.getenv("BUCKET_NAME")

    if not api_key:
        print("OPENAI_API_KEY not found in .env file.")
        sys.exit(1)
    if not aws_access_key:
        print("AWS_ACCESS_KEY not found in .env file.")
        sys.exit(1)
    if not aws_secret_key:
        print("AWS_SECRET_KEY not found in .env file.")
        sys.exit(1)
    if not bucket_name:
        print("BUCKET_NAME not found in .env file.")
        sys.exit(1)

    input_pdf_file = sys.argv[1]
    prompt = read_prompt_from_file("prompt.txt")
    output_csv_file = get_output_file(input_pdf_file)
    max_tokens = int(sys.argv[2]) if len(sys.argv) >= 3 else 100
    structured_text = ""

    if args.text_only:
        openai.api_key = api_key
        pdf_text = extract_pdf_text(input_pdf_file)
        structured_text += generate_response_from_pdf(prompt, pdf_text, max_tokens)
    else:
        image_path = IMAGE_OUTPUT_DIR + input_pdf_file.replace(".pdf", "")
        saved_images = pdf_to_image(input_pdf_file, image_path)

        for i, saved_image in enumerate(saved_images):
            try:
                # s3_image, delete_image = upload_temp_file(
                #     saved_image, aws_access_key, aws_secret_key, bucket_name
                # )
                response = pytesseract.image_to_string(
                    PILImage.open(saved_image), lang=args.lang
                )
                structured_text += response
            except Exception as e:
                print(f"An error occurred while processing page {i + 1}: {e}")
            finally:
                # delete_image()
                os.remove(saved_image)

    shutil.rmtree(IMAGE_OUTPUT_DIR)
    write_solution(output_csv_file, structured_text)
    print(f"Response saved in {output_csv_file}")
