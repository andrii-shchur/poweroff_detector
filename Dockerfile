FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt run.sh poweroff_detector.session run.sh ./
COPY src ./src
RUN pip install -r requirements.txt

RUN apt update && apt install -y tesseract-ocr libtesseract-dev

CMD ["./run.sh"]