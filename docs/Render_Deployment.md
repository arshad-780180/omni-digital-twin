# Deploying OMNI Backend to Render

This document explains how to deploy the FastAPI backend of the OMNI Digital Twin to [Render.com](https://render.com).

## Prerequisites

1. **GitHub Account**: Your codebase must be pushed to a GitHub repository.
2. **MongoDB Atlas**: You need an active MongoDB Atlas cluster. Ensure your cluster network access allows connections from `0.0.0.0/0` (since Render IP addresses are dynamic).
3. **Render Account**: A Render account linked to your GitHub.

## Deployment Method 1: Infrastructure as Code (Recommended)

We have provided a `render.yaml` file in the root of the repository. This allows for a one-click setup.

1. Go to your Render Dashboard.
2. Click **New +** and select **Blueprint**.
3. Connect your GitHub repository.
4. Render will automatically detect the `render.yaml` file and prompt you to create the `omni-backend` service.
5. You will be prompted to enter the missing environment variables (e.g., `MONGODB_URL`, `GEMINI_API_KEY`, `CORS_ORIGINS`). 
6. Click **Apply** to deploy.

## Deployment Method 2: Manual Setup

If you prefer to set up the service manually via the Render dashboard:

1. Click **New +** and select **Web Service**.
2. Connect your GitHub repository.
3. Configure the service:
   * **Name**: `omni-backend`
   * **Language**: `Docker`
   * **Branch**: `main`
   * **Root Directory**: `backend` (or leave blank if you want Render to use the root, but ensure the Dockerfile path is `backend/Dockerfile`)
   * **Instance Type**: Free (or higher depending on your needs)
4. Add the following **Environment Variables**:
   * `PORT`: `8000` (Render will override this, but it's good practice)
   * `MONGODB_URL`: Your MongoDB Atlas connection string (e.g., `mongodb+srv://<user>:<password>@cluster0.../?retryWrites=true&w=majority`)
   * `DATABASE_NAME`: `omnimind_db`
   * `JWT_SECRET_KEY`: Generate a secure random string for JWT signing.
   * `GEMINI_API_KEY`: Your Google Gemini API Key.
   * `CORS_ORIGINS`: A comma-separated list of allowed frontend origins (e.g., `https://your-frontend.vercel.app`).
5. Click **Create Web Service**.

## Verification & Health Check

* The Dockerfile includes a health check at `/health`. Render will automatically wait for this endpoint to return `200 OK` before marking the deployment as successful.
* Once deployed, your backend URL will look like: `https://omni-backend.onrender.com`.
* You can test it by appending `/docs` to view the Swagger UI.

## Troubleshooting

1. **MongoDB Connection Fails**: Ensure you have whitelisted `0.0.0.0/0` in MongoDB Atlas Network Access. Render does not provide static outbound IPs on the free tier.
2. **CORS Errors**: Ensure your `CORS_ORIGINS` environment variable exactly matches your frontend deployment URL (no trailing slash).
3. **Uploads (Resumes, etc.)**: Note that the Render free tier has an ephemeral file system. Any PDF uploads stored in `/app/uploads` will be lost when the server restarts or deploys. In this version, uploads are processed in memory or immediately parsed, so long-term storage is not strictly required. For permanent storage, consider attaching a Render Persistent Disk (requires paid tier) or integrating AWS S3.
