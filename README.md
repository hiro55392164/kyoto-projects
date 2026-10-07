# kyoto-projects
京都入札案件

## 入札工程表

Streamlitのサイドバーから「入札工程表」を開きます。表のセルで件名、配置技術者名、申請日、入札日、開札日、工期開始・終了、備考を編集し、「変更を保存」を押してください。最下行で追加、行選択で削除できます。

工程図には編集中の内容が即時反映されます。配置技術者での絞り込み、同一技術者の工期重複確認、Excelへの表のダウンロードに対応しています。「保存済みデータを再読込」は未保存の編集を破棄します。

保存先はチェックアウトの隣の `kyoto-projects-data/bids.sqlite3` です。必要なら `BID_SCHEDULE_DB` で変更できます。保存はこの環境内での永続化であり、他の環境への同期は行いません。

クラウド環境での起動例（準備済みのPython環境とテンプレート別名を使用）:

```sh
cd /workspace/kyoto-projects-runtime
/workspace/kyoto-projects-env/bin/python -m streamlit run /workspace/kyoto-projects/app.py --server.headless=true --server.address=127.0.0.1 --server.port=8501 --browser.gatherUsageStats=false
```

## 入札公告PDFの読み取り

「入札公告PDFから案件を追加」を開き、PDFをアップロードして「PDFを読み取る」を押します。候補と原文を確認・修正し「確認した内容を案件表へ追加」、最後に「変更を保存」を押してください。既存の表の未保存の編集も引き継ぎます。

文字入りPDFの自動抽出は外部API不要です。和暦、申請期限、入札書提出期限、開札日、工期に対応し、曖昧な候補や契約日基準の開始日は空欄にします。画像PDFはAI読み取りまたは手動入力を使用してください。対応は15MB・20ページまでで、範囲を超えたPDFを黙って省略しません。

AI読み取りを有効にする場合は、Streamlit Cloudのアプリ設定のSecretsに `BID_AI_API_KEY` を安全に設定してください。環境変数でも設定できます。値をGitHubやチャットに貼り付けないでください。デフォルトモデルは `gpt-4.1-mini`（環境変数 `BID_AI_MODEL` で変更）。AI読み取りはPDFの内容をOpenAIへ送信し、画像ページも解析対象にします。API利用料がかかります。API接続と実際のAI抽出は、キーを設定した公開環境での確認が必要です。

発注者・キーワードから京都府サイトを自動検索する機能は未実装です。実際の検索システムURLと、通信許可・検索方法の確認が必要です。

検証: `python -m unittest discover -s tests -v`
