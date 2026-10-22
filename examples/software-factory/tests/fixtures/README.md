# software-factory/tests/fixtures

ステージ本体が作業領域に写す成果物。成果物の先頭の印 `[[class <ステージ>=<クラス>]]` は、確率的な実行で MarkerClassifier が読む。

- inputs/: ワークフローの inputs。依頼の feature\_request.md と、変更前のコードベース repo/（shopcart の Cart と、そのテスト）
- implement/<変種>/: implement が書く repo/src/ と impl\_notes.md
- unit\_test/<変種>/: unit\_test が書く repo/tests/test\_discount.py と test\_report.md
- <ステージ>/<変種>/: ほかのステージの成果物

コードを含むフィクスチャには、意図的に lint に反するもの、構文の誤り、失敗するテスト、同じ名前のモジュールの変種がある。
tests/fixtures/ の下はリポジトリの検査（ruff、mypy、pytest の収集）から外れる（adopting.md 第11節）ので、そのまま置く。
指標はこれらを一時ディレクトリに書き出して、実在のツールで測る（lint は `ruff check --isolated`）。
