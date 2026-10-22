# F4 software-factory workflow.yaml 事前レビュー（検証役）

- 検証日: 2026-10-22
- 対象のコミット: 87f03d5（「F4 往復 5: N11 は解消し、adopting-gaps.md の「未解消」が空になった」）。元の作業ツリーには docs/decisions.md と docs/progress.md の未コミットの変更があったが、examples/ には変更が無い。HEAD の内容を見た
- 役割: 検証（第三者）。examples/software-factory/workflow.yaml の MECE の事前レビュー（人間のレビューに出す前の確認）。実装の作業過程は見ておらず、成果物と仕様だけから判定した
- 読んだもの
  - 対象: examples/software-factory/workflow.yaml、README.md、software\_factory/（metrics.py、stages/deterministic.py、stages/probabilistic.py）、tests/fixtures/ の全変種、tests/stochastic.yaml。意図の確認のために docs/adopting-gaps.md の C1 と D4、tests/scenarios/task\_unclear\_crosses\_phase.yaml
  - 基準: docs/plan.md 第2節と第6節 F4。contract/contract.md 第2・3節（特に 2.4）と第5節。docs/adopting.md 第2節（2.1〜2.6）と第4・5節。schema/workflow.schema.json
  - 参考: reports/f1-toy-minimal-review.md、docs/decisions.md（HEAD の版の一覧、D-3、D-11 の C1）。記憶の扱いを確かめるために、参照ランタイムの状態文書の組み立てと終了時の記憶の作り方を読んだ
- 書いたもの: このファイルだけ。workflow.yaml などは変えていない。下の書き換え案はすべて提案である

## 総合判定: 直してから出すべき

整合性検査は違反も警告も無く通り、例のテストは全部通る（下記「証拠」）。end\_state にはすべて戻り先があり、carry の記憶は記述の中で証拠として名指されている。重なりうる所には優先が書かれ、assurance のゲートは adopting.md 2.4 の書き方（goal の時にも中身を持つ review\_findings で戻す）に従っている。骨格はよくできている。

ただし、次の二つは分類器が記述どおりに読むと主経路で誤る。人間に出す前に直すべきである。

1. **高 H-1**: implement と design は、memory\_out の記憶を「問題がある時に書く」としか書いていない。carry で持ち帰った値は、本体が書かなければスナップショットに残り、状態文書にそのまま出る。implement の task\_unclear は「task\_questions に問いが列挙されていれば goal に優先する」ので、plan\_tasks から戻った次の訪問は、問いが解けていても task\_unclear に分類されうる。その辺は max 1 なので、そこで escalate になる。参照ランタイムで、古い問いが状態文書に出ることを確かめた
2. **高 H-2**: plan\_tasks の goal は「各タスクの paths と tests が design.md の『## 構成』のファイルに収まり」を求める。一方、design.md の「## 構成」は repo/src/ の変えるファイルしか挙げない。goal の代表のフィクスチャ自身がこの文に反している。design\_incomplete にも当たらないので、記述どおりに読むと主経路が unknown になる

中の指摘は八つある。指標が落ちた時に当たる end\_state が無い所（M-1、M-2）、四つのゲートの不合格が unknown に落ちることが書かれていない所（M-3）、観測できない goal の条件（M-4）、狭すぎる end\_state（M-5）、空でも成り立つ end\_state（M-6）、要件の id の数え漏れ（M-7）、記述と合わない代表のフィクスチャ（M-8）である。分類体系の変更（end\_state の追加・分割・統合）が要るのは M-2 の別案だけで、ほかは記述、description、指標の実装、フィクスチャの直しで済む。M-1、M-2、M-5、M-8 の推奨案は既存のクラスの境界を広げる（追加・分割・統合ではない）。

## 前提と方法

### 分類器が見るもの

契約 2.4 により、ステージの状態文書は、そのステージの reads と writes のファイルの内容と、memory\_out の記憶の値でできる。フェーズゲートの状態文書は、フェーズ内の全ステージの reads と writes の和と、最終ステージの memory\_out でできる。memory\_in は入らない。指標の値も入らない。

| 対象 | ファイル | 記憶 |
| --- | --- | --- |
| intake | feature\_request.md、intake.md | （無し） |
| analyze | feature\_request.md、intake.md、requirements.md | intake\_questions |
| design | requirements.md、repo/、design.md | requirement\_gaps |
| plan\_tasks | requirements.md、design.md、repo/、tasks.yaml | design\_issues |
| implement | requirements.md、design.md、tasks.yaml、repo/、impl\_notes.md | task\_questions、impl\_violations |
| unit\_test | requirements.md、tasks.yaml、repo/、impl\_notes.md、test\_report.md | failing\_tests、coverage\_gaps |
| acceptance | feature\_request.md、intake.md、requirements.md、tasks.yaml、repo/、test\_report.md、verification.md | unmet\_requirements、requirement\_gaps |
| review | design.md、tasks.yaml、repo/、verification.md、review.json | review\_findings、design\_issues |
| release | requirements.md、verification.md、review.json、repo/、CHANGELOG.md、release.json | missing\_notes |
| ゲート discovery | feature\_request.md、intake.md、requirements.md | intake\_questions |
| ゲート architecture | requirements.md、repo/、design.md、tasks.yaml | design\_issues |
| ゲート construction | requirements.md、design.md、tasks.yaml、repo/、impl\_notes.md、test\_report.md | failing\_tests、coverage\_gaps |
| ゲート assurance | 上の acceptance と review の和 | review\_findings、design\_issues |
| ゲート delivery | release と同じ | missing\_notes |

全記述の参照先をこの表と突き合わせた。参照するファイルと記憶は、すべて投影に入っている。観測の問題は、前後の差（「変更」）を述べる条件、指標の値（カバレッジの百分率）を述べる条件、記録の形式に無い事実（どのパスを査読したか、M-4）に限られる。

### 記憶の持ち越し

