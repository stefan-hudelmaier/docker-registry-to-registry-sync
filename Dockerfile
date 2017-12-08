FROM python:3.6.3-alpine3.6

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ADD docker-registry-to-registry-sync.py /usr/src/app/docker-registry-to-registry-sync.py

CMD ["python", "./docker-registry-to-registry-sync.py"]
