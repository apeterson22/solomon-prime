FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    RDE_REFLEX_HOST=0.0.0.0 \
    RDE_REFLEX_PORT=8787

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

USER 65532:65532
EXPOSE 8787
CMD ["python", "-m", "rde_reflex"]
