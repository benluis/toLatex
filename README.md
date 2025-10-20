# Image to LaTeX Converter

A web application that converts images containing equations, formulas, or mathematical content into compilable LaTeX code using Google's Gemini API.

This project is designed to be deployed as a Docker container on AWS App Runner.

## Features

- Convert images (PNG, JPG, JPEG) to LaTeX
- Simple, user-friendly interface
- Copy LaTeX code to clipboard with one click

## Deployment (AWS App Runner)

1.  **Build and Push the Docker Image:**
    - Build the image: `docker build -t your-repo-name .`
    - Tag it for ECR: `docker tag your-repo-name:latest your-aws-account-id.dkr.ecr.your-region.amazonaws.com/your-repo-name:latest`
    - Push it to ECR: `docker push your-aws-account-id.dkr.ecr.your-region.amazonaws.com/your-repo-name:latest`

2.  **Configure App Runner:**
    - Create an App Runner service pointing to your ECR image repository.
    - Set the following environment variables in the service configuration:
        - `GOOGLE_API_KEY`: Your API key for the Gemini API.
        - `S3_BUCKET_NAME`: The name of your private S3 bucket for uploads.
    - Ensure the service's instance role has `s3:PutObject` permissions for the specified bucket.

## Local Development

1.  **Prerequisites:**
    - Python 3.9+
    - Docker Desktop

2.  **Setup:**
    - Create a `.env` file in the root directory:
      ```
      GOOGLE_API_KEY=your-gemini-api-key
      S3_BUCKET_NAME=your-local-test-bucket
      ```
    - Install dependencies: `pip install -r requirements.txt`

3.  **Run:**
    - Start the application: `uvicorn app.main:app --reload`
    - Open your browser to `http://localhost:8000`

## Project Structure

- `app/main.py`: FastAPI application entry point and API routes.
- `convertor.py`: Contains all the image processing and LaTeX conversion logic.
- `clients.py`: Initializes the AWS S3 client.
- `app/templates/`: Contains the `index.html` for the web interface.
- `Dockerfile`: Defines the container for deployment.
- `requirements.txt`: Lists the Python dependencies.

## Acknowledgements

- Google for the Gemini API
- FastAPI for the web framework
- OpenCV for image processing
