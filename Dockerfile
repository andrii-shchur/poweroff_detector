FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt detection.py const.py img.png ./
RUN pip install -r requirements.txt

RUN apt update && apt install -y tesseract-ocr libtesseract-dev

# TODO expose the whole thing via telegram bot or webserver
CMD ["python", "detection.py"]