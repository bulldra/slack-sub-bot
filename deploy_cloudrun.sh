#!/usr/bin/env bash
set -e

if [ -f ./.env ]; then
    # shellcheck disable=SC1091
    source ./.env
fi

IMAGE_NAME="gcr.io/${GCP_PROJECT_ID}/${SERVICE_NAME}"

gcloud builds submit --tag "$IMAGE_NAME" .

gcloud run deploy "$SERVICE_NAME" \
    --image "$IMAGE_NAME" \
    --region=asia-northeast1 \
    --platform=managed \
    --min-instances=0 \
    --max-instances=30 \
    --memory=512Mi \
    --service-account "$SERVICE_ACCOUNT" \
    --set-secrets SECRETS="$SECRETS_MANAGER" \
    --quiet

date
