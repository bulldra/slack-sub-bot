source ./.env

gcloud functions deploy ${FUNCTION_NAME} \
	--gen2 \
	--region=asia-northeast1 \
	--runtime=python311 \
	--trigger-topic=${TRIGGER_TOPIC} \
	--timeout=120s \
	--min-instances=0 \
	--max-instances=20 \
	--memory=512Mi \
	--source=src/ \
	--entry-point=main \
	--service-account ${SERVICE_ACCOUNT} \
	--set-secrets SECRETS=${SECRETS_MANAGER}
