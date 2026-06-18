# CI/CD Pipeline

The AI Trading Simulator features a robust Continuous Integration and Continuous Deployment (CI/CD) pipeline built using **GitHub Actions**. This ensures that every commit is tested, built, and ready for deployment without manual intervention.

## ⚙️ Workflow Breakdown

The pipeline is defined in `.github/workflows/ci.yml` and triggers automatically on pushes and pull requests to the `main` or `master` branches.

### 1. Backend Tests (Pytest)
This job spins up isolated, ephemeral PostgreSQL and Redis service containers directly inside the GitHub Actions runner.
- **Transactional Rollbacks**: Tests are wrapped in SQL transactions that are rolled back after every single test. This guarantees that no state leaks between tests (avoiding annoying 409 Conflict errors).
- **In-Memory Mocking**: We bypass expensive and network-dependent operations (like bcrypt hashing and yfinance HTTP calls) using `unittest.mock` and `hashlib`, reducing the test suite execution time to less than 1 second.
- **Result**: If any test fails, the entire pipeline halts, preventing broken code from reaching production.

### 2. Frontend Build (React + Vite)
This job sets up Node.js 20, installs dependencies via `npm ci` (ensuring deterministic installs from the package-lock), and runs the Vite build process.
- **Environment Injection**: It injects dummy `VITE_API_URL` and `VITE_WS_URL` variables to ensure the build succeeds in the isolated CI environment.
- **Artifacts**: The resulting static assets (`dist/`) are uploaded as a GitHub Actions artifact for inspection or manual deployment.

### 3. Docker Build & Push
Once the code is tested and compiled, this job packages the application into production-ready Docker containers.
- **Docker Buildx**: Utilizes Docker's advanced Buildx engine for layer caching, significantly speeding up subsequent builds.
- **GitHub Container Registry (GHCR)**: The images are tagged with the commit SHA and `latest`, then pushed securely to `ghcr.io`. 
- *Note: The pipeline automatically normalizes the repository name to lowercase to comply with Docker registry standards.*

### 4. Deploy to Render (Optional/Configurable)
The final step is automated deployment to Render.com.
- **Webhook Triggers**: The pipeline fires `curl` POST requests to Render Deploy Hooks.
- **Graceful Skipping**: If the `RENDER_BACKEND_DEPLOY_HOOK` or `RENDER_FRONTEND_DEPLOY_HOOK` secrets are not configured in your GitHub repository, this step gracefully skips without failing the pipeline.
- **Smoke Testing**: Once deployed, it pings the production `/health` endpoint to verify the deployment was successful.

## 🔐 Required Secrets
To fully utilize the deployment step, you must configure the following **Repository Secrets** in GitHub:
- `RENDER_BACKEND_DEPLOY_HOOK`: The unique deploy URL provided by Render for the backend web service.
- `RENDER_FRONTEND_DEPLOY_HOOK`: The unique deploy URL provided by Render for the frontend static site.
- `PRODUCTION_URL`: The base URL of your deployed backend (e.g., `https://api.mytradingapp.com`) used for smoke testing.
