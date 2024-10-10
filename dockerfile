FROM python:3.12.5

WORKDIR /usr/src/app
COPY . .

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6 -y && pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
