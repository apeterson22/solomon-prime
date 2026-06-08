FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY extensions/memory-snn-lnn/model/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy model code
COPY extensions/memory-snn-lnn/model/ /app/

EXPOSE 5001

ENV PYTHONUNBUFFERED=1

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:5001/health')" || exit 1

CMD ["python3", "server.py"]
