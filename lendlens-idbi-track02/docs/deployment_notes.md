# Deployment Notes

This prototype is designed to run locally with zero cloud dependencies, which is the intended and simplest way to demonstrate it.

The core of the project is the `python run_all.py` script, which is a batch process. It generates all necessary data artifacts and ML models and places them in the `data/processed` directory. The API server and dashboard are lightweight consumers of these pre-computed files.

If you choose to host the application, here is the recommended approach.

---

### Hosting Strategy

The application consists of two main components to deploy:
1.  A **backend API** (FastAPI) that serves the `leads.json` file.
2.  A **frontend dashboard** (React/Vite) which is a static single-page application.

These should be deployed as separate services.

### 1. Backend API (FastAPI) Deployment

The key consideration for the API is ensuring the `data/processed/leads.json` file is available to it at runtime.

-   **Build Step:** The `python run_all.py` command **must** be executed at build time on the deployment server. This will create the `leads.json` artifact that the API serves. Alternatively, you can run the script locally and bake the `data/processed/` directory directly into your container image or deployment package.
-   **Recommended Services:**
    -   **PaaS (Platform-as-a-Service):** Services like **Render** or **Railway** are ideal. You can configure a Python environment, specify `pip install -r requirements.txt` as the build command, and `uvicorn api.main:app --host 0.0.0.0 --port $PORT` as the start command. You would add `python run_all.py` as a step before the `uvicorn` command.
    -   **Container Services:** For more control, you can use **AWS App Runner** or **AWS ECS Fargate**. You would provide a `Dockerfile` that copies the repository, runs `pip install` and `python run_all.py`, and then sets the `CMD` to run `uvicorn`.
-   **Start Command:**
    ```bash
    uvicorn api.main:app --host 0.0.0.0 --port $PORT
    ```
    -   `--host 0.0.0.0` is critical to bind to the network interface provided by the hosting environment.
    -   The `$PORT` environment variable is typically set automatically by the PaaS provider.

### 2. Frontend Dashboard (React/Vite) Deployment

The dashboard is a standard static website.

-   **Build Step:** The command `npm run build` (executed within the `dashboard/` directory) will compile the React application and all its assets into the `dashboard/dist/` directory.
-   **Environment Variable:** You must set the `VITE_API_URL` environment variable during the build process. This tells the frontend where to find the deployed backend API.
    ```bash
    # Example for Vercel/Netlify build settings
    VITE_API_URL=https://your-deployed-api-url.com npm run build
    ```
-   **Recommended Services:**
    -   **Static Hosting:** Services like **Vercel** and **Netlify** are perfect for this. Connect your Git repository, set the build command to `npm run build` (with the base directory as `dashboard/`), and specify the output directory as `dashboard/dist`.
    -   **Cloud Storage:** A traditional approach is to use **AWS S3** for hosting combined with **AWS CloudFront** as a CDN for low-latency global access. You would upload the contents of the `dashboard/dist/` directory to your S3 bucket.

### 3. CORS (Cross-Origin Resource Sharing)

For the demo, the FastAPI application is configured in `api/main.py` to allow requests from any origin (`allow_origins=["*"]`).

**This is not secure for a production environment.**

Before any real deployment, you must lock this down to only allow requests from your deployed frontend dashboard's URL.

```python
# In api/main.py, change this:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Insecure for production
    ...
)

# To this:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-dashboard-domain.vercel.app"], # Example
    ...
)
```
