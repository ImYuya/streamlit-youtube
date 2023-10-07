# 使い方

.envファイルを作成
```Shell
cp .env.sample .env
```

.envファイルの設定（OPENAI_API_KEYは[こちら](https://platform.openai.com/account/api-keys)から取得）
```Shell
OPENAI_API_KEY=<YOUR API KEY>
```

必要な方はpoetryをインストール
```Shell
pip install poetry
```

仮想環境作成(初回のみ)
```Shell
poetry install
```

アプリ実行
```Shell
poetry run streamlit run main.py
```

# 仕様
- 1秒ごとのスクリーンショットは`static`フォルダに保存される
- ダウンロードした動画および作成した音声ファイルは`movie`フォルダに保存される

