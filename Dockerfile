FROM python:3.8

# Install AI models
RUN apt-get update && apt-get install -y tesseract-ocr
ENV TESSERACT_PATH /usr/bin/tesseract

# Modify Wand's policy.xml to allow PDF handling
RUN sed -i 's/rights="none" pattern="PDF"/rights="read|write" pattern="PDF"/g' /etc/ImageMagick-6/policy.xml

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY prompt.txt .
COPY run_tests.py .
COPY parse.py .
COPY .env .
COPY example_pdfs ./example_pdfs/

RUN chmod +x parse.py

CMD ["python", "run_tests.py", "example_pdfs"]
