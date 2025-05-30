FROM python:3.12-slim

WORKDIR /app

COPY src/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ .

ENV PORT=8080

CMD ["functions-framework", "--target", "main", "--signature-type", "cloudevent"]
