# harness-testing-framework

ワークフロー型エージェントハーネスのための汎用テスティングフレームワーク。現在の版は v0.1 です。v1.0 までは仕様と API が変わることがあります。

ワークフロー定義（YAML）を唯一の情報源として、ハーネスの遷移・ゲート・ロールバックを決定論的に検証し、LLM の振る舞いの分布を統計的に検証します。v0.1 には次のものが入っています。

- ワークフロー定義のスキーマ（[schema/workflow.schema.json](schema/workflow.schema.json)）と整合性検査器
- ハーネス契約 v0.1（[contract/contract.md](contract/contract.md)）と、言語に依存しない契約適合テストのシナリオ
- 参照ランタイム（Python のライブラリ）: 遷移、スナップショットと復元、記録と再生、中断と再開、escalate 後の運用者の選択
- テストランナー: 遷移の決定論テスト、分布テスト（expectations）、独立性検証、E2E のカバレッジ計画とマルコフ合成、分類器の検証、トリアージ
- 例: [examples/toy-minimal/](examples/toy-minimal/)（2 フェーズ 4 ステージ。LLM を使わない偽のステージ本体で、全ランナーを通す）

## 使い方

- 手引き: [docs/adopting.md](docs/adopting.md)
- 公開 API と、公開 API の文書の一覧: [docs/api.md](docs/api.md)
- 版ごとの変更: [docs/changelog.md](docs/changelog.md)

パッケージレジストリには公開していません。git の tag から入れてください（Python 3.12 以上）。

```sh
pip install "git+https://github.com/asuka1975/harness-testing-framework@v0.1.0"
```

## 開発

- 構築計画: [docs/plan.md](docs/plan.md)
- 決定記録: [docs/decisions.md](docs/decisions.md)
- 作業ログ: [docs/progress.md](docs/progress.md)

Python 3.12 以上と [uv](https://docs.astral.sh/uv/) が要ります。

```sh
scripts/check.sh   # 依存の同期、lint、format、型検査、テスト、配布物の確認
```

## ライセンス

GPL-3.0-or-later（GNU GPL 第 3 版、またはそれ以降の版）。[LICENSE](LICENSE) を参照。
