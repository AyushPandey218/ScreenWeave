FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
# The OCR package depends on opencv-python, which needs these Linux libraries.
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 fonts-liberation && rm -rf /var/lib/apt/lists/*
COPY requirements.txt requirements-ocr.txt ./
RUN pip install -r requirements-ocr.txt
COPY app ./app
COPY reconstruct.py react_export.py tailwind_export.py ./
# Fail the image build if any export dependency is missing.
RUN python -c "from app.main import package_layout; result = package_layout({'version': 1, 'viewport': {'width': 1, 'height': 1}, 'background': '#ffffff', 'elements': [], 'limitations': []}); assert set(result['exports']) == {'html', 'react', 'tailwind'}"
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
