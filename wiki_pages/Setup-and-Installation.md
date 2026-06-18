# Setup and Installation

This guide will walk you through getting the AI Trading Simulator running on your local machine.

## 🐳 Option 1: Docker (Recommended)

Docker is the fastest and most reliable way to get the entire stack (PostgreSQL, Redis, Backend, Frontend) running seamlessly.

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
- Git.

### Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/Nidhish-0810/AI-Trading-Simulator.git
   cd AI-Trading-Simulator
   ```

2. **Environment Variables**
   The project includes a `.env.example` file. Copy it to `.env`:
   ```bash
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   ```
   *(The default values in the example files are already configured to work with Docker Compose.)*

3. **Start the Stack**
   ```bash
   docker compose up --build
   ```
   *This command will pull the necessary images, build the frontend and backend, run database migrations automatically, and start all services.*

4. **Access the Application**
   - **Frontend UI**: `http://localhost:5173`
   - **Backend API Docs (Swagger)**: `http://localhost:8000/docs`
   - **PostgreSQL**: `localhost:5432`
   - **Redis**: `localhost:6379`

---

## 💻 Option 2: Manual Local Setup

If you prefer to run the components natively (useful for heavy development), follow these steps.

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL server running locally.
- Redis server running locally.

### 1. Database Setup
Create a local PostgreSQL database named `tradeai`:
```sql
CREATE DATABASE tradeai;
CREATE USER tradeai_user WITH ENCRYPTED PASSWORD 'tradeai_pass';
GRANT ALL PRIVILEGES ON DATABASE tradeai TO tradeai_user;
```

### 2. Backend Setup
Navigate to the backend directory and set up a Python virtual environment:
```bash
cd backend
python -m venv venv

# Activate venv (Windows)
venv\Scripts\activate
# Activate venv (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Update your `backend/.env` file with your local database credentials:
```env
DATABASE_URL=postgresql+asyncpg://tradeai_user:tradeai_pass@localhost:5432/tradeai
REDIS_URL=redis://localhost:6379/0
```

Run Alembic migrations to create the tables:
```bash
alembic upgrade head
```

Start the FastAPI server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup
Open a new terminal window and navigate to the frontend directory:
```bash
cd frontend

# Install Node modules
npm install

# Start the Vite development server
npm run dev
```

Navigate to `http://localhost:5173` to see the app!
