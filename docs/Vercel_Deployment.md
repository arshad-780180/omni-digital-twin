# Deploying OMNI Frontend to Vercel

This document explains how to deploy the React (Vite) frontend of the OMNI Digital Twin to [Vercel](https://vercel.com).

## Prerequisites

1. **GitHub Account**: Your codebase must be pushed to a GitHub repository.
2. **Render Backend**: Ensure your FastAPI backend is deployed and you have the live API URL (e.g., `https://omni-backend-xxxx.onrender.com`).
3. **Vercel Account**: A Vercel account linked to your GitHub.

## SPA Routing Configuration

We have added a `vercel.json` file in the `frontend/` directory to configure Vercel for Single-Page Application (SPA) routing. This ensures that when users visit nested routes (like `/dashboard`), Vercel correctly serves `index.html` instead of returning a 404 error.

```json
{
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

## Deployment Steps

1. Go to your [Vercel Dashboard](https://vercel.com/dashboard).
2. Click **Add New...** > **Project**.
3. Import your GitHub repository for OMNI Digital Twin.
4. **Configure the Project**:
   - **Framework Preset**: Vercel should automatically detect `Vite`.
   - **Root Directory**: Click "Edit" and select `frontend`.
5. **Environment Variables**:
   - Expand the "Environment Variables" section.
   - Add a new variable:
     - **Name**: `VITE_API_URL`
     - **Value**: `https://omni-backend-5d3i.onrender.com/api` (Replace with your actual backend URL, ensuring `/api` is at the end).
6. Click **Deploy**.

## Verification

Once the deployment completes, Vercel will provide you with a live `.vercel.app` domain. 
To verify the deployment works end-to-end:
1. Open the Vercel app URL in your browser.
2. Register a new account or log in to verify the auth flow communicates with the backend.
3. Upload a Resume to verify binary file streams and MongoDB Atlas parsing.
4. Trigger the GitHub Analysis and wait for the AI summaries to load.
5. Check the Career Dashboard. 

## Updating the CORS Configuration

**CRITICAL**: Once Vercel gives you your live URL (e.g., `https://omni-frontend-xyz.vercel.app`), you MUST go back to your **Render Backend** settings and update the `CORS_ORIGINS` environment variable to include this exact Vercel URL (with no trailing slash). 
If you skip this step, all API requests from the frontend will be blocked by CORS policy.
