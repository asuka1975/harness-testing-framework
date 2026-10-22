# software-factory/tests

- fixtures/: ステージ本体が写す成果物。fixtures/<ステージ>/<変種>/ と、コードを含む fixtures/.code/<ステージ>/<変種>/。
  fixtures/inputs/feature_request.md と fixtures/.code/baseline/repo/ はワークフローの inputs（fixtures/README.md）
- scenarios/: 遷移の決定論テストのシナリオ（contract/conformance/scenario.schema.json の形）
- stochastic.yaml: 確率的な偽の本体の設計値（変種、クラス、記憶、落ちる指標、分布）
- expectations/: 分布テストの基準。markov.yaml は通るはずのもの、markov\_shifted.yaml はすべて落ちるはずのもの
- conftest.py: fixtures/ の下を pytest の収集から外す（フィクスチャのコードベースに、意図的に失敗するテストがある）

分布テスト、独立性検証、マルコフ合成の回数は、環境変数 `HTF_RUNS` で増やせる（減らせない）。
