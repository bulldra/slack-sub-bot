# 実行方法

## API 構成の作成

```sh
gcloud api-gateway api-configs create chatai --api=test --openapi-spec=api.yml --backend-auth-service-account=functions-api@radiant-voyage-325608.iam.gserviceaccount.com
```

## 作成した API 構成で Gateway を作成

## API の有効化

```sh
gcloud services enable test-2twcr0xkt7vpo.apigateway.radiant-voyage-325608.cloud.goog
```

## API キーの作成と保存

- [API とサービス](https://console.cloud.google.com/apis/dashboard?project=radiant-voyage-325608)
  - 認証情報
  - +認証情報を作成
  - API キー
- 取得したAPI キーを`.env`に格納

```env
x-api-key={APIキー}
```

- 作成した API キーの詳細を表示
  - 「API の制限」から作成した API のみを選択して保存

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
