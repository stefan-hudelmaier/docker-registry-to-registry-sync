FROM python:3.6.3-alpine3.6

WORKDIR /

COPY requirements.txt /
RUN pip install --no-cache-dir -r /requirements.txt

ADD docker-registry-to-registry-sync.py /docker-registry-to-registry-sync.py

CMD ["python", "docker-registry-to-registry-sync.py"]
