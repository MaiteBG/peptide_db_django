FROM python:3.11-slim
ENV PROJECT_NAME=peptide_project

# Copy DB initialization script and make it executable
COPY init-db.sh /docker-entrypoint-initdb.d/init-db.sh
RUN chmod +x /docker-entrypoint-initdb.d/init-db.sh

# Install basic dependencies needed for building and running the app
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside container
WORKDIR /${PROJECT_NAME}/${PROJECT_NAME}

# Copy requirements and install
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose port 8000 for Django development server
EXPOSE 8000

# Default command commented out — use docker-compose command override for development
# CMD ["gunicorn", "peptide_project.wsgi:application"]
