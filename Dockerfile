FROM python:3.11-slim
ENV PROJECT_NAME=peptide_project


# Instala dependencias básicas
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gettext \
    && rm -rf /var/lib/apt/lists/*

# Configura directorio de trabajo
WORKDIR /${PROJECT_NAME}

# Copia requirements (si tienes)
COPY requirements.txt .

# Instala dependencias Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copia el resto de la app
COPY . .

# Expone el puerto para Django
EXPOSE 8000

# Comando por defecto para el contenedor web (lo puedes sobreescribir en docker-compose)
CMD ["sh", "-c", "python ${PROJECT_NAME}/manage.py runserver 0.0.0.0:8000"]

