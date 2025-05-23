# Bioactive Peptides & Proteases Database

This is a Django-based web application designed to store, manage, and explore data on **bioactive peptides** and their
associated **proteases**. The goal of this project is to provide a robust and extensible platform for researchers and
developers working in the fields of biochemistry, pharmacology and bioinformatics.

## About this project

This project is a practical exercise to reinforce recently acquired knowledge in web development and deployment using
the following technologies:

* **Django:** (basic plan)  A Python web framework designed to enable rapid development of robust and scalable
  applications. It comes with built-in tools such as database management, user authentication, and API creation.
* **Docker:** (basic plan)  A platform for building, deploying, and running applications in lightweight, portable
  containers. It ensures your application runs consistently across different environments, eliminating compatibility
  issues.
* **PostgreSQL:**  (basic plan)  An advanced relational database management system. Reliable, flexible, and compatible
  with Django, it is ideal for storing and managing your application’s structured data.
*
* **Gunicorn:**(future plan) A WSGI server that acts as a bridge between web servers and your Django application in
  production. It handles requests efficiently and scales well, especially under high traffic.
* **Django REST Framework:** (future plan) A powerful and flexible toolkit for building Web APIs on top of Django,
  enabling easy creation of RESTful services.
* **Celery (optional/future):** An asynchronous task queue/job queue based on distributed message passing, useful for
  handling background tasks such as sending emails or processing data.
* **Nginx (optional/future):** A high-performance web server often used as a reverse proxy in front of Gunicorn to
  handle static files, load balancing, and SSL termination.

## Project Goals

- Build a clean and queryable **relational database** for bioactive peptides.
- Include detailed metadata: sequence, activity, source, references, etc.
- Model relationships with **proteases**.
- Provide a **user-friendly web interface** for search, filtering and data export.
- Support **API endpoints** for programmatic access and data integration.


## Tech Stack

- **Backend:** Django (Python)
- **Database:** PostgreSQL
- **Frontend:** Django templates
- **APIs:** Django REST Framework (planned)
- **Containerization:** Docker (for easy deployment and environment management)

