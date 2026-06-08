# Use an official lightweight Python image.
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the main application file
COPY main.py .

# Expose the port the app runs on
EXPOSE 8080

# Define the command to run the application
CMD ["python", "main.py"]
