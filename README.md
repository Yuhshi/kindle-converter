# kindle-converter

HTML をダウンロードして、kindle の mobi ファイルを作る準備をする。
別途 kindlegen コマンドが必要。

1. 作業用のディレクトリを作る(HTML等がダウンロードされるので)
2. sample-config.yaml と同じ形式で設定を書く。
	* HTML に余分な要素が入っていると重くなる場合があるので、convert 関数で HTML を変換する
3. python converter.py 設定ファイル.yaml
4. kindlegen -verbose 生成されたOPFファイル.opf

----

## イントールしたパッケージ等

* python 2.7

* brew install libxml2
	* export C_INCLUDE_PATH=/usr/local/Cellar/libxml2/2.9.2/include/libxml2/:$C_INCLUDE_PATH
* pip install lxml
* pip install pillow
* pip install pyyaml

