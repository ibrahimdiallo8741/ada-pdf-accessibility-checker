#!/usr/bin/env fish

gcloud config set project ada-compliance-checker-511904

gcloud run deploy ada-compliance-checker \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 2