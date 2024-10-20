source ./.env

poetry update
poetry export -f requirements.txt -o src/requirements.txt --without-hashes
gcloud components update
gcloud functions deploy ${FUNCTION_NAME} \
	--gen2 \
	--region=asia-northeast1 \
	--runtime=python312 \
	--trigger-topic=${TRIGGER_TOPIC} \
	--timeout=120s \
	--min-instances=0 \
	--max-instances=30 \
	--memory=512Mi \
	--source=src/ \
	--entry-point=main \
	--service-account ${SERVICE_ACCOUNT} \
	--set-secrets SECRETS=${SECRETS_MANAGER}
