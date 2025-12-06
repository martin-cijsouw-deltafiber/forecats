FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY forecats/ ./forecats/

RUN pip install --no-cache-dir .

RUN mkdir -p data logs static/images

# Expose port
EXPOSE 8000

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Start application
CMD ["uvicorn", "forecats.main:app", "--host", "0.0.0.0", "--port", "8000"]