スナップショットは記憶をすべて持つ（契約 5）。スキーマの memory\_in の説明も「carry で運ばれてくるもの、または前のステージの memory\_out」と書き、記憶が前へ流れることを前提にしている。carry で重ねた記憶は、戻り先の開始時スナップショットに入り（契約 2.3）、以後のステージにも残る。本体が memory\_out の項目を書かなければ、終了時スナップショットにはその残った値があり、状態文書の「## 記憶」に出る。一方、ファイルは事情が違う。そのステージの writes の内容は、開始時スナップショットではそのステージが一度も走っていない時点のものになる。どの戻りも、そのステージかそれより前の開始時スナップショットを復元するからである。

### 証拠

- 整合性検査: リポジトリの複製の上で `PYTHONPATH=examples/software-factory uv run --offline python -m harness_testing_framework.testing.spec examples/software-factory/workflow.yaml --registry software_factory.metrics:REGISTRY` → `0 error(s), 0 warning(s)`、終了コード 0
- 例のテスト: 複製の上で `uv run --offline pytest -q examples/software-factory/tests -p no:cacheprovider --no-cov` → 157 passed（70.7 秒）
- 実験 1（H-1）: 複製の上で、参照ランタイムに偽の本体を束縛して走らせた。implement の訪問 1 は変種 unclear を写し、task\_questions に問いを書く。訪問 2 は変種 ok\_fixed を写し、impl\_violations だけを書く（task\_questions は書かない）。ほかのステージは goal の変種である。分類器は MarkerClassifier を包んで状態文書を記録した。implement の訪問 2 の状態文書に `## 記憶 task_questions` として `["T2: 割引を小計に適用するのか、商品ごとに適用するのかが tasks.yaml から決められない"]` が出た。選択肢は goal、task\_unclear、quality\_violation、unknown だった。印を読む分類器なので実行は完了した。例のシナリオ task\_unclear\_crosses\_phase.yaml も、implement#2 で記憶を書かない台本（implement/ok を写すだけ）なので、同じ状態文書を分類器に渡している。台本の分類器は goal を返すので、テストは通る
- 実験 2（M-7）: 例の要件の id の照合（`\bREQ-1\b`）に文字列を与えた。`- REQ-1: 分岐`、`REQ-1、REQ-2`、`（REQ-1）`、`REQ-1 の割引` は 1.0、`REQ-1は Discount.apply`、`REQ-1の割引`、`REQ-1と REQ-2` は 0.0 になった
- 実験 3（M-5、L-8）: 複製の上で workflow.yaml の写しを作り、unit\_test の memory\_in に review\_findings を足したもの、failing\_tests を足したものをそれぞれ整合性検査にかけた。どちらも `memory_unsupplied` の誤り一件で、終了コード 1 だった

## ステージとゲートの所見（要約）

| 対象 | クラス | MECE | 観測 | carry と戻り先 |
| --- | --- | --- | --- | --- |
| intake | goal、unknown | 最初のステージなので構造上こうなる。妥当 | 可。持ち帰った問いを尋ねたかは見えない（L-2） | なし |
| analyze | goal、needs\_unclear、unknown | 優先あり。根拠の無い要件などは unknown（自分で直す不足）。妥当 | 可 | intake\_questions → intake。妥当。max 2 |
| design | goal、requirements\_gap、unknown | 全要件を割り当てたうえで問いを残すと unknown（L-7） | 可 | requirement\_gaps → analyze。古い値が残る（H-1） |
| plan\_tasks | goal、design\_incomplete、unknown | goal の文が代表の成果物と矛盾する（H-2） | 可 | design\_issues → design。妥当 |
| implement | goal、task\_unclear、quality\_violation、unknown | 既存のテストの失敗と自己申告の漏れは unknown（M-1） | 「変更」は差で、指標と impl\_notes.md 頼み（L-3） | task\_questions と impl\_violations に古い値が残る（H-1） |
| unit\_test | goal、impl\_defect、tests\_insufficient、unknown | lint、範囲、誤ったテストは unknown（M-2） | 「80%」は分類器に見えない（M-2） | 妥当。回帰テストが失われうる（L-8） |
| acceptance | goal、requirement\_misread、requirement\_unmet、unknown | 優先あり。妥当 | 可 | 妥当。代表の unmet が記述と合わない（M-8） |
| review | goal、design\_flaw、changes\_requested、unknown | changes\_requested が空でも成り立つ（M-6）。テストへの指摘は unknown（M-5） | 査読したパスが記録されない（M-4） | 妥当 |
| release | goal、notes\_incomplete、unknown | 版を上げ忘れると unknown（L-6） | 可 | 自分自身へ。妥当 |
| 五つのゲート | フェーズの goal と最終ステージのクラス | assurance だけが end\_state で戻る。ほかの四つは不合格がすべて unknown で、その意図が書かれていない（M-3） | 可 | assurance は adopting.md 2.4 どおり |

end\_state が goal の言い換えになっているものは無い。tests\_insufficient と notes\_incomplete は goal の一部の否定に近いが、原因と戻り先と carry を特定しているので、言い換えではない。

戻り先と max はどれも妥当である。フェーズ境界を越える辺は六本ある（requirements\_gap、task\_unclear、requirement\_misread、requirement\_unmet、design\_flaw、changes\_requested）。どの戻り先も carry を memory\_in に持ち、状態を直せる。費用の大きい越境（requirement\_misread は三つのフェーズを戻る）を max 1 にしているのも筋が通っている。

## 指摘

### 高

#### H-1 implement と design の memory\_out に、持ち帰った古い値が残り、分類を誤らせる

