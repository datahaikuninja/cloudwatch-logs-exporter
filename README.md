# cloudwatch-logs-exporter
CloudWatchログのログデータをS3バケットへエクスポートするスクリプトです。

本スクリプトには次の特徴があります。一つは、エクスポート対象のロググループ名やエクスポート先のS3バケット名などをスクリプトの引数に渡す点です。スクリプトの外から渡すことで、別の環境で実行する際にスクリプトの中身を書き換える必要がありません。

もう一つは、S3オブジェクト（エクスポートするログデータ）のキー(prefix)に年月日を付与することで、後にAthenaで集計分析する際にパーティショニングによるクエリ実行時間とコスト削減の恩恵を得られる点です。

# Usage
以下のように使用します。
```
python3 cloudwatch-logs-exporter.py \
  --start_datetime "2023/01/01 00:00:00" \
  --end_datetime "2023/01/31 23:59:59" \
  --log_group_name "example-access-log" \
  --log_stream_name_prefix "api/" \
  --destination_bucket "cloudwatch-logs-exporter" \
  --destination_prefix "api/" \
  --profile "example"
```
スクリプトの引数の意味は以下のコマンドで知ることができます。
```
python3 cloudwatch-logs-exporter.py -h
```

個人的な使い勝手のために、すべてのオプション引数を必須指定（Required=True）としていますが、状況によってはログストリームやS3バケットのprefixは指定不要としたい場合もあるでしょうから、そういった場合はスクリプトを自由に変更して使っていただいて構いません。

また、スクリプトの実行状況を知るために以下のように標準出力にメッセージを出していますが、こちらも好きに変えていただいて構いません。
```
taskName: export_logs_from_2021-07-01_00:00:00_to_2021-07-01_23:59:59, taskStatus: PENDING
taskName: export_logs_from_2021-07-01_00:00:00_to_2021-07-01_23:59:59, taskStatus: RUNNING
taskName: export_logs_from_2021-07-01_00:00:00_to_2021-07-01_23:59:59, taskStatus: RUNNING

...中略...

export_logs_from_2021-07-01_00:00:00_to_2021-07-01_23:59:59, taskStatus: COMPLETED
```
