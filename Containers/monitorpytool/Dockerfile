# Use the official Python image as the base image
FROM python:3.8

# Set the working directory inside the container
WORKDIR /app

# Copy the necessary files into the container
COPY monitor_tool.py /app/
COPY templates /app/templates

# Install dependencies
RUN pip install Flask pymongo apscheduler matplotlib

# Expose the port that Flask will run on
EXPOSE 5000

# Set the environment variable for Flask to run in development mode
ENV FLASK_APP=monitor_tool.py
ENV FLASK_RUN_HOST=0.0.0.0

# Command to run the Flask application
CMD ["flask", "run"]