- 場所: implement の description（第207〜212行）と task\_unclear（第240〜244行）、quality\_violation（第245〜248行）。design の description（第107〜111行）と requirements\_gap（第127〜131行）
- 問題: 三つの記憶は、本体が書かなければ前の値のまま状態文書に出る。古い値がどこから入るかは次のとおり
  - implement.task\_questions: implement が task\_unclear になる → plan\_tasks に task\_questions を持ち帰る → plan\_tasks が goal に達し、architecture のゲートを通る → implement の次の訪問の開始時スナップショットに、その問いが入っている。description は「曖昧で実装を決められない時は、その問いを記憶 task\_questions に書いて」とだけ書く。そのとおりに作った本体は、問いが解けた訪問では何も書かない → 状態文書に古い問いが出る → task\_unclear の最後の一文「repo/src/ の変更の有無や指標の結果によらず、task\_questions に問いが列挙されていればこの状態とし、goal と quality\_violation に優先する」が記憶だけで成り立つ → task\_unclear → この辺は max 1 で使い切っているので escalate（max\_exceeded）。問いを解いて正しく実装した訪問が、人に回される
  - implement.impl\_violations: quality\_violation → implement（自分自身へ。carry impl\_violations）。違反を直した次の訪問で本体が書かなければ、古い違反が出る。impl\_notes.md の「## 違反」は書き直されて空なので、分類器は食い違う証拠を比べることになる。さらに、この自分自身への戻りの後の開始時スナップショットは impl\_violations を持つ。後の impl\_defect、requirement\_unmet、changes\_requested でそこへ戻るたびに、同じ古い値が入る
  - design.requirement\_gaps: requirements\_gap → analyze、または acceptance の requirement\_misread → analyze で持ち帰った値が、analyze を経て design の開始時スナップショットに入る。description は「設計できない時は、その要件と理由を記憶 requirement\_gaps に書く」だけである
- 根拠: 契約 2.3、2.4、5。スキーマの memory\_in の説明。実験 1。例のシナリオ task\_unclear\_crosses\_phase.yaml の implement#2 も記憶を書かない台本で、同じ状態文書を分類器に渡している。ほかの六つのステージ（analyze、plan\_tasks、unit\_test、acceptance、review、release）の九つの記憶は「無ければ空の一覧」と書かれ、毎回上書きされるので問題が無い
- 例のテストで見つからない理由: 確率的な偽の本体の変種（tests/stochastic.yaml）は、すべての memory\_out を毎回書く（implement の ok は `{task_questions: [], impl_violations: []}`）。MarkerClassifier と台本の分類器は記憶を読まない
- 書き換え案（分類体系の変更なし）:
  - implement の description: 「…その問いを記憶 task\_questions に書いて実装しない（無ければ空の一覧）。…ビルド、lint、変更の範囲の違反に気づいたら、その違反を記憶 impl\_violations に書く（無ければ空の一覧）」
  - design の description: 「…その要件と理由を記憶 requirement\_gaps に書く（無ければ空の一覧）」
  - task\_unclear の優先の条件を、毎回書き直されるファイルと組にする。impl\_notes.md は、implement の開始時スナップショットに決して無い（前節「記憶の持ち越し」）ので、古い値が出ない

    ```yaml
    - id: task_unclear
      description: >-
        tasks.yaml のタスクの記述が曖昧で、repo/src/ をどう変えるかを決められない。決められない点が、タスクの id とともに
        記憶 task_questions と impl_notes.md の「## 問い」の両方に列挙されている。repo/src/ の変更の有無や指標の結果によらず、
        両方に問いが列挙されていればこの状態とし、goal と quality_violation に優先する。
    ```

  - 本体の文書への申し送り: adopting.md 2.1 と第5節は、書かなかった memory\_out の項目が前の値（carry で持ち帰った値を含む）のまま状態文書に出ることを書いていない。「memory\_out の項目は訪問のたびに必ず書く（無ければ空の値）」を手引きに足すとよい（下記「計画役へ上げる事項」）

#### H-2 plan\_tasks の goal が、tests まで design.md の「## 構成」に収めることを求め、代表の成果物がそれに反する

- 場所: plan\_tasks の goal（第151〜154行）。design の description の「## 構成」（変えるファイルと役割）（第108〜109行）
- 問題: goal は「各タスクの paths と tests が design.md の『## 構成』のファイルに収まり」と書く。design の「## 構成」は「変えるファイルと役割」で、design の goal もテストのファイルを挙げることを求めていない。フィクスチャでは、tests/fixtures/design/ok/design.md の「## 構成」は repo/src/shopcart/discount.py と repo/src/shopcart/cart.py だけを挙げる。一方、tests/fixtures/plan\_tasks/ok/tasks.yaml の両タスクは `tests: [repo/tests/test_discount.py]` を持つ。goal の代表が goal の文に反している。記述どおりに読む分類器は goal を選べない。design\_incomplete は「タスクにすべての要件を割り当てられない」を条件にするが、全要件は割り当て済みなので当たらない。残りは unknown で、毎回の実行の主経路が escalate になる
- 根拠: 契約 2.2（選択肢は記述そのもの）。adopting.md 2.1（観測できる条件として書く）
- 書き換え案（分類体系の変更なし）。推奨は plan\_tasks の goal を直す案

  ```yaml
  qualitative: >-
    tasks.yaml のタスクが requirements.md のすべての要件を扱い、各タスクの paths が design.md の「## 構成」のファイルに収まり、
    tests が repo/tests/ の下にあり、タスクどうしで paths が重ならない。
  ```

  別案として、design の description と goal に「『## 構成』に、変える repo/src/ のファイルと、書く repo/tests/ のファイルを挙げる」を足し、フィクスチャの design.md にテストのファイルを足す。こちらは design の責任が増え、design.md の検査（design\_covers\_requirements）とも関係が無いので、推奨しない

### 中

#### M-1 implement で指標が落ちた時、当たる end\_state が無いか、本体の自己申告に頼っている

- 場所: implement の goal の指標（第222〜238行）、quality\_violation（第245〜248行）、description（第207〜212行）
- 問題:
  - tests\_pass（既存のテスト）が落ちると、goal は選択肢から外れる。しかし quality\_violation の列挙（byte-compile か import の失敗、lint、paths の外の変更）にも、task\_unclear にも当たらず、unknown になる。直す場所は implement 自身で、自分自身への辺はもうある
  - goal の「repo/src/ の変更が design.md の構成どおり」に反する状態も、どの end\_state にも当たらない
  - quality\_violation は「違反の内容が記憶 impl\_violations と impl\_notes.md の『## 違反』に列挙されている」を条件にする。分類器は指標の値を見ない（契約 2.4）。だから、指標は落ちたが本体が気づかなかった時（気づいていれば直したはずで、指標が捕まえるのはむしろこの場合）は、証拠が無く unknown になる。仮に quality\_violation を選んでも carry が空で、戻った implement に直す材料が届かない（契約 2.3 の 2）
