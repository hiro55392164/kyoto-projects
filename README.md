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
