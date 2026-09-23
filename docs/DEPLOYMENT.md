# Publish ScreenWeave on free services

## Deployment configuration

ScreenWeave uses Vercel and Render. Project URLs are in the root README. Local checks do not certify hosted performance; verify deployment status in the provider dashboards.

## 1. Accounts and source repository

Create accounts at https://github.com, https://render.com, and https://vercel.com.
Complete email verification and any provider identity checks yourself. Never
paste account passwords or access tokens into chat.

Create a GitHub repository named `screenweave`. Commit the application source,
dependency files, frontend package lock, and deployment configuration. Do not
upload `.venv`, `node_modules`, `.env` files, private screenshots, or build outputs.
Synthetic test fixtures are included under `tests/fixtures`; generated reports
and local screenshots are excluded from version control.

## 2. Render backend

Connect the repository and create a Blueprint using root `render.yaml`. Confirm
the compute plan is Free. It builds the Dockerfile inside `backend`, installs the
Linux OpenCV libraries and OCR dependencies, and launches one Uvicorn worker.
Set `ALLOWED_ORIGINS` to the eventual Vercel production origin. If the frontend
does not exist yet, create it first or update this value after receiving its URL.

Record the backend HTTPS URL. `/health` should return `status: ok`. Inspect build
and runtime logs before attempting inference. Do not upgrade to a paid instance
if the free service fails: measure the failure and revise the pipeline first.

## 3. Vercel frontend

Import the same repository. Root directory: `frontend`. Framework: Vite.
Build command: `npm run build`. Output directory: `dist`.
Set `VITE_API_URL` to the backend HTTPS URL before building. This is a public
frontend setting, not a secret. Redeploy after changing it.

Set Render's `ALLOWED_ORIGINS` to the exact Vercel origin without a trailing slash.
Do not use `*`. Preview deployment URLs need their own explicit authorization.

## 4. Hosted acceptance checks

- Open the public frontend with local development servers stopped.
- Upload a simple and a rounded-controls screenshot.
- Confirm preview, text/icon reconstruction, and editing work.
- Download all three ZIP formats and build the React export.
- Check invalid uploads, backend startup delay, and busy responses.
- Inspect memory/CPU and logs across repeated requests and maximum-size uploads.
- Verify the service stays within the free plan; local results are preliminary.

## Reference documentation

- https://render.com/docs/compute-plans
- https://render.com/docs/docker
- https://vercel.com/docs/frameworks/frontend/vite