- 書き換え案（分類体系の変更なし。quality\_violation の境界の変更であり、追加・分割・統合ではない）:
  - description に自己点検を足す。「終える前に、repo/src/ の byte-compile と import、repo/tests/ の既存のテスト、repo/src/ の lint、tasks.yaml の paths に照らした変更の範囲を自分で確かめ、見つかった違反を記憶 impl\_violations と impl\_notes.md の『## 違反』に書く（無ければ空の一覧）」
  - quality\_violation:

    ```yaml
    - id: quality_violation
      description: >-
        repo/src/ が、byte-compile か import に失敗する、repo/tests/ の既存のテストを落とす、lint（ruff の E、F、W）の違反がある、
        tasks.yaml のタスクの paths に無いファイルを変えている、または design.md の構成から外れている。違反の内容が記憶
        impl_violations と impl_notes.md の「## 違反」に列挙されている。
    ```

  - README に「指標が落ちても impl\_violations が空なら unknown になり、人に戻る（本体の自己点検の漏れ）」と意図を書く

#### M-2 unit\_test で、テストの側の不備が unknown に落ち、カバレッジの条件が分類器に見えない

- 場所: unit\_test の goal の指標（第276〜292行）、impl\_defect と tests\_insufficient（第294〜303行）
- 問題:
  - lint\_errors（repo/tests/）と out\_of\_scope\_changes（tasks.yaml の tests の外）が落ちると goal は選択肢から外れる。しかし impl\_defect にも tests\_insufficient にも当たらず、unknown になる。期待が要件に反するテスト（テストが誤っている）も同じである。どれも unit\_test 自身が直せる
  - tests\_insufficient の「repo/src/ の行カバレッジが 80% に届かない」は、指標の値を見ない分類器には判定できない。証拠になるのは coverage\_gaps の「実行されない箇所」だけで、本体が自分でカバレッジを測らないと書けない
- 書き換え案:
  - description に自己点検を足す（分類体系の変更なし）。「終える前に、pytest、行カバレッジ、repo/tests/ の lint、tasks.yaml の tests に照らした範囲を自分で確かめ、結果を test\_report.md と記憶に書く」
  - 推奨（tests\_insufficient の境界の変更であり、追加・分割・統合ではない）。tests\_insufficient を「テストに不足か不備がある」に広げる

    ```yaml
    - id: tests_insufficient
      description: >-
        repo/tests/ のテストに、unit_test 自身が直すべき不足か不備がある。requirements.md の受け入れ基準のうちテストの無いもの、
        実行されない repo/src/ の箇所、lint（ruff の E、F、W）の違反、tasks.yaml のタスクの tests に無いファイル、または
        requirements.md に反する期待のテストである。その箇所が記憶 coverage_gaps と test_report.md の「## 未網羅」に列挙されている。
    ```

    impl\_defect が「その期待が requirements.md に従っている」失敗に限られるので、二つは排他のままである。id と内容がずれるのが気になるなら、id を tests\_inadequate のように改める（シナリオと expectations の直しが要る）
  - 別案（分類体系の変更: end\_state の追加）: tests\_faulty（lint、範囲、誤った期待）を足し、unit\_test に自分自身へ戻す。記憶 test\_issues を memory\_out と memory\_in に足す。下流の振る舞い（unit\_test のやり直し）は tests\_insufficient と同じなので、独立性の上では分ける理由が弱い

#### M-3 四つのフェーズゲートの不合格が必ず unknown に落ち、その意図が書かれていない

- 場所: 各フェーズの goal（第12〜24行、第91〜103行、第179〜203行、第420〜436行）。README の構成の表（assurance についてだけ「ゲートの不合格もこれで戻る」とある）
- 問題: 最終ステージの end\_state は、どれも goal の時に空になる記憶を証拠にする（needs\_unclear は intake\_questions、design\_incomplete は design\_issues、impl\_defect と tests\_insufficient は failing\_tests と coverage\_gaps、notes\_incomplete は missing\_notes）。だからゲートで選ばれることは無く、ゲートの不合格はすべて unknown になる。この選択は adopting.md 2.4 の注意（「記憶 X が空でないこと」を証拠にしたクラスにはフェーズ全体の条件を書かない）に沿っていて、誤りではない。ただ、workflow.yaml にも README にも意図として書かれていない。さらに、四つのゲートの指標はステージの goal がすでに保証している。強制通過（goal 到達扱いで続行）の後にしか落ちない

  | ゲート | 指標をすでに保証しているもの | ステージの goal に無い定性の条件 |
  | --- | --- | --- |
  | discovery | files\_nonempty は intake の unanswered\_questions（質問が無ければ測れない）と analyze の requirement\_count。requirements\_with\_criteria は analyze の同じ指標 | intake.md の回答がすべて要件か受け入れ基準に反映されている |
  | architecture | design\_covers\_requirements は design の、tasks\_cover\_requirements は plan\_tasks の同じ指標（plan\_tasks は design.md と requirements.md を変えない） | design.md の構成とタスクが対応する（構成の各要素にタスクがある） |
  | construction | build\_passes と lint\_errors（src）は implement、tests\_pass、line\_coverage、lint\_errors（tests）は unit\_test。out\_of\_scope\_changes は implement（paths）と unit\_test（tests）の和で足りる | 無い（二つのステージの goal の連言） |
  | delivery | changelog\_covers\_requirements と version\_bumped は release。tests\_pass は construction 以後 repo/ を誰も書かないので保たれる | 「review.json の結果に合い」（何と何が合うのかが曖昧。L-9） |

- 書き換え案（分類体系の変更なし。文書で明示する）: README に節を足す。案

  > ## フェーズゲートの落ち方
  >
  > end\_state でゲートの不合格を戻すのは assurance だけで、ゲートが changes\_requested を選ぶと implement に戻る（review は修正を要しない指摘も review\_findings に書く）。discovery、architecture、construction、delivery の最終ステージの end\_state は、goal の時には空になる記憶を証拠にするので、ゲートでは選ばれない。これらのゲートの不合格は unknown になり、人に戻る。四つのゲートの指標はステージの goal ですでに満たされていて、goal 到達扱いで続行した後にだけ落ちる。ゲートに固有の定性の条件は、discovery の「回答の反映」、architecture の「構成とタスクの対応」、delivery の「review.json との整合」である。

  あわせて、各フェーズの description に「ゲートの不合格は unknown（人に戻す）」と一言書くとよい。自動で戻したいなら、analyze と plan\_tasks に自分自身へ戻る end\_state を足すことになる（分類体系の変更。goal の時にも中身を持つ記憶が要る）。推奨はしない

#### M-4 review.json に査読したパスの記録が無く、review の goal の条件が観測できない

- 場所: review の description（第379〜383行）と goal（第389〜390行）
- 問題: goal は「review.json に、tasks.yaml のタスクの paths と tests の変更を見た結果があり」を求める。しかし review.json の形（`{"findings": [...]}`）は指摘だけを持つ。指摘の無いパスを見たかどうかは書かれない。goal の代表 tests/fixtures/review/ok/review.json の指摘は repo/src/shopcart/discount.py の一件だけで、cart.py と test\_discount.py を見たことは状態文書から分からない。厳密に読む分類器は goal を選べず、ほかのクラスにも当たらないので unknown になりうる
- 書き換え案（分類体系の変更なし）: review.json の形に査読したパスを足す

  ```yaml
  # review の description
  … review.json は {"reviewed": [パス], "findings": [{"path": パス, "blocking": 修正を要するか, "comment": 指摘}]} の形で、
  reviewed に見たファイルをすべて挙げる。…
  # review の goal
  qualitative: >-
    review.json の reviewed が tasks.yaml のタスクの paths と tests をすべて含み、修正を要する指摘が一つも無い。
  ```

  指標にもできる（例: reviewed\_task\_paths、tasks.yaml の paths と tests のうち reviewed にあるものの割合、min 1.0）。フィクスチャの review.json にも reviewed を足す

#### M-5 テストへの修正を要する指摘が unknown に落ち、unit\_test はレビューの指摘を受け取らない

- 場所: review の changes\_requested（第401〜405行）、unit\_test の memory\_in（第270行）
- 問題: review は「tasks.yaml のタスクの paths と tests の変更」を見る。しかし changes\_requested は「すべて repo/src/ の修正で解消する」指摘に限られる。repo/tests/ の修正で解消する修正要の指摘（テストが受け入れ基準を確かめていない、など）は、changes\_requested にも design\_flaw にも当たらず unknown になる。implement へ戻せば repo/tests/ も捨てられて unit\_test が書き直すので、戻り先は implement でよい。ただ、unit\_test は review\_findings を受け取らないので、書き直す unit\_test に指摘が届かない
- 書き換え案（changes\_requested の境界の変更であり、追加・分割・統合ではない）:
  - changes\_requested の第一文を「review.json に修正を要する指摘が一つ以上あり、そのすべてが repo/src/ か repo/tests/ の修正で解消する（design.md は変えなくてよい）」にする（M-6 と合わせる）
  - 指摘を unit\_test に届ける経路は、implement が書き unit\_test が読むファイル impl\_notes.md を使う。implement の description に「持ち帰った review\_findings のうち repo/tests/ に関するものを、impl\_notes.md の『## テストへの依頼』に書き写す」、unit\_test の description に「impl\_notes.md の『## テストへの依頼』があれば、それに応えるテストを書く」と書く。unit\_test の goal に「impl\_notes.md の『## テストへの依頼』のすべてに応えるテストがある」を足せば、unit\_test の投影の中で観測できる
  - unit\_test の memory\_in に review\_findings を足す案は採れない。複製の上で試すと、整合性検査が `memory_unsupplied`（memory\_in の項目を carry も前のステージも生成しない）で拒んだ。review\_findings は後ろの review が生成し、carry は implement にしか運ばないためである

#### M-6 changes\_requested は修正を要する指摘が無くても成り立ち、ステージでもゲートでも goal と重なりうる

- 場所: review の changes\_requested（第401〜405行）
- 問題: 第一文「review.json の修正を要する指摘が、すべて repo/src/ の修正で解消する」は、修正を要する指摘が無い時にも（空の全称として）成り立つ。ステージの評価で修正要の指摘が無いと、goal と changes\_requested の両方に当たる文になる。ゲートの評価（修正要の指摘は必ず無い）では、goal の時にも中身を持つ review\_findings があるので、「その指摘が review\_findings に列挙されている」まで成り立つ。第二文（フェーズ assurance の評価での条件）が本来の境界なのに、第一文だけで changes\_requested を選ぶ読みが残る
- 書き換え案（分類体系の変更なし）:

  ```yaml
  - id: changes_requested
    description: >-
      review.json に修正を要する指摘が一つ以上あり、そのすべてが repo/src/ の修正で解消する（design.md は変えなくてよい）。その指摘が
      記憶 review_findings に列挙されている。フェーズ assurance の評価では、修正を要する指摘が無くても、修正を要しない指摘が
      verification.md の結果と合わせると repo/src/ を直してからリリースすべきもので、その指摘が review_findings に列挙されて
      いれば、この状態とする。
  ```

  M-5 を採るなら「repo/src/」を「repo/src/ か repo/tests/」にする

#### M-7 要件の id の照合が、日本語の文に続く id を数えない

- 場所: metrics.py の `_mentioned`（第300〜301行）。使う指標は design\_covers\_requirements（design の goal と architecture のゲート）と changelog\_covers\_requirements（release の goal と delivery のゲート）
- 問題: `\bREQ-1\b` は、id の直後に仮名か漢字が続くと一致しない（実験 2）。design の description は「## 対応」の行の形を決めていない（「## 要件」は「- REQ-n: 要件」と決めている）。だから「REQ-1は Discount.apply の…」のような自然な書き方で割合が下がり、goal が選択肢から外れる。design の requirements\_gap は requirement\_gaps の列挙を、release の notes\_incomplete は missing\_notes の列挙を証拠にする。本体は割り当てたつもりなので列挙せず、unknown になる
- 書き換え案（分類体系の変更なし）: 照合を `(?<![A-Za-z0-9_-])REQ-1(?![0-9])` のように ASCII の境界だけで切る。あわせて design の description に「## 対応」の行の形（「- REQ-n: 受け持つ構成要素」）を、release の description に CHANGELOG.md の行の書き方を書く

