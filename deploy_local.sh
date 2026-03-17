source ./.env

uv pip compile pyproject.toml -o src/requirements.txt
CLOUDSDK_PYTHON=/opt/homebrew/bin/python3.11
gcloud -q components update

# Update Secret Manager only if secrets.json differs from current version
SECRET_RESOURCE="${SECRETS_MANAGER%%:*}"
SECRET_NAME="${SECRET_RESOURCE##*/}"
if [ -f secrets.json ]; then
	REMOTE_SECRET=$(gcloud secrets versions access latest --secret="${SECRET_NAME}" 2>/dev/null || echo "")
	LOCAL_SECRET=$(cat secrets.json)
	if [ "${REMOTE_SECRET}" != "${LOCAL_SECRET}" ]; then
		echo "Secret '${SECRET_NAME}' has changed. Uploading new version..."
		gcloud secrets versions add "${SECRET_NAME}" --data-file=secrets.json
	else
		echo "Secret '${SECRET_NAME}' is up to date. Skipping upload."
	fi
	# 最新バージョン以外を削除（コスト削減）
	OLD_VERSIONS=$(gcloud secrets versions list "${SECRET_NAME}" --filter="state=enabled" --format="value(name)" | sort -n | awk 'NR>1{print prev} {prev=$0}')
	if [ -n "${OLD_VERSIONS}" ]; then
		echo "Destroying old secret versions: ${OLD_VERSIONS}"
		echo "${OLD_VERSIONS}" | xargs -I{} gcloud secrets versions destroy {} --secret="${SECRET_NAME}" --quiet
	fi
fi

DEPLOY_OUTPUT=$(gcloud -q functions deploy ${FUNCTION_NAME} \
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
	--set-secrets SECRETS=${SECRETS_MANAGER} 2>&1)

if [ $? -eq 0 ]; then
	osascript -e "display notification \"Deployment succeeded.\" with title \"Visual Studio Code\" subtitle \"✅ Cloud Function ${FUNCTION_NAME} deployment.\" sound name \"Bell\""
else
	ERROR_MESSAGE=$(echo "$DEPLOY_OUTPUT" | head -n 1 )
	osascript -e "display notification \"Deployment failed: ${ERROR_MESSAGE}\" with title \"Visual Studio Code\" subtitle \"❌ Cloud Function ${FUNCTION_NAME} deployment.\" sound name \"Basso\""
	echo "Deployment failed for ${FUNCTION_NAME}."
	echo "Error: ${ERROR_MESSAGE}"
fi
date
