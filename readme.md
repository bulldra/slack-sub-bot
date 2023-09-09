## Secretを環境変数として利用

- Secret Manager を有効化
- Open AI API KEYを登録

```sh
gcloud functions deploy secret_access_as_env \
    --region asia-northeast1 \
    --runtime python37 \
    --trigger-http \
    --allow-unauthenticated \
    --service-account <secret-access-sample@cm-da-mikami-yuki-258308.iam.gserviceaccount.com> \
    --set-secrets MY_SECRET=projects/797147019523/secrets/my-secret-sample:latest
```
