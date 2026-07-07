FROM python:3.12-slim 

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . . 

EXPOSE 8000

ENV DEBUG=False
ENV PORT=8000
ENV LOG_FILE=/logs/log.txt
ENV PYTHONUNBUFFERED=1


CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
