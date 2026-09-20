FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
# The OCR package depends on opencv-python, which needs these Linux libraries.
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 fonts-liberation && rm -rf /var/lib/apt/lists/*
COPY requirements.txt requirements-ocr.txt ./
RUN pip install -r requirements-ocr.txt
COPY app ./app
COPY reconstruct.py react_export.py ./
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
