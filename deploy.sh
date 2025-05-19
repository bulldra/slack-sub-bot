#!/usr/bin/env bash
set -e

# Load local environment variables when running manually
if [ -f ./.env ]; then
    # shellcheck disable=SC1091
    source ./.env
fi

# Deploy Cloud Function
DEPLOY_OUTPUT=$(gcloud -q functions deploy "${FUNCTION_NAME}" \
    --gen2 \
    --region=asia-northeast1 \
    --runtime=python311 \
    --trigger-topic="${TRIGGER_TOPIC}" \
    --timeout=120s \
    --min-instances=0 \
    --max-instances=30 \
    --memory=512Mi \
    --source=src/ \
    --entry-point=main \
    --service-account "${SERVICE_ACCOUNT}" \
    --set-secrets SECRETS="${SECRETS_MANAGER}" 2>&1) || DEPLOY_EXIT_CODE=$?

if [ "${DEPLOY_EXIT_CODE:-0}" -eq 0 ]; then
    echo "Deployment succeeded."
else
    ERROR_MESSAGE=$(echo "$DEPLOY_OUTPUT" | head -n 1)
    echo "Deployment failed for ${FUNCTION_NAME}."
    echo "Error: ${ERROR_MESSAGE}"
    exit 1
fi
date
