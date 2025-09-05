# Wood eBay App - Cloud Run デプロイメントガイド

## 前提条件

1. Google Cloud Project が作成済み
2. Cloud Build API と Cloud Run API が有効化済み
3. 必要な権限（Cloud Build Service Account、Cloud Run Admin）

## 1. Secret Manager での機密情報設定

```bash
# eBay API認証情報をSecret Managerに保存
gcloud secrets create ebay-app-id --data-file=- <<< "YOUR_EBAY_APP_ID"
gcloud secrets create ebay-cert-id --data-file=- <<< "YOUR_EBAY_CERT_ID"  
gcloud secrets create ebay-ru-name --data-file=- <<< "YOUR_REDIRECT_URI"
gcloud secrets create flask-secret-key --data-file=- <<< "YOUR_SECRET_KEY"

# Cloud Build Service Accountに権限付与
PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)")
gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
    --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

## 2. Cloud Build トリガー設定

```bash
# GitHubリポジトリと連携してトリガー作成
gcloud builds triggers create github \
    --repo-name=wood \
    --repo-owner=Staninbui \
    --branch-pattern="^master$" \
    --build-config=cloudbuild.yaml \
    --name=wood-ebay-app-trigger
```

## 3. 手動デプロイ（初回）

```bash
# Cloud Buildを手動実行
gcloud builds submit --config=cloudbuild.yaml .
```

## 4. Cloud Run設定の確認

デプロイ後、以下の設定を確認：

- **メモリ**: 2GB（XML処理のため）
- **CPU**: 2（並列処理対応）
- **同時実行数**: 100
- **最大インスタンス数**: 10
- **タイムアウト**: 300秒
- **最小インスタンス数**: 0（コスト最適化）

## 5. パフォーマンス監視

Cloud Runコンソールで以下を監視：

- レスポンス時間
- エラー率
- CPU使用率
- メモリ使用率
- インスタンス数

## 6. ログ監視

```bash
# リアルタイムログ確認
gcloud logs tail "projects/$(gcloud config get-value project)/logs/run.googleapis.com%2Fstdout"

# エラーログ確認
gcloud logs read "projects/$(gcloud config get-value project)/logs/run.googleapis.com%2Fstderr" --limit=50
```

## 7. トラブルシューティング

### よくある問題

1. **メモリ不足**: インスタンスメモリを4GBに増加
2. **タイムアウト**: TASK_TIMEOUTを600秒に延長
3. **同時実行制限**: MAX_WORKERSを調整

### デバッグコマンド

```bash
# サービス詳細確認
gcloud run services describe wood-ebay-app --region=asia-northeast1

# 最新リビジョンのログ
gcloud run revisions list --service=wood-ebay-app --region=asia-northeast1
```

## 8. セキュリティ考慮事項

- 非rootユーザーでコンテナ実行
- Secret Managerで機密情報管理
- HTTPS強制
- セッションセキュリティ設定済み

## 9. コスト最適化

- 最小インスタンス数: 0（アイドル時のコスト削減）
- CPU割り当て: リクエスト処理時のみ
- 自動スケーリング設定済み