#### M-8 クラスの代表のフィクスチャが記述と合わない

- 場所: tests/fixtures/acceptance/unmet/verification.md、tests/fixtures/plan\_tasks/unknown/tasks.yaml
- 問題:
  - acceptance/unmet は REQ-2 を不合格にし、内容を「小計 1200 円に OFF500 を二回続けて適用すると、二回目も割り引かれる（コードは一回の支払いに一回）」とする。REQ-2 の要件と受け入れ基準（1000 円に OFF500 で 500 円、300 円に OFF500 で 0 円）のどれにも反していない。requirement\_unmet の「受け入れ基準に反する repo/ の振る舞い」に当たらず、記述の上では要件の欠落（requirement\_misread）か unknown である。ソフトウェア開発としても、「一回の支払いに一回」は requirements.md に無い要件で、要件分析へ戻すべき不足である
  - plan\_tasks/unknown は、全要件を扱う一つのタスク（title「全部やる」）で、paths は構成のファイルに収まり、paths の重なりも無い。H-2 の点を除けば goal の文を満たし、unknown の代表になっていない
  - 例のテストは印を読む分類器を使うので、この食い違いを捕まえない。人手のラベルや分類器の検証のコーパスに使うと、ラベルが記述と食い違う
- 書き換え案（分類体系の変更なし）:
  - acceptance/unmet の不合格を、要件の記述に反する振る舞いにする。この例には自然な候補がある。implement の ok と ok\_b（支払額を切り捨てる系統）は REQ-1 の「割引額の 1 円未満は切り捨てる」に反し、小計 333 円に PCT10 で 299 円を返す（REQ-1 では 300 円）。unit\_test/ok のテストはこの場合を確かめないので通り、acceptance で初めて見つかる。これを「REQ-1: 小計 333 円に PCT10 で 299 円（割引額 33.3 円を切り捨てると 300 円）」とする。あわせて requirement\_unmet の「受け入れ基準に反する repo/ の振る舞い」を「要件の記述か受け入れ基準に反する repo/ の振る舞い」にする（impl\_defect の「受け入れ基準か要件の記述に従っている」と揃う。境界の変更）
  - plan\_tasks/unknown は、goal にも design\_incomplete にも当たらない成果物にする（例: 二つのタスクの paths が同じファイルで重なる。全要件は割り当てられているので design\_incomplete にも当たらない）

### 低

#### L-1 analyze の requirement\_count の min 3 は、要件分析の基準として不自然

依頼によっては要件が一つか二つで足りる。その時は goal が選択肢から外れ、needs\_unclear（問いが要る）にも当たらず unknown になる。この依頼では四つになるので動くが、手本として読む人は誤解する。min 1 にするか、README に「この依頼に合わせた値」と書く。

#### L-2 持ち帰った記憶への対応が、戻り先の goal で観測できず、連鎖で失われる

- intake は持ち帰った intake\_questions を尋ねるが、memory\_in は状態文書に入らない。尋ねたかを goal で判定できない。intake.md に「## 持ち帰った問い」の節を設け、goal に「その節の問いにすべて回答がある」を足すと観測できる
- acceptance → analyze（requirement\_gaps）→ needs\_unclear → intake → analyze と連鎖すると、intake の開始時スナップショットには requirement\_gaps が無いので、再び analyze に来た時には消えている。依頼に根拠の無い食い違いは依頼者に尋ねるしかない（analyze の goal は根拠を求める）ので、これが想定の経路である。analyze の description に「持ち帰った食い違いを依頼者に尋ねる時は、その内容を intake\_questions に含める」と書いておくとよい

#### L-3 quality\_violation の「paths に無いファイルを変えている」は差で、分類器には見えない。paths が狭すぎる場合の行き先も決まっていない

分類器は repo/src/ の今の内容しか見ず、どれが変わったかは分からない（既存の \_\_init\_\_.py はどのタスクの paths にも無い）。指標と impl\_violations が頼りなので、記述は「…変更の範囲の違反が記憶 impl\_violations に列挙されている」を主にする書き方がよい。また、tasks.yaml の paths が狭すぎて実装できない時は、implement 自身へ戻しても直らない。description に「paths の外のファイルを変えないと実装できない時は、変えずに task\_questions に書く（task\_unclear）」と書く。

#### L-4 blocking\_findings が真偽値でない blocking を数える

`if f["blocking"]` は文字列の `"false"` も修正要と数える。真偽値でなければ MetricError にする。

#### L-5 changelog\_covers\_requirements は CHANGELOG.md のどこに id があっても数える

「未対応: REQ-3」のような行でも REQ-3 を載せたと数える。最新の版の見出しの下だけを数えるか、description に書き方を決める。

#### L-6 release がパッケージの版を上げず、版を上げ忘れると unknown になる

release は repo/ を書かないので、リリースした repo/src/shopcart/\_\_init\_\_.py の \_\_version\_\_ は古い版のままで、release.json の版と食い違う。実際のリリースとしては不自然である。release.json を「リリースの記録」として版の更新を範囲外にするなら、README に書く。含めるなら、release の writes に \_\_init\_\_.py を足し、version\_bumped を view.baseline() と比べる形にする。また、版を上げていない状態は notes\_incomplete に当たらず unknown になる。自分で直せる不足なので、notes\_incomplete の記述に含めてもよい（境界の変更）。

#### L-7 design が全要件を割り当てたうえで問いを残すと unknown になる

暫定の解釈で割り当て、「## 要件への問い」にも書くのは自然な振る舞いである。goal（問いが無い）にも requirements\_gap（割り当てていない）にも当たらない。requirements\_gap を「割り当てていないか、割り当てたが『## 要件への問い』に問いがある」に広げ、「goal に優先する」を書く（境界の変更）。

