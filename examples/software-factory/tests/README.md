# software-factory/tests

- fixtures/: ステージ本体が写す成果物 fixtures/<ステージ>/<変種>/ と、ワークフローの inputs の fixtures/inputs/（fixtures/README.md）
- scenarios/: 遷移の決定論テストのシナリオ（contract/conformance/scenario.schema.json の形）。inputs と開始時スナップショットの
  ファイルは、フィクスチャを `{from: パス}` で参照する。software\_factory/scenarios.py が作る
- stochastic.yaml: 確率的な偽の本体の設計値（変種、クラス、記憶、落ちる指標、分布）。profiles の markov と divergent は分布テスト、
  独立性検証、マルコフ合成に、labeling は人がラベルを付ける材料（docs/human-labeling.md）の試しの実行に使う
- expectations/: 分布テストの基準。markov.yaml は通るはずのもの、markov\_shifted.yaml はすべて落ちるはずのもの、markov\_gated.yaml は
  assurance のゲートを実行の種で揺らす実行で通るはずのもの（bindings.gates にゲートの分布）、markov\_gated\_shifted.yaml は
  その実行ですべて落ちるはずのもの
- conftest.py: 多数の実行の集まりと、設計値の MarkovModel の予測を、テストの間で共有する
- test\_labeling.py: docs/human-labeling.md とそのコーパスが試しの実行から作り直したものと一致すること、受け取ったラベルを
  印と比べる仕組み（`python -m software_factory.labeling`）を確かめる。ラベルのファイル docs/human-labels.jsonl は人がラベルを
  付けるまで無く、その間 compare は無いことを報告する

分布テスト、独立性検証、マルコフ合成の回数は、環境変数 `HTF_RUNS` で増やせる（減らせない）。人がラベルを付ける材料の試しの実行は
240 回に固定する（材料の項目が回数で変わらないように。`HTF_RUNS` によらない）。

独立性検証（`independence`）と入り方の検定（`entry_dependence`）は、正しい本体でも偶然に違いを示しうる。確かめ方は次のとおり。

- 仕込んだ違い（divergent の stage:implement=goal、訪問 1 → 1）は violated で確かめる（p 値はおよそ 0.0005）
- 仕込んでいない所を全状態（全ステージ）で見る時は、判定できた検定の数で alpha 0.01 を割る（`family_wise_violations`）
- 仕込んでいない所を絞って見る時（markov の stage:implement=goal の訪問 1 → 1、intake のペルソナの代表、入り方の検定の
  implement）は、判定でき、p 値が 0.001 以上であることで確かめる。補正の無い alpha 0.01 で not\_detected を求めると、種の基点を
  変えて 200 回ずつ試した検証役の確かめで、正しい本体でも markov の集まりで 8/200、ゲートを揺らす集まりで 6/200 落ちた
- それでも、`HTF_RUNS` や種を変えると、絞った確かめはそれぞれ約 0.1%、全状態の確かめは約 1% の確率で、正しい本体でも落ちうる。
  落ちたら、まず別の種で再現するかを見る
