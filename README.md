# harness-testing-framework

ワークフロー型エージェントハーネスのための汎用テスティングフレームワーク。開発中で、まだ使える版はありません。

ワークフロー定義（YAML）を唯一の情報源として、ハーネスの遷移・ゲート・ロールバックを決定論的に検証し、LLM の振る舞いの分布を統計的に検証するための、スキーマ、ハーネス契約、整合性検査器、参照ランタイム、テストランナー群を提供する予定です。

- 構築計画: [docs/plan.md](docs/plan.md)
- 決定記録: [docs/decisions.md](docs/decisions.md)
- 作業ログ: [docs/progress.md](docs/progress.md)

## 開発

Python 3.12 以上と [uv](https://docs.astral.sh/uv/) が要ります。

```sh
scripts/check.sh   # 依存の同期、lint、format、型検査、テスト、配布物の確認
```

## ライセンス

GPL-3.0-only。[LICENSE](LICENSE) を参照。
