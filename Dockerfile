FROM python:3.12
WORKDIR /app

COPY requirements.txt run.sh poweroff_detector.session run.sh ./
COPY src ./src

RUN chmod +x run.sh

RUN pip install -r requirements.txt
RUN apt update && apt install -y tesseract-ocr libtesseract-dev
RUN wget https://github.com/tesseract-ocr/tessdata/raw/main/ukr.traineddata
RUN mv ukr.traineddata /usr/share/tesseract-ocr/5/tessdata/

CMD ["./run.sh"]