# 実行方法

```sh:a.sh
gcloud api-gateway api-configs create chatai --api=test --openapi-spec=api.yml --backend-auth-service-account=functions-api@radiant-voyage-325608.iam.gserviceaccount.com
gcloud services enable test-2twcr0xkt7vpo.apigateway.radiant-voyage-325608.cloud.goog
```
