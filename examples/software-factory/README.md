# software-factory

harness-testing-framework の利用者として、docs/adopting.md だけを手引きに作ったワークフロー型ハーネスの例。依頼（feature_request.md）から、小さなコードベース（repo/: shopcart の Cart）に割引コードの機能を足してリリースするまでのソフトウェア開発のワークフローを、5 フェーズ 9 ステージで定義する。フレームワーク本体はこの例を参照しない。

ステージ本体はすべて偽物で、LLM は使わない。決定論的な本体（シナリオの台本）はフィクスチャの成果物を写し、確率的な本体は種を固定した既知の分布（tests/stochastic.yaml）で変種を選ぶ。実装と単体テストの指標（ビルド、テスト、カバレッジ、lint、変更パスの範囲）は、フィクスチャのコードベースに実在のツールをかけて測る。

- workflow.yaml: ワークフロー定義
- software\_factory/metrics.py: 指標レジストリ（実在のツールで測るものを含む）
- software\_factory/personas.py: 要求の取り込みに束縛するユーザーシミュレータ（ペルソナ 3 つ）
- software\_factory/stages/: 偽のステージ本体（deterministic はシナリオ、probabilistic は確率的なもの）
- software\_factory/design.py: 設計値の MarkovModel（ゲートの分布を足せる）を作り、synthesize の予測から分布テストの基準の根拠（評価の数の期待値 E[n]、訪問の回数の分散）を出す
- software\_factory/scenarios.py: tests/scenarios/ のシナリオの YAML を作る（`python -m software_factory.scenarios`）。遷移の列を手で並べ、ファイルはフィクスチャを `{from: パス}` で参照する
- tests/: テスト、フィクスチャ、シナリオ、expectations（tests/README.md）
- docs/progress.md: 作業ログ
- docs/adopting-gaps.md: adopting.md だけでは判断できなかったこと、足りなかったこと、回避したくなったこと

## 構成

| フェーズ | ステージ | 読む | 書く | end\_state → 戻り先（carry、max） |
| --- | --- | --- | --- | --- |
| discovery | intake（ユーザー待ち） | feature_request.md | intake.md | （unknown のみ） |
| discovery | analyze | feature_request.md, intake.md | requirements.md | needs\_unclear → intake（intake\_questions、2） |
| architecture | design | requirements.md, repo/ | design.md | requirements\_gap → analyze（requirement\_gaps、1）。フェーズ境界越え |
| architecture | plan\_tasks | requirements.md, design.md, repo/ | tasks.yaml | design\_incomplete → design（design\_issues、2） |
| construction | implement | requirements.md, design.md, tasks.yaml, repo/ | repo/src/, impl\_notes.md | task\_unclear → plan\_tasks（task\_questions、1）。フェーズ境界越え<br>quality\_violation → implement（impl\_violations、2） |
| construction | unit\_test | requirements.md, tasks.yaml, repo/, impl\_notes.md | repo/tests/, test\_report.md | impl\_defect → implement（failing\_tests、2）<br>tests\_insufficient → unit\_test（coverage\_gaps、2） |
| assurance | acceptance | feature_request.md, intake.md, requirements.md, tasks.yaml, repo/, test\_report.md | verification.md | requirement\_misread → analyze（requirement\_gaps、1）。三つのフェーズ境界越え<br>requirement\_unmet → implement（unmet\_requirements、2）。フェーズ境界越え |
| assurance | review | design.md, tasks.yaml, repo/, verification.md | review.json | design\_flaw → design（design\_issues、1）。フェーズ境界越え<br>changes\_requested → implement（review\_findings、2）。フェーズ境界越え。assurance のゲートの不合格もこれで戻る |
| delivery | release | requirements.md, verification.md, review.json, repo/ | CHANGELOG.md, release.json | notes\_incomplete → release（missing\_notes、1） |

inputs は feature_request.md と repo/（変更前のコードベース）。

## 実在のツールで測る指標

指標はスナップショットの repo/ を一時ディレクトリに書き出し、このインタプリタで次を走らせる。結果は指標名、引数、内容のハッシュで覚える（同じ内容には同じ値）。

| 指標 | ツール | 使うところ |
| --- | --- | --- |
| build\_passes | `compileall` と、src の下の全モジュールの import | implement、construction のゲート |
| tests\_pass | `pytest` | implement（既存のテスト）、unit\_test、acceptance、construction と delivery のゲート |
| line\_coverage | `coverage run -m pytest` と `coverage json` | unit\_test（80% 以上）、construction のゲート |
| lint\_errors | `ruff check --isolated`（E、F、W、行の長さ 100） | implement（src）、unit\_test（tests）、construction のゲート（両方） |
| out\_of\_scope\_changes | `view.baseline()` との差を、tasks.yaml のタスクの paths と tests に照らす | implement（paths）、unit\_test（tests）、construction のゲート（フェーズの開始から） |

writes（repo/src/、repo/tests/）の外を変えるのは契約違反で、評価の前に escalate される。out\_of\_scope\_changes はそれより狭い、タスクの範囲を測る。

## 確率的な本体の仕掛け

- carry を受けた再進入で分布が変わる: release は、記憶 missing\_notes を受けたかで分布を選ぶ（goal 0.75 → 0.97）。release に戻る辺は自分自身への一本だけで、運用者が中止で答える実行では「訪問 2 以降」と一致する
- クラス内で下流の分布が分かれる: divergent では、implement の goal の二つの変種のうち ok は REQ-1 の割引額の切り捨てを誤り、ok\_fixed は正しい。unit\_test の変種 defect のテストは、実在の pytest で ok では落ち（impl\_defect）、ok\_fixed では通る（goal）。markov では二つ目の変種が ok と同じ誤りを持つ ok\_b なので分かれない
- intake は、種から選んだペルソナに尋ね、回答で intake.md を書く。ペルソナごとの intake.md は intake の goal の違う代表になるが、下流は変えない
- ゲートの分布: markov の実行のゲートはいつも goal。もう一つの実行の集まり（tests/expectations/markov\_gated.yaml）では、assurance のゲートを、実行の種で組み立てた RandomGateClassifier が成果物によらず 0.2 の確率で changes\_requested にする（review の goal の時にも書く review\_findings を持って implement に戻る）。ゲートの答えが代表によらないので独立性検証は違反を出さず、ゲートの分布を足した設計値のモデルの予測が実測と合う

## 通したランナー

| ランナー | テスト |
| --- | --- |
| 整合性検査 | tests/test\_definition.py |
| 契約適合テスト（パッケージに同梱した全シナリオ。参照ランタイムを使うので必須ではなく、版の確認として） | tests/test\_conformance.py |
| 遷移の決定論テスト（14 シナリオ、遷移の六種、escalate の四択、記録再生、ペルソナの束縛） | tests/test\_scenarios.py |
| 分布テスト（expectations。ゲートを揺らす実行を含む） | tests/test\_stochastic.py |
| 独立性検証 | tests/test\_independence.py |
| E2E のカバレッジ（ペルソナを束縛）とマルコフ合成（ゲートの分布を含む） | tests/test\_e2e.py |
| 偽の分類器によるオラクル検証 | tests/test\_oracle.py |
| トリアージの一周 | tests/test\_triage.py |
| 指標とフィクスチャの整合、ユーザーシミュレータ | tests/test\_metrics.py、tests/test\_personas.py |