#### L-8 戻りで成果物が捨てられることを前提にした書き方が無い

- impl\_defect → implement は implement の開始時スナップショットを復元するので、欠陥を見つけたテストも捨てられる。unit\_test は failing\_tests を受け取らないので、書き直す unit\_test はそのテストを回帰テストとして書き直せない。unit\_test の memory\_in に failing\_tests を足す案は、整合性検査が `memory_unsupplied` で拒む（複製の上で確かめた。failing\_tests は unit\_test 自身の memory\_out で、carry は implement にしか運ばない）。M-5 と同じく、implement が「持ち帰った failing\_tests のテストを impl\_notes.md の『## テストへの依頼』に書き写す」形にする
- review や acceptance から implement へ戻ると、implement は実装前のコードから書き直す。持ち帰る記憶（review\_findings、unmet\_requirements、failing\_tests）は、捨てられるコードの行番号ではなく、パス、関数、期待する振る舞いで書くべきである。また implement の開始時スナップショットには、前の carry の記憶も残っている。コードを一から書き直すので、古い指摘もまだ有効である。これらを README か各 description に書いておくと、本体を作る人が誤解しない

#### L-9 冗長な指標と曖昧な文

acceptance の tests\_pass は unit\_test の goal と construction のゲートが保証しており、強制通過の後にしか落ちない。delivery の goal の「review.json の結果に合い」は、何と何が合うのか分からない（修正要の指摘が残っていない、のことなら assurance のゲートがすでに保証している）。construction の goal の「repo/ の変更全体」は分類器には見えず、out\_of\_scope\_changes だけが判定する。

## 計画役へ上げる事項

- 書かなかった memory\_out の項目が、開始時スナップショットの値（carry で持ち帰った値を含む）のまま状態文書に出ることは、公開の文書から導けるが、どこにも明記されていない（H-1）。adopting.md 2.1 か第5節に「memory\_out の項目は訪問のたびに必ず書く（無ければ空の値）。書かなければ前の値が状態文書に出る」を足すとよい。toy-minimal の記述も同じ観点で見直す価値がある（この検証では見ていない）

## 触ったファイル

- 書いた: reports/f4-workflow-review.md（このファイル）
- 元の作業ツリーでは、ほかのファイルを変えていない。テストも実験も走らせていない。git 操作はしていない
- 副作用: スクラッチパッドにリポジトリの複製を作り（git clone）、その中に .venv を作った。整合性検査、例のテスト、三つの実験はその複製の上で行った。実験のスクリプトと workflow.yaml の写しはスクラッチパッドの exp/ にある

## 利用者への指摘（公開の文書の語だけで）

この節は、workflow.yaml、adopting.md、契約（contract/contract.md）、スキーマの語だけで書いている。

### 高

**1. implement と design の記憶が、持ち帰った古い値のまま分類器に見える**

- 記憶はスナップショットに含まれる（契約 5）。carry で重ねた記憶は戻り先の開始時スナップショットに入り（契約 2.3）、その後のステージにも残る（スキーマの memory\_in の説明「前のステージの memory\_out」）。ステージが memory\_out の項目を書かなければ、状態文書（契約 2.4）の記憶の欄にはその残った値が出る
- implement の description は「タスクの記述が曖昧で実装を決められない時は、その問いを記憶 task\_questions に書いて」としか書いていない。task\_unclear で plan\_tasks に戻ると、次の implement の開始時スナップショットには前の問いが入っている。問いが解けて実装した訪問で task\_questions を書かないと、状態文書に前の問いが出る。task\_unclear の「task\_questions に問いが列挙されていればこの状態とし、goal と quality\_violation に優先する」が記憶だけで成り立ち、task\_unclear に分類されうる。この辺は max 1 なので、そこで escalate（max\_exceeded）になる。参照ランタイムで、前の問いが状態文書に出ることを確かめた
- 同じことが、implement の impl\_violations（quality\_violation で自分自身に戻った後。その後に implement へ戻るたびにも入る）と、design の requirement\_gaps（requirements\_gap か acceptance の requirement\_misread で analyze へ戻った後）で起きる。analyze、plan\_tasks、unit\_test、acceptance、review、release の記憶は「無ければ空の一覧」と書かれているので起きない
- 直し方: implement の task\_questions と impl\_violations、design の requirement\_gaps にも「（無ければ空の一覧）」を書く。task\_unclear の優先の条件を「記憶 task\_questions と impl\_notes.md の『## 問い』の両方に問いが列挙されていれば」にする。impl\_notes.md は implement の writes で、implement の開始時スナップショットには無い（戻りはそのステージかそれより前の開始時スナップショットを復元する）ので、古い値が出ない。偽のステージ本体が記憶を毎回書き、MarkerClassifier が記憶を読まないと、テストではこの問題が見えない

**2. plan\_tasks の goal が、代表の成果物で満たせない**

- plan\_tasks の goal は「各タスクの paths と tests が design.md の『## 構成』のファイルに収まり」を求める。design の「## 構成」は「変えるファイルと役割」で、goal の代表の design.md も repo/src/ のファイルしか挙げていない。一方、代表の tasks.yaml の tests は repo/tests/test\_discount.py である。分類器は記述そのものを選択肢として読む（契約 2.2）ので、goal を選べない。design\_incomplete（タスクにすべての要件を割り当てられない）にも当たらず、unknown になる
- 直し方: goal を「各タスクの paths が design.md の『## 構成』のファイルに収まり、tests が repo/tests/ の下にあり、タスクどうしで paths が重ならない」にする

### 中

**3. implement で指標が落ちた時に当たる end\_state が無い所がある**

