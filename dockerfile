FROM python:3.9-slim

# Set work directory
WORKDIR /app

# Copy the requirements and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the entire app into the container
COPY . .

# Run the tests
CMD ["python", "-m", "unittest", "discover", 'tests']
