# OMNI Digital Twin - Backend

This is the FastAPI backend for the OMNI Digital Twin application.

## Running with Docker

You can run the backend completely containerized using Docker.

### 1. Build the Docker Image

Make sure you are in the `backend` directory, then run:

```bash
docker build -t omni-backend:latest .
```

### 2. Run the Docker Container

The backend requires environment variables to function properly (e.g., MongoDB URL, JWT secret). You should define these in a `.env` file (see `.env.example` if available) or pass them directly.

Run the container, exposing port 8000:

```bash
docker run -d \
  -p 8000:8000 \
  --name omni-backend \
  --env-file .env \
  omni-backend:latest
```

The API will now be accessible at `http://localhost:8000`. You can visit `http://localhost:8000/docs` to see the interactive API documentation.

## MongoDB Atlas Configuration

For production or cloud deployment, OMNI Digital Twin uses MongoDB Atlas. The backend connects directly to Atlas using an environment variable without any localhost fallbacks.

To configure Atlas:
1. Create a cluster on [MongoDB Atlas](https://www.mongodb.com/cloud/atlas).
2. Create a database user and whitelist your application's IP address (or `0.0.0.0/0` if deploying to a dynamic IP environment).
3. Obtain your connection string. It will look like this:
   `mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority`
4. In your `.env` file or deployment environment settings, set `MONGODB_URL`:
   ```
   MONGODB_URL=mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority
   ```
5. Ensure the database name is configured via `DATABASE_NAME` if you are not using the default `omnimind_db`.
