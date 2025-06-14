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
* **Gunicorn:**(future plan) A WSGI server that acts as a bridge between web servers and your Django application in
  production. It handles requests efficiently and scales well, especially under high traffic.
* **Django REST Framework:** (future plan) A powerful and flexible toolkit for building Web APIs on top of Django,
  enabling easy creation of RESTful services.
* **Celery (optional/future):** An asynchronous task queue/job queue based on distributed message passing, useful for
  handling background tasks such as sending emails or processing data.
* **Nginx (optional/future):** A high-performance web server often used as a reverse proxy in front of Gunicorn to
  handle static files, load balancing, and SSL termination.

### 🧠 Learning Goals

This project is not only a technical implementation but also a personal learning exercise. The main objectives include:

* Practicing collaborative workflows using **pull requests**.
* Applying the **[Conventional Commits](https://www.conventionalcommits.org/)** specification to maintain a clean and
  structured commit history.
* Using **pytest** to write and run automated tests, fostering test-driven development and ensuring code reliability.
* Improving discipline in version control and aligning with real-world software development practices.

I’m open to feedback and suggestions — what else would you recommend to help me grow toward professional-level
development?

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

## 📫 Contact

For questions, ideas or collaboration proposals, contact:<br>

* **[Maite Bernaus Gimeno]** – [[maite.bernaus@gmail..com]()] <br>
* GitHub: [@MaiteBG](https://github.com/MaiteBG)

___

## 📅 Project Progress Overview

## 14/06/2025

## 📚 Learning Features

- Set up a professional development environment with:
  - Docker and `docker-compose`
  - `.env` environment variables
  - Automated DB initialization scripts (`init-db.sh` / `.ps1`)
- Modular Django architecture with multiple apps
- Custom logging system with `logger_base.py`
- API integration with UniProt via service layer
- Clean design patterns in services, views, and templates
- Dynamic filter handling with **HTMX**
- Separation of views to manage hierarchical taxonomy filters
- Custom Django `template tags` for reusability and clarity

### *JavaScript* Concepts

- **DOM manipulation (indirect)**: Understanding how elements are updated and targeted in the DOM using `hx-target`,
  `hx-swap`, etc.
- **AJAX basics**: HTMX abstracts away XMLHttpRequest or `fetch`, but familiarity with HTTP verbs and async updates is
  necessary.
- **Pagination logic**: Implementing server-side pagination with dynamic frontend updates using HTMX links or buttons
  helps understand:
  - How pagination works behind the scenes (e.g. updating a portion of the page without full reload)
  - Request-response patterns for paginated data
  - Replacing or appending content dynamically with `hx-swap`
- **Progressive enhancement**: Ensuring the app remains functional with server-rendered HTML while providing dynamic
  updates.
- **Event handling**: Implicit understanding of user-triggered events like `click`, `change`, `submit`, which HTMX binds
  to automatically.
- **Component thinking**: Designing views and templates as reusable components similar to frontend JS frameworks.
- **Debugging tools**: Using browser dev tools (Network/Console) to inspect request/response cycles triggered by HTMX.
- **Client-server lifecycle**: Understanding how partial updates from Django views replace or augment content without a
  full page reload.

## App Features

### Backend

- Data models with clear relations between Organism, Protein, Reference, and external databases
- Management of cross-references with UniProt
- Logic to extract and associate gene names and synonyms
- Integrated logging system using a `UserActionLog` model
- Multi-database setup support (different type of users)

### Frontend

- **Bootstrap** integrated for UI styling and layout
- Sidebar with dynamic organism filters using HTMX
- Paginated and searchable protein list view
- Expandable sections for long texts like protein functions or reference lists ("Show more" toggle)
- Fully functional organism dropdowns with hierarchical taxonomy logic
- Improved main page layout (layout, dropdowns, sidebar)
- Taxonomy filter supporting hierarchical structure (parent-child taxons)


