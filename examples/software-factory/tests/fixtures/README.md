# software-factory/tests/fixtures

ステージ本体が作業領域に写す成果物。成果物の先頭の印 `[[class <ステージ>=<クラス>]]` は、確率的な実行で MarkerClassifier が読む。

- inputs/feature_request.md: ワークフローの inputs の依頼
- .code/baseline/repo/: ワークフローの inputs の、変更前のコードベース（shopcart の Cart と、そのテスト）
- .code/implement/<変種>/: implement が書く repo/src/ と impl\_notes.md
- .code/unit\_test/<変種>/: unit\_test が書く repo/tests/test\_discount.py と test\_report.md
- <ステージ>/<変種>/: ほかのステージの成果物

コードを含むフィクスチャを .code/ の下に置くのは、意図的に lint に反するもの、構文の誤り、失敗するテスト、同じ名前の
モジュールの変種を、リポジトリ全体の検査から外すため。mypy はドットで始まるディレクトリを辿らず、ruff は ruff.toml の
exclude で、pytest は tests/conftest.py の collect\_ignore で外す。指標はこれらの設定によらず、一時ディレクトリで測る。