- 既存のテスト（tests\_pass）が落ちた時と、repo/src/ の変更が design.md の構成から外れた時は、どの end\_state にも当たらず unknown になる
- quality\_violation は「違反の内容が記憶 impl\_violations と impl\_notes.md の『## 違反』に列挙されている」を条件にする。分類器は指標の値を見ない（契約 2.4 の状態文書はファイルと memory\_out だけ）。本体が違反に気づかずに指標だけが落ちた場合は unknown になる。選ばれても carry が空になる（adopting.md 2.1「戻り先が直すのに使う情報は、記憶に書かせ、その記憶を証拠として記述に書く」）
- 直し方: description に「終える前に、ビルド、既存のテスト、lint、paths に照らした変更の範囲を自分で確かめ、違反を記憶 impl\_violations と impl\_notes.md の『## 違反』に書く（無ければ空の一覧）」と書く。quality\_violation の列挙に「repo/tests/ の既存のテストを落とす」と「design.md の構成から外れている」を足す（既存のクラスの境界を広げる。end\_state の追加ではない）。それでも impl\_violations が空なら unknown になることを、意図として README に書く

**4. unit\_test でテストの側の不備が unknown に落ちる**

- repo/tests/ の lint（lint\_errors）、tasks.yaml の tests の外のファイル（out\_of\_scope\_changes）、要件に反する期待のテストは、impl\_defect にも tests\_insufficient にも当たらない。tests\_insufficient の「行カバレッジが 80% に届かない」は、指標の値を見ない分類器には判定できない
- 直し方: description に、終える前に pytest、行カバレッジ、lint、範囲を自分で確かめて記憶に書くことを足す。tests\_insufficient を「unit\_test 自身が直すべき不足か不備がある（テストの無い受け入れ基準、実行されない箇所、lint の違反、tests に無いファイル、要件に反する期待）」に広げる（境界の変更）。別案として、テストの不備の end\_state を足して unit\_test 自身に戻す方法もあるが、これは分類体系の変更（end\_state の追加）になる

**5. 四つのフェーズゲートの不合格が unknown に落ちることが書かれていない**

- discovery、architecture、construction、delivery の最終ステージの end\_state は、goal の時には空になる記憶を証拠にするので、ゲートでは選ばれない。ゲートの不合格はすべて unknown になる。adopting.md 2.4 の注意に沿った選択だが、workflow.yaml にも README にも書かれていない。四つのゲートの指標は、ステージの goal がすでに満たしていて、goal 到達扱いで続行した後にだけ落ちる
- 直し方: README に「フェーズゲートの落ち方」を書く。end\_state で戻すのは assurance だけ（changes\_requested）であること、ほかの四つは unknown で人に戻ること、ゲートに固有の定性の条件（discovery の回答の反映、architecture の構成とタスクの対応、delivery の review.json との整合）を明記する

**6. review の goal の「paths と tests の変更を見た結果があり」が観測できない**

- review.json は指摘だけを持ち、指摘の無いパスを見たかは書かれない。代表の review.json は一つのファイルへの指摘だけである
- 直し方: review.json の形を `{"reviewed": [パス], "findings": [...]}` にし、goal を「reviewed が tasks.yaml の paths と tests をすべて含み、修正を要する指摘が一つも無い」にする。指標にしてもよい

**7. テストへの修正を要する指摘が unknown に落ちる**

- changes\_requested は repo/src/ の修正で解消する指摘に限られる。review は tests の変更も見るのに、repo/tests/ の修正で解消する指摘はどこにも当たらない。unit\_test は review\_findings を受け取らないので、implement に戻って unit\_test が書き直す時にも指摘が届かない
- 直し方: changes\_requested を「repo/src/ か repo/tests/ の修正で解消する」に広げる（境界の変更）。指摘は、implement が書き unit\_test が読む impl\_notes.md で渡す。implement は持ち帰った review\_findings のうちテストに関するもの（と failing\_tests のテスト）を impl\_notes.md の「## テストへの依頼」に書き写し、unit\_test はそれに応えるテストを書く。unit\_test の memory\_in に review\_findings や failing\_tests を足す方法は、整合性検査が拒む（memory\_in の項目を、carry も前のステージも生成しないため）

**8. changes\_requested が、修正を要する指摘が無くても成り立つ**

- 「修正を要する指摘が、すべて repo/src/ の修正で解消する」は、修正を要する指摘が無い時にも成り立つ。ステージでもゲートでも goal と重なる読みが残る
- 直し方: 「review.json に修正を要する指摘が一つ以上あり、そのすべてが…」にし、ゲートの条件は「フェーズ assurance の評価では、修正を要する指摘が無くても…」と書き分ける

**9. 要件の id の照合が、日本語の文に続く id を数えない**

- design\_covers\_requirements と changelog\_covers\_requirements の実装は、「REQ-1は」「REQ-1の」「REQ-1と」の REQ-1 を数えない。design の description は「## 対応」の行の形を決めていないので、自然な書き方で goal が選択肢から外れる。本体は割り当てたつもりなので記憶に列挙せず、unknown になる
- 直し方: 照合を英数字の境界だけで切る（例 `(?<![A-Za-z0-9_-])REQ-1(?![0-9])`）。design と release の description に行の書き方を決める

**10. クラスの代表の成果物（フィクスチャ）が記述と合わない**

- requirement\_unmet の代表の verification.md は、REQ-2 の要件にも受け入れ基準にも無い振る舞い（コードは一回の支払いに一回）を不合格にしている。記述の上では要件の欠落（requirement\_misread）か unknown である。plan\_tasks の unknown の代表の tasks.yaml は、記述の上では goal を満たす
- MarkerClassifier は成果物の印を読むので、テストはこの食い違いを捕まえない。分類器の検証（adopting.md 第15節）のラベルに使うと、ラベルが記述と食い違う
- 直し方: requirement\_unmet の代表を、要件の記述に反する振る舞いにする。たとえば支払額を切り捨てる実装は REQ-1（割引額の 1 円未満は切り捨てる）に反し、小計 333 円に PCT10 で 299 円を返すが、単体テストがこの場合を確かめなければ acceptance で初めて見つかる。あわせて requirement\_unmet の「受け入れ基準に反する」を「要件の記述か受け入れ基準に反する」に広げる。plan\_tasks の unknown の代表を、goal にも design\_incomplete にも当たらない成果物（例: タスクどうしで paths が重なる）にする
