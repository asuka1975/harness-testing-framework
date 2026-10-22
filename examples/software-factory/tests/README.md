# software-factory/tests

- fixtures/: ステージ本体が写す成果物 fixtures/<ステージ>/<変種>/ と、ワークフローの inputs の fixtures/inputs/（fixtures/README.md）
- scenarios/: 遷移の決定論テストのシナリオ（contract/conformance/scenario.schema.json の形）。inputs と開始時スナップショットの
  ファイルは、フィクスチャを `{from: パス}` で参照する。software\_factory/scenarios.py が作る
- stochastic.yaml: 確率的な偽の本体の設計値（変種、クラス、記憶、落ちる指標、分布）
- expectations/: 分布テストの基準。markov.yaml は通るはずのもの、markov\_shifted.yaml はすべて落ちるはずのもの、markov\_gated.yaml は
  assurance のゲートを実行の種で揺らす実行で通るはずのもの（bindings.gates にゲートの分布）
- conftest.py: 多数の実行の集まりと、設計値の MarkovModel の予測を、テストの間で共有する

分布テスト、独立性検証、マルコフ合成の回数は、環境変数 `HTF_RUNS` で増やせる（減らせない）。
