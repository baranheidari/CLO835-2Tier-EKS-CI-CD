FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

# Install the Python dependencies (efficiently uses Docker caching)
# We use --no-cache-dir to keep the image small
# - r indicates the requirements file
RUN pip install --no-cache-dir -r requirements.txt

# Copy . (current directory) to /app in the container
COPY . /app

EXPOSE 81

CMD ["python", "app.py"]