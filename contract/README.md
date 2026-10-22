# contract

ハーネス契約（言語に依存しない仕様）。保護ファイル。

- [contract.md](contract.md): 契約の本文（三つの操作、遷移、スナップショット、実行記録、インターフェース、記録再生、契約適合テスト）
- [snapshot.schema.json](snapshot.schema.json): スナップショットのマニフェストの形式
- [trace.schema.json](trace.schema.json): 実行記録の一行の形式
- examples/: 形式の例

Python の束縛は `harness_testing_framework.contract`。契約適合テストは conformance/ にある。
