# eBay Wood プロジェクト

eBay APIを使用してeBay商品の在庫レポートを生成し、XMLファイルを処理してCSVファイルを作成するWebアプリケーションです。
（全ての機能が完成していない可能性があります）

## 🚀 機能

- **eBay OAuth 2.0認証**: eBayアカウントとの安全な連携
- **在庫レポート生成**: eBay Inventory APIを使用したアクティブ商品リストの取得
- **XMLファイル処理**: 大容量XMLファイルの並列処理とCSV変換
- **リアルタイム進捗表示**: WebSocketを使用した処理状況のリアルタイム更新
- **ファイルダウンロード**: 生成されたCSVファイルの自動ダウンロード

## 🏗️ 技術スタック

- **バックエンド**: Python Flask
- **フロントエンド**: HTML, CSS, JavaScript
- **API**: eBay Feed API, eBay Inventory API
- **デプロイ**: Google Cloud Run
- **認証**: eBay OAuth 2.0

## 📁 プロジェクト構造

```
wood/
├── app.py                 # メインFlaskアプリケーション
├── config.py              # 設定ファイル
├── xml_processor.py       # XML処理ロジック
├── progress_manager.py    # 進捗管理
├── requirements.txt       # Python依存関係
├── Dockerfile            # Dockerコンテナ設定
├── cloudbuild.yaml       # Google Cloud Build設定
├── .env.example          # 環境変数テンプレート
├── static/
│   └── app.js            # フロントエンドJavaScript
└── templates/
    ├── index.html        # ログインページ
    └── dashboard.html    # ダッシュボード
```

## 🔧 開発環境セットアップ

### 前提条件

- Python 3.9以上
- eBay Developer Account
- eBay App ID, Cert ID, RuName

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd wood
```

### 2. 仮想環境の作成

```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# または
.venv\Scripts\activate     # Windows
```

### 3. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 4. 環境変数の設定

`.env`ファイルを作成し、以下の設定を追加：

```bash
# eBay API設定
EBAY_APP_ID=your_ebay_app_id_here
EBAY_CERT_ID=your_ebay_cert_id_here
EBAY_RU_NAME=your_redirect_uri_here

# 本地调试用 - 设置此项可跳过OAuth流程
EBAY_USER_ACCESS_TOKEN=your_user_access_token_here

# Flask設定
FLASK_ENV=development
SECRET_KEY=your_secret_key_here
LOG_LEVEL=DEBUG

# パフォーマンス設定
MAX_WORKERS=4
TASK_TIMEOUT=300
```

### 5. 開発サーバーの起動

```bash
python app.py
```

アプリケーションは `http://localhost:8080` でアクセス可能です。

### 🔍 ローカルデバッグモード

OAuth認証をスキップしてローカルでテストする場合：

1. eBayから直接ユーザーアクセストークンを取得
2. `.env`ファイルに `EBAY_USER_ACCESS_TOKEN` を設定
3. アプリケーションを起動すると自動的にダッシュボードにアクセス可能

## 🌐 本番環境デプロイ（Google Cloud Run）

### 前提条件

- Google Cloud Platform アカウント
- Google Cloud CLI (`gcloud`) のインストールと認証
- Docker のインストール

### 1. Google Cloud プロジェクトの設定

```bash
# プロジェクトIDを設定
export PROJECT_ID=your-gcp-project-id

# プロジェクトを設定
gcloud config set project $PROJECT_ID

# 必要なAPIを有効化
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
```

### 2. 環境変数の設定

Cloud Runサービスに環境変数を設定：

```bash
gcloud run services update wood-ebay-app \
  --set-env-vars="EBAY_APP_ID=your_app_id" \
  --set-env-vars="EBAY_CERT_ID=your_cert_id" \
  --set-env-vars="EBAY_RU_NAME=your_ru_name" \
  --set-env-vars="SECRET_KEY=your_secret_key" \
  --set-env-vars="FLASK_ENV=production" \
  --region=asia-northeast1
```

### 3. Cloud Buildを使用したデプロイ

```bash
# Cloud Buildでビルドとデプロイ
gcloud builds submit --config cloudbuild.yaml .
```

### 4. サービスの確認

```bash
# サービスURLを取得
gcloud run services describe wood-ebay-app \
  --region=asia-northeast1 \
  --format="value(status.url)"
```

## 📋 使用方法

### 1. 認証
- アプリケーションにアクセス
- 「eBayでログイン」ボタンをクリック
- eBayアカウントで認証

### 2. レポート生成
- ダッシュボードで「レポート生成」をクリック
- 処理の進捗をリアルタイムで確認
- 完了後、CSVファイルが自動ダウンロード

### 3. XMLファイル処理
- XMLファイルをアップロード
- 処理形式を選択（Enhanced CSV等）
- 変換されたCSVファイルをダウンロード

## 🔧 設定オプション

### 環境変数

| 変数名 | 説明 | デフォルト値 |
|--------|------|-------------|
| `EBAY_APP_ID` | eBay App ID | 必須 |
| `EBAY_CERT_ID` | eBay Cert ID | 必須 |
| `EBAY_RU_NAME` | eBay RuName (Redirect URI) | 必須 |
| `EBAY_USER_ACCESS_TOKEN` | デバッグ用ユーザートークン | オプション |
| `SECRET_KEY` | Flask セッション暗号化キー | 必須 |
| `FLASK_ENV` | Flask環境 | `production` |
| `LOG_LEVEL` | ログレベル | `INFO` |
| `MAX_WORKERS` | 並列処理ワーカー数 | `4` |
| `TASK_TIMEOUT` | タスクタイムアウト（秒） | `300` |
| `PORT` | サーバーポート | `8080` |

## 🐛 トラブルシューティング

### よくある問題

1. **OAuth認証エラー**
   - eBay RuNameが正しく設定されているか確認
   - eBay Developer Consoleでアプリケーション設定を確認

2. **API呼び出しエラー**
   - アクセストークンの有効期限を確認
   - eBay APIの利用制限を確認

3. **ファイル処理エラー**
   - XMLファイルの形式を確認
   - メモリ使用量を確認

### ログの確認

```bash
# ローカル環境
tail -f app.log

# Cloud Run環境
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=wood-ebay-app" --limit 50
```

## 🤝 コントリビューション

1. フォークを作成
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add some amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📞 サポート

問題や質問がある場合は、GitHubのIssuesページで報告してください。

