# Use Python 3.11 as the base (matches your description)
FROM python:3.11-slim

# 1. Install System Dependencies (Tesseract for OCR)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Set up the working directory
WORKDIR /app

# 3. Create a non-root user (Hugging Face security requirement)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# 4. Copy requirements and install Python dependencies
COPY --chown=user requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# 5. Copy the rest of your backend code
# Note: We structure it so /app/main.py is at the root and /app/app contains the package
COPY --chown=user app /app/app
COPY --chown=user main.py /app/main.py

# 6. Expose the port Hugging Face expects (7860)
EXPOSE 7860

# 7. Start the FastAPI server
# We use main:app because main.py is in the root of WORKDIR
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
