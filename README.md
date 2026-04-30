Finance API

A production-ready personal finance management REST API built with **Django** and **Django REST Framework**. 
Supports budgeting, transaction tracking, real-time notifications, financial reports.




Features

-  **JWT Authentication** — Secure token-based auth with refresh support
-  **User Management** — Registration, login, profile management
-  **Accounts** — Multiple financial accounts per user (bank, cash, wallet, etc.)
-  **Transactions** — Full CRUD with filtering, search, and pagination
-  **Categories** — Customizable income and expense categories
-  **Budgets** — Set and track spending limits by category and period
-  **Notifications** — Real-time alerts via WebSockets (budget limits, anomalies)
-  **Reports** — Export financial reports as PDF, CSV, or Excel
-  **Stripe Payments** — Integrated payment processing
-  **AWS S3 Storage** — Cloud file uploads and storage
-  **Celery Task Queue** — Async background jobs and scheduled tasks
-  **Swagger Docs** — Auto-generated interactive API documentation



Tech Stack

| Layer | Technology |
|---|---|
| **Framework** | Django 5.0.4, Django REST Framework 3.15.1 |
| **Database** | PostgreSQL (psycopg2) |
| **Authentication** | JWT via `djangorestframework-simplejwt` |
| **Cache / Broker** | Redis |
| **Task Queue** | Celery 5.4, django-celery-beat, django-celery-results |
| **API Docs** | drf-spectacular (OpenAPI / Swagger) |
| **Containerization** | Docker, Docker Compose |
| **Config** | python-decouple |

> No need to install Python, PostgreSQL, or Redis locally — Docker handles everything.

---

### Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/Vinnie-8/finance_api.git
   cd finance_api
   ```

2. **Create your environment file:**

   ```bash
   cp .env.example .env
   ```

3. **Fill in your environment variables** (see section below)

4. **Build and start all services:**

   ```bash
   docker compose up --build
   ```

5. **Run database migrations:**

   ```bash
   docker compose exec web python manage.py migrate
   ```

6. **Create a superuser (admin):**

   ```bash
   docker compose exec web python manage.py createsuperuser
   ```

7. **The API is now running at:** `http://localhost:8000`

---

### Environment Variables

Create a `.env` file in the project root. Here is the full list of required variables:

```env
# Django
SECRET_KEY=your_secret_key_here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (PostgreSQL)
DB_NAME=finance_db
DB_USER=finance_user
DB_PASSWORD=your_db_password
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# JWT
JWT_ACCESS_TOKEN_LIFETIME=60        # minutes
JWT_REFRESH_TOKEN_LIFETIME=7        # days

```

Never commit your `.env` file. It is included in `.gitignore` by default.


  API Modules

### 🔐 Authentication — `/api/auth/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | Register a new user |
| POST | `/api/auth/login/` | Login and receive JWT tokens |
| POST | `/api/auth/token/refresh/` | Refresh access token |
| POST | `/api/auth/logout/` | Logout / blacklist token |
| POST | `/api/auth/password/change/` | Change password |

---

### 👤 Users — `/api/users/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/users/me/` | Get current user profile |
| PUT | `/api/users/me/` | Update user profile |
| PATCH | `/api/users/me/` | Partially update profile |
| DELETE | `/api/users/me/` | Delete account |

---

### 🏦 Accounts — `/api/accounts/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/accounts/` | List all user accounts |
| POST | `/api/accounts/` | Create a new account |
| GET | `/api/accounts/{id}/` | Get account details |
| PUT | `/api/accounts/{id}/` | Update account |
| DELETE | `/api/accounts/{id}/` | Delete account |
| GET | `/api/accounts/{id}/balance/` | Get current balance |

---

### 🗂️ Categories — `/api/categories/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/categories/` | List all categories |
| POST | `/api/categories/` | Create a custom category |
| GET | `/api/categories/{id}/` | Get category detail |
| PUT | `/api/categories/{id}/` | Update category |
| DELETE | `/api/categories/{id}/` | Delete category |

---

### 💸 Transactions — `/api/transactions/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/transactions/` | List transactions (filterable) |
| POST | `/api/transactions/` | Create a transaction |
| GET | `/api/transactions/{id}/` | Get transaction detail |
| PUT | `/api/transactions/{id}/` | Update transaction |
| DELETE | `/api/transactions/{id}/` | Delete transaction |
| GET | `/api/transactions/summary/` | Get income vs expense summary |

> Supports filtering by: `account`, `category`, `type` (income/expense), `date_from`, `date_to`, `amount_min`, `amount_max`

---

### 📊 Budgets — `/api/budgets/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/budgets/` | List all budgets |
| POST | `/api/budgets/` | Create a budget |
| GET | `/api/budgets/{id}/` | Get budget detail with progress |
| PUT | `/api/budgets/{id}/` | Update budget |
| DELETE | `/api/budgets/{id}/` | Delete budget |

## 📖 API Documentation

Interactive API docs are auto-generated . Once the server is running, visit:


| Swagger UI | `http://localhost:8000/api/docs/` |



## 🐳 Running with Docker

The project uses **Docker Compose** to orchestrate all services.

### Services



