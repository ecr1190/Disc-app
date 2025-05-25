# DISC測定アプリケーション セットアップガイド

このガイドでは、Windows 11 ARM64環境でDISC測定アプリケーションを設定する手順を説明します。

## 1. 環境要件

- Windows 11 ARM64
- Python 3.10以上
- MySQL 8.0以上

## 2. 修正後のrequirements.txt

エラーが出た`numpy`や`matplotlib`パッケージを除外し、グラフ描画を別の方法で実装するため、以下のように`requirements.txt`を修正しました：

```
flask==2.3.3
flask-sqlalchemy==3.1.1
flask-login==0.6.2
flask-wtf==1.2.1
pymysql==1.1.0
werkzeug==2.3.7
email-validator==2.0.0
cryptography==41.0.3
gunicorn==21.2.0
python-dotenv==1.0.0
flask-migrate==4.0.4
```

## 3. インストール手順

1. リポジトリをクローンまたはダウンロードします
```
git clone https://github.com/yourusername/disc-app.git
cd disc-app
```

2. 仮想環境を作成してアクティベートします
```
python -m venv venv
# Windowsの場合
venv\Scripts\activate
```

3. 依存パッケージをインストールします
```
pip install -r requirements.txt
```

4. MySQL データベースを設定します
```sql
CREATE DATABASE disc_app CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'disc_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON disc_app.* TO 'disc_user'@'localhost';
FLUSH PRIVILEGES;
```

5. 設定ファイルを編集します
`config.py`ファイル内の`SQLALCHEMY_DATABASE_URI`を以下のように変更します：
```python
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://disc_user:your_password@localhost/disc_app'
```

## 4. ARM64環境でのグラフ描画について

Windows ARM64環境では、一部のPythonパッケージ（numpyやmatplotlib）のインストールに問題が生じる場合があります。このアプリケーションでは、グラフ描画を以下のように処理しています：

1. サーバー側でデータを準備
2. Chart.jsを使用してフロントエンドでグラフを描画

これにより、複雑なPythonグラフィックライブラリに依存せずにアプリケーションを実行できます。

## 5. アプリケーションの起動

1. データベースを初期化します
```
python app.py
```
初回実行時、自動的にデータベースのテーブルが作成され、初期データが投入されます。

2. アプリケーションを実行します
```
python app.py
```

3. ブラウザで以下のURLにアクセスします
```
http://localhost:5000
```

## 6. 管理者アカウント

初期管理者アカウントは以下のとおりです：
- ユーザー名: admin
- パスワード: adminpassword

セキュリティのため、初回ログイン後にこのパスワードを変更することを強くお勧めします。

## 7. トラブルシューティング

### データベース接続エラー

- MySQLサービスが実行されていることを確認してください
- `config.py`内のデータベース接続文字列が正しいことを確認してください
- MySQLのユーザー名、パスワード、データベース名が正しいことを確認してください

### モジュールが見つからないエラー

依存関係が正しくインストールされていない可能性があります。以下を試してください：
```
pip install --upgrade pip
pip install -r requirements.txt
```

### ARM64特有の問題

ARM64環境で問題が発生した場合、以下を試してください：

1. Pythonの最新バージョンを使用する（3.10以上推奨）
2. ネイティブでビルドされたPythonディストリビューションを使用する
3. 互換性のあるパッケージバージョンを使用する

## 8. カスタマイズ

- スタイルは`static/css/style.css`で変更できます
- JavaScriptの機能は`static/js/script.js`で変更できます
- テンプレートは`templates/`ディレクトリ内のファイルで変更できます

## 9. バックアップ

定期的にデータベースをバックアップすることをお勧めします：

```
mysqldump -u root -p disc_app > disc_app_backup.sql
```

---

このガイドに従ってセットアップした後も問題が発生した場合は、開発者にお問い合わせください。