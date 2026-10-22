# adopting.md の不足の記録（software-factory）

software-factory を作る途中で、docs/adopting.md（と、それが指す公開 API の文書、examples/toy-minimal/）だけでは判断できなかったこと、足りなかったこと、回避したくなったことの記録。最初の版（30 項目、A1〜F2）を受けてフレームワークの側が直したので往復 1 で確かめ直し、そこで見つけた N1〜N7 を往復 2 で、往復 2 で見つけた N8、N9 を往復 3 で、往復 3 で見つけた N10 を往復 4 で、往復 4 で見つけた N11 を往復 5 で確かめ直した。往復 6 では、検証役による workflow.yaml の事前レビューと基準の確認の指摘（docs/review-findings.md）に対応し、そこで分かった不足を N12 に書いた。往復 7 で N12 を確かめた。往復 8 では、完了判定の指摘（review-findings.md の E）に対応し、そこで分かった不足を N13 に書いた。往復 9 で N13 を確かめた。往復 10 では、人間のレビューの回答と完了判定の二回目の指摘（review-findings.md の F）に対応し、そこで分かった不足を N14、N15 に書いた。往復 11 では、人間の決定（review-findings.md の G）に対応し、N14、N15 を確かめ（どちらも解消）、そこで分かった不足を N16 に書いた。往復 12 では、N16 を受けて書き足された手引き第15.1節の目安で N16 を確かめ（解消）、この例の人に渡す材料の選び方をその目安に合わせ、そこで分かった不足を N17 に書いた。往復 13 では、N17 を受けて改められた第15.1節の三つの目安の文で N17 を確かめ（解消）、この例の人に渡す材料の選び方を改められた目安に合わせた。往復 13 で新しい不足は無かった。往復 14 では、往復 10〜13 の差分の確かめ（review-findings.md の H）に対応し、そこで分かった不足を N18 に書いた。往復 15 では、N18 を受けて足された `ScenarioResult.store` と api-reference.md の説明、手引き第15.1節の一文で N18 を確かめ（解消）、この例の回避（シナリオの台本の偽物でランタイムを組み立て直すこと）を外した。往復 15 で新しい不足は無かった。往復 16 では、人に渡す材料の確かめ直し（review-findings.md の I）に対応し、そこで分かった不足を N19 に書いた。

読んだのは adopting.md、api.md、api-reference.md、examples/toy-minimal/、schema/workflow.schema.json、contract/ の文書と形式（contract.md、README.md、conformance/ の下のすべて、formats/ と trace と snapshot の schema）だけ。往復 2 と往復 3 では、これらの文書の変更を git の差分で見た（読んでよい文書に限る。往復 3 はコミット前の作業ツリーとの差分）。往復 11 でも、往復 10 の前（08f79b4）からの adopting.md、changelog.md、contract/ の差分を見た。往復 12 では、056374f の adopting.md と changelog.md の差分（第15.1節の 1 の下の三つの目安、2 の `item.source` の文、changelog.md の「未公開」の最後の項目）を見た。往復 13 では、3b28deb の adopting.md と changelog.md の差分（第15.1節の 1 の下の三つの目安の文、changelog.md の「未公開」の最後の項目）を見た。往復 14 では、85c7ed5 から今までの adopting.md と changelog.md の差分（第15.1節の 1 と 2、changelog.md の「未公開」の第15.1節の項目）を見て、contract/conformance/README.md の「シナリオの実行のしかた」と「偽物」を読み直した。往復 15 では、453fd31 の adopting.md、api-reference.md、changelog.md の差分（第15.1節の 1 の一文、`ScenarioResult`、`ScriptedBody`、`ScriptedClassifier` の説明、changelog.md の「未公開」の `ScenarioResult.store` の項目）を見た（そのコミットが変えたファイルの名前の一覧（`git show --stat`）には読まないファイルの名前も出たが、それらの差分は開いていない）。往復 16 では、227c72e の adopting.md と changelog.md の差分（第15.1節の 2、changelog.md の「未公開」の第15.1節の項目）を見た（同じく、名前の一覧に出た decisions.md の差分は開いていない）。フレームワーク本体の実装（src/、tests/、scripts/、pyproject.toml、conftest.py の中身を含む）、plan.md、progress.md、decisions.md、reports/ は読んでいない。本体について知ったことは、公開の名前の signature と docstring、`scripts/check.sh` と本体のテスト（tests/test\_package.py だけ）を実行した時の出力、cProfile の出力（関数の名前と時間）、例外の traceback（往復 14。`ScriptedClassifier` と `ScriptedOperator` の例外に、本体のファイル名、行番号、その行の文が出た。ファイルは開いていない）からだけ。本体は直していない。回避策はこの例の中にだけ置いた。

## 未解消

- **N19 人に渡す材料を対象の順に分ける時、ゲートの項目を順のどこに置くかが手引きから一つに決まらない**（往復 16。docs/review-findings.md の I-M2 に対応して見つけた）
  - 手引き第15.1節の 2 は、「後の対象とゲートの状態文書は、前のステージの goal の成果物を含む」ので「対象の順に分けて渡し」、「ステージの項目だけでなく、ゲートの項目も含める」と書く。ゲートの状態文書はフェーズの全体で、ゲートの訪問はフェーズの最終ステージの訪問と同じ（第15.1節の「訪問」の目安）なので、ゲートの項目は、そのフェーズのステージの項目と同じ所にも、別の所にも置ける。置き場によって漏れ方が変わるのに、手引きはどこに置くかも、置き場で何が漏れるかも書かない。第三者の検証役も、(a)「そのフェーズの最終ステージより前に置く」か (c)「別のファイルにして最後に回す」を例に挙げた（手引きの文からではなく、review-findings.md の I-M2）
  - この例で確かめた事実（tests/test\_labeling.py の test\_earlier\_files\_do\_not\_contain\_what\_later\_targets\_write）: (a) では、ゲートの状態文書が最終ステージの goal の成果物（discovery では analyze の requirements.md、architecture では plan\_tasks の tasks.yaml）を含み、最終ステージを付ける前に見える。(c) では、後のフェーズの対象の状態文書がゲートの状態文書のファイルをすべて含み（acceptance は discovery のゲートの feature\_request.md、intake.md、requirements.md を、implement は architecture のゲートのファイルをすべて含む）、ゲートを通った（goal だった）状態文書が、ゲートを付ける前に見える。(b)「そのフェーズの最終ステージの直後」だけが、どちらも付けた後でしか見えない。(a) と (c) の並びでは、このテストと、ファイルの順を確かめるテストが落ちる（スクラッチで確かめた）
  - 手引きの文から読めること: 「後の対象とゲートの状態文書は、前のステージの goal の成果物を含む」から、ゲートは自分のフェーズのステージより後に置くと読める（(a) は除ける）。(b) と (c) のどちらかは、後のフェーズの状態文書がゲートを通ったことを見せる、という手引きに無い事実から決めた
  - この例の扱い（回避ではなく、選んだ規則として記録した）: (b) を選び、software\_factory/labeling.py の ORDER（workflow.yaml のフェーズとステージの順で、ゲートはそのフェーズの最終ステージの直後）と、README の「記述と代表の整合」に理由を書き、テストで確かめる
  - 提案: 第15.1節の 2 の「対象の順に分けて渡し」に、ゲートはそのフェーズの最終ステージの直後（ワークフローが評価する順）に置くこと、最終ステージより前に置くと最終ステージの goal の成果物を先に見せ、最後に回すと後のフェーズの状態文書がゲートを通ったことを先に見せることを添える

## 解消済み（往復 15）

- **N18 シナリオで分類器が見る状態文書を読む手段と、`ScriptedClassifier` の引数の形が、公開の文書に無い**: 解消。`run_scenario` の結果（`ScenarioResult`）に `store`（実行が使った置き場）が足され、api-reference.md に `ScenarioResult` の属性の説明（store は「分類器が見た状態文書は、trace の evaluation の classification.state（SHA-256）を store.get に渡して読める」）と、`ScriptedBody` の visits、`ScriptedClassifier` の stages と gates の形が書かれた。手引き第15.1節の 1 の「項目にしない時は…記録する」の後に「シナリオの状態文書は、`run_scenario` の結果の `trace` の evaluation の `classification.state`（SHA-256）を `result.store.get(...)` に渡して読める」が足された（changelog.md の「未公開」の「足したもの」の `ScenarioResult.store` の項目）。読んで、試して確かめた: 往復 14 で書いた三つは、どれも足された文で決まる
  - 状態文書を読む手段: シナリオ plan\_tasks\_design\_incomplete\_rollback を `run_scenario`（この例の software\_factory/stages/deterministic.py の run）で実行し、trace の evaluation の 16 件の `classification.state` をすべて `result.store.get` で読めた（読んだ文の SHA-256 が digest と一致する）。中断して再開するシナリオ happy\_path\_user\_suspend（再開 1 回）でも、再開をまたいだ trace の 14 件をすべて読め、seq は重ならない。往復 14 で書いた「中断するシナリオでは再開（手順 4）も自分で書くことになる」は無くなった
  - `verify` に渡す store: api-reference.md の `verify` の項は store がどれかを名指さないが、置き場は `result.store` のほかに無く、`verify(scenario, result, result.store)` は二つのシナリオで空（`result.problems` と同じ）だった。期待との食い違いは手引き第8節のとおり `problems` で見れば足り、この例は `verify` を使わない
  - 引数の形: `ScriptedClassifier` の stages は「シナリオの visits の各項目の classify の値だけを集めたもの」、gates は「シナリオの gates そのもの」、`ScriptedBody` の visits は「シナリオの visits そのもの」と書かれ、往復 14 に試して知った形と同じ。この例は回避を外したので、どれももう直接は使わない
  - 回避を外した（software\_factory/labeling.py の scenario\_corpus）: シナリオを `run_scenario` で実行し、`problems` が空であることを確かめ、`RunRecord(scenario.seed, result.status, result.trace)` を `build_corpus(RunSet([...]), result.store, workflow, unique_states=True)` にかける。シナリオの台本の偽物（`ScriptedBody`、`ScriptedClassifier`、`ScriptedOperator`、`ScriptedUser`）と自分の置き場でランタイムを組み立て直すこと、`record_run`、実行記録の要約をシナリオの期待と自分で比べることが要らなくなった
  - 選んだ手順（不足には数えない）: 第15.1節が書くのはシナリオの状態文書を読む手段で、この例はシナリオの状態文書をコーパスの項目にする（往復 14 の H-L4）。そのために trace を `RunRecord` にして `build_corpus` に渡した。api-reference.md の `RunRecord(seed, status, events, representatives)`（引数と属性が公開）、`ScenarioResult.trace`（実行記録の出来事。再開をまたいで続けたもの）、`build_corpus`（実行記録の各評価から、置き場の状態文書と選択肢の項目を作る）から判断できた。試して知った小さなこと: representatives を渡さずに作った `RunRecord` の `run_id` は、往復 14 の回避（`record_run`）の実行記録のものと同じ（46612a644073df0b）で、16 項目の id、scope、対象、選択肢、状態文書、source（seq と種）が回避の出力とすべて同じだった
  - 材料: 変わらない。置き換えた後のコードで試しの実行から作り直した docs/human-labeling.md と docs/human-labeling.corpus.jsonl は、コミットしたもの（往復 14 の回避で作った）とバイト単位で同じ（スクラッチに書いて比べた。コミットしたファイルは書き直していない）。tests/test\_labeling.py の test\_material\_is\_regenerated\_from\_the\_trial\_runs が、作り直した項目と材料の文がコミットしたものと同じことを確かめ、置き換えた後のコードで通る。test\_scenario\_only\_representative\_is\_the\_state\_the\_classifier\_sees を、項目の状態文書が `run_scenario` の trace の evaluation の `classification.state` を `result.store.get` で読んだものと文として同じこと（前は SHA-256 が実行記録にあることだけ）と、scenario\_corpus の全項目が、評価ごとにそう読んだ状態文書と同じことを確かめる形にした
  - 小さなこと（不足に数えない）: api-reference.md の `ScenarioResult` の属性の説明に `problems` が無い（signature にはあり、意味は手引き第8節の「結果の `problems` が空なら期待どおり」にある）。`ScenarioResult` の signature で `store` は `resumes` の前に入った（位置引数で `ScenarioResult` を作るコードは変わるが、changelog.md は「足したもの」に書く。利用者が作るものではなく、この例も作らない）

## 解消済み（往復 13）

- **N17 変えた所に絞る目安の三つ（対象、訪問、まとめ方）の、組み合わせ方と範囲が読み手に任される**: 解消。adopting.md 第15.1節の 1 の下の三つの目安の文が改められた（changelog.md の「未公開」の最後の項目が「対象は記述が変えた所を根拠にしうるもの、訪問 2 以降は memory\_in を持つステージとそのフェーズのゲート、まとめ方の組に訪問の区分を含める」になった）。読んで確かめた: (a)〜(c) は、それぞれ改められた一つの文で決まる
  - (a) 組み合わせ方: まとめ方の組が (対象, 訪問の区分（1 か 2 以降か）, 印, 上流の違い) になり、訪問の目安に「見出し行のほかは訪問 1 の項目と同じ状態文書は除く」が足された。訪問 2 以降の項目が同じ組の訪問 1 の項目に代えられることも、応答の現れない訪問 2 以降の状態文書が選ばれることも、字のとおりに読んで無くなる。往復 12 のこの例の判断（組に訪問の区分を足し、訪問 1 と同じものを除く）は改められた文と同じ。往復 12 で足した「訪問 2 以降は持ち帰った問いの回答を含むものを先に選ぶ」は目安に無いので外し、目安の字のとおり（組ごとに短いもの）にした。試しのコーパスで、外す前と後の選び方が同じ項目を選ぶことを確かめた（往復 12 の試しの実行で 45 項目、往復 13 の試しの実行で 49 項目とも同じ。訪問 1 と同じものを除いた後に残る訪問 2 以降の候補 34 項目は、どれも持ち帰った問いの回答を含む）
  - (b) 訪問の目安の範囲: 「訪問 2 以降も渡すのは、memory\_in を持つステージ（持ち帰った記憶を受けて成果物が変わる）と、そのステージを含むフェーズのゲートだけ」で決まる。往復 12 のこの例の読み方（software\_factory/labeling.py の receives\_carry。workflow.yaml の memory\_in から決める）と同じで、acceptance は訪問 1 だけ。往復 13 で対象に足した review も memory\_in が無いので訪問 1 だけ。README と labeling.py に残っていた、手引きに無い条件（記述が持ち帰った記憶の扱いを書く）と、改める前の手引きの文の引用を、改められた文に合わせた（どれも選ぶ項目は変えない）
  - (c) 対象の目安の範囲: 「記述（ステージの goal と end\_state、フェーズの goal）が、変えた所（直した節、要件、回答など。成果物の全体ではない）を判断の根拠にしうる対象」と「変えた成果物を読むだけで、記述が変えた所に触れない対象は渡さなくてよい」で決まる。成果物の全体ではなく変えた所で見るので、REQ-3 の受け入れ基準と振る舞いに照らす unit\_test と construction のゲート、「## 構成」で判断する implement は渡さない（往復 12 の判断のまま）。unit\_test の impl\_defect と tests\_insufficient の記述は「要件の記述」「要件に反する期待」に触れるので、「しうる」で確かめ直した。変えたのは REQ-3 の誰がどこで入力するかの句で、テストの期待はそれを確かめも否定もできないので、判断の根拠にはならない
  - 改められた文に当てはめると、この例の選び方は対象の一か所で合っていなかった。review の design\_flaw と changes\_requested の境界は、修正を要する指摘が design.md の構成かインターフェースを変えなければ解消しないかで決まり、design.md の「## 対応」の REQ-3 に足した句（コードを文字列で受け取る、画面は repo/ の外）はインターフェースと境界を述べるので、判断の根拠にしうる。往復 12 は「review は design.md の構成とインターフェースを指摘を分ける時だけ使い、「## 対応」に触れない」として外したが、記述は節を名指しておらず、design\_flaw の代表の指摘（割引の種類を Discount の分岐で表している）も「## 対応」にある内容を根拠にする。往復 12 の外した理由は節で分けたもので、記述の字に合っていなかった（手引きの不足ではなく、この例の判断の誤り）。review を対象に足した（記述は変えていない）
  - 材料を作り直した: 試しの分布 labeling の review の訪問 1 に四つのクラスを置き（ok 0.4、changes、design\_flaw、unknown 0.2 ずつ。前は ok だけ）、回数 240 と種 90000 は変えていない。49 項目（訪問 1 が 37、訪問 2 以降が 12。往復 12 の 45 項目に review の 4 を足した。往復 12 の 45 項目の状態文書はすべて残り、試しの実行が変わったので 12 項目の id が変わった）。人のラベルはまだ無かった（docs/human-labels.jsonl が無く、「ラベル:」はすべて空）ので、付け直す範囲の問題は無い
  - 目安の「など」のうちでこの例が選んだ規則（手引きの「選んだ規則を記録する」のとおり README の「記述と代表の整合」と labeling.py に記録した。不足には数えない）: 変えた所を、節や要件より細かい句で区切った（REQ-3 なら誰がどこで入力するかの句。REQ-3 を一つの変えた所とすると、要件の記述に照らす unit\_test も対象になる）。review の上流の違いは無しとした（intake.md を読まず、goal の実装の変種は review.json の代表と変えた句に関わらない）。訪問の目安の「訪問 1 の項目と同じ」は、コーパスの訪問 1 の項目と比べた（選んだ訪問 1 の項目と比べても、この例では除く項目が同じ）

## 解消済み（往復 12）

- **N16 変えた所に絞ってラベルを付け直す時に、コーパスのどの項目を人に渡すかが書かれていない**: 解消（目安を組み合わせて使う時の残りは N17）。adopting.md 第15.1節の 1 の下に「変えた所に絞ってラベルを付け直す時（第13節のクラスの変更や、代表を直した後）」の三つの目安と「選んだ規則を記録する」が足され、2 に「`item.source` は分類器の選択（印を読む分類器では印そのもの）を含むので、人に渡す形からは除く」が足された（changelog.md の「未公開」の最後の項目）。読んで確かめた: 往復 11 で決められなかった三点は、それぞれ一つの目安で決まる
  - (2) 「証拠に使う」の範囲: 対象の目安（記述が、その成果物の内容を証拠に使う対象。ステージとゲート。下流の記述がその内容に触れないなら渡さなくてよい）で決まる。当てはめると、往復 11 の選び方は合っていなかった。plan\_tasks（要件を扱うタスクと、要件を受け持つ構成要素の欠け）と architecture のゲート（すべての要件が design.md の「## 対応」とタスクで扱われる）の記述は、変えた requirements.md の REQ-3 と design.md の「## 対応」を根拠にするのに、往復 11 は design.md を design だけの根拠とし、この二つを渡していなかった（G-6 の列挙が「design」だったため）。足した。渡さない対象と理由（implement、unit\_test と construction のゲートの requirements.md、review、release と後の二つのゲート）は README に書いた（review は、往復 13 で改められた目安に当てはめて足した。N17）
  - (3) 訪問 2 以降を省いてよいか: 訪問の目安（訪問 1 を渡す。記述が持ち帰った記憶やその応答に触れる対象では、訪問 2 以降も渡す）で決まる。往復 11 はすべて訪問 1 だけで、合っていなかった。intake（持ち帰った問いを尋ねる）、analyze（requirement\_gaps を直す。持ち帰らせた問いの回答を intake.md で読む）、design、plan\_tasks、unit\_test と、discovery と architecture のゲートで訪問 2 以降も見るようにした。訪問 2 以降で訪問 1 と違う状態文書になるのは、持ち帰った問いと回答が intake.md に入る intake、analyze、discovery のゲートで、その 12 項目を足した
  - (4) 同じ組をまとめてよいか: まとめ方の目安（(対象, 印, 上流の違い) の組ごとに一つ以上。短い状態文書の一つで代えてよい）で決まる。往復 11 の選び方（組ごとに一つ、状態文書の短いもの）と同じ。訪問の目安と組み合わせる時に組に訪問を足したことは N17
  - 小さなこと（source）: 2 の文で決まる。この例はもともと材料のコーパスの source から選択を除き（残るのは run と seq で、印は分からない）、人には human-labeling.md だけを渡している。コーパスの状態文書には印が残るので、human-labeling.md の読み方に「ラベルを付け終えるまでコーパスを開かない」を足した
  - 材料を作り直した: 試しの分布 labeling に、plan\_tasks の訪問 1 の unknown と、訪問 2 以降を見る対象の訪問 2 以降のクラス（markov に出るもの）を置き、240 回（種 90000 のまま）にした。45 項目（訪問 1 が 33、訪問 2 以降が 12。往復 11 の 30 項目に、plan\_tasks 2、architecture のゲート 1、intake、analyze、discovery のゲートの訪問 2 以降 12 を足した）。人のラベルはまだ無かったので、付け直す範囲の問題は無い。記述は変えていない

## 解消済み（往復 11）

- **N14 クラスの粒度を、独立性検証の結果以外の理由で変えてよいかが、手引きに無い**: 解消。adopting.md 第13節の「violated が出たら」の下に二つが足された（changelog.md の「未公開」の最後）。一つは「戻り先が同じで、運用の上で分けて数えたいだけ（たとえば、テストの不足とテストの誤り）なら、クラスは分けない。持ち帰る記憶の項目の中で区別し、記憶の中身で数える。クラスは下流の振る舞いに関する同値類で、集計のための分類ではない」。もう一つは、クラスを変えた後（分割、統合、記述の意味の改訂）に確かめることの一覧。読んで確かめた: 往復 10 で迷った二点は、どちらも一つ目で決まる。往復 10 の分割（戻り先が同じ unit\_test 自身で、違いは分けて数えたいことだけ）は書かれた例そのもので、手引きだけで「分けない」と判断できる。(a)「この検証の結果でのみ」が運用の理由を含むかは、集計の都合は理由にならないと明示されて決まった。(b) 戻り先が同じクラスを分けてよいかも、分けずに記憶の項目で区別すると決まった。分けた後に何を確かめるかは二つ目の一覧にある。往復 11 で、取り消し（記述を往復 10 の前の文に戻す、統合で記述の意味の改訂）に一覧を当てはめた
  - 整合性検査（第3節）: tests/test\_definition.py が違反も警告も無いことを確かめる。rollback、carry、記憶の生成と消費は、記憶 test\_defects と tests\_defective の辺が無くなって往復 10 の前の形
  - 記述の分け方と優先（第2.1節）、description の「訪問のたびに必ず書く」、フェーズゲート（第2.4節）: 人間が承認した往復 10 の前の文に一字も変えずに戻した（`git diff 08f79b4 -- examples/software-factory/workflow.yaml` が空）。最終ステージの成果物の節（test\_report.md の「## 不備」）を戻したので、construction のゲートの goal も戻した
  - 偽の本体の代表（第12節）: tests\_insufficient は確率的な実行の代表 thin のまま。defective は tests\_insufficient の確率 0 の代表にし（不備を「## 未網羅」と coverage\_gaps に書く）、シナリオ unit\_test\_defective\_self\_rollback で空でない記憶を持って戻る辺を踏む。分布、設計値、基準は変えていない
  - 独立性検証と E2E のカバレッジ（第14節）: E2E の (ステージ, クラス) は 31 → 30。独立性検証、入り方の検定、マルコフ合成は check.sh でやり直して通る（markov と divergent の分布を変えていないので値も往復 10 と同じ）
  - 第15.1節の付け直し: 人に渡す材料（docs/human-labeling.md）に、defective を三つの実装の変種の後で読む unit\_test の 3 項目を入れた。分類器の検証のコーパスの人手のラベルと、トリアージの判定で tests\_defective を指すものは無い（この例のラベルと判定は、テストの実行の時に印から作る。examples/software-factory の中を tests\_defective で検索して、往復の記録の文書と、取り消しを述べる docstring と注記のほかに残りが無い）
- **N15 シナリオの files で、ディレクトリの参照とその下のファイルの鍵が重なる時の扱いが書かれていない**: 解消。contract/conformance/README.md の「ファイルの内容」に「同じパスに鍵が重なる時（ディレクトリの鍵と、その下のファイルの鍵や、より深いディレクトリの鍵）は、より長い鍵（そのパスに最も具体的な鍵）の内容になる。鍵の並びにはよらない」が足され、changelog.md の「互換性に注意する変更」に、前は鍵の並びで後に書いたものになっていたことが載った。試した（スクラッチ）: inputs に repo/（inputs の repo）、repo/src/（implement の ok\_fixed の src）、repo/src/shopcart/discount.py（implement の ok の discount.py）の二つか三つを、並びを変えて 7 通り書き、`load_scenario` の結果を見た。どの並びでも discount.py は最も長い鍵（ファイル）の ok の内容、cart.py は repo/src/ の ok\_fixed の内容、ほかは repo/ の内容になった。回避（software\_factory/scenarios.py の ok\_files\_by\_file。inputs の repo/ をファイルごとに展開する）を外し、ok\_files が inputs の repo/ の参照に implement と unit\_test のフィクスチャのファイルの参照を重ねる形にした。シナリオ unit\_test\_defective\_self\_rollback の expect.starts と、往復 11 で足した construction\_rollbacks の unit\_test#2、release\_notes\_self\_rollback の release#2 の expect.starts はこの重ね方で書き、通る。作り直したシナリオの YAML の、往復 10 の前（08f79b4）にもあった 15 本との差は、足した expect.starts（と YAML の別名）だけ

## 解消済み（往復 9）

- **N13 クラスを種だけで選ぶ偽の本体では、代表は組みうるすべての上流の成果物と整合しなければならないことが、手引きに無い**: 解消。adopting.md 第12節の「実行のしかた」に「代表は、届きうるすべての上流の成果物と整合させる」の項が足され、changelog.md の「未公開」にも載った。読んで確かめた: 往復 8 でこの例が当たった二つの形がどちらも書かれている。一つは、代表がユーザーシミュレータのペルソナの回答や上流の変種と組み合わさるので、どの組み合わせでも記述どおりにそのクラスにならなければならないこと（この例の analyze の goal と needs\_unclear、acceptance の requirement\_misread）。もう一つは、上流の goal の記述と両立しないクラスには確率的な実行の代表を置けず、シナリオか E2E の注入で踏むこと（例に挙がっているのは、この例の plan\_tasks の design\_incomplete と同じ形）。整合は第15.1節の手順で上流の違いを分けて確かめる、と第15.1節にもつながっている。この例は往復 8 で、この項のとおりにしてある（design\_incomplete は E2E の注入で踏み、ペルソナの回答と持ち帰る問いを全ペルソナで整合させ、第15.1節をペルソナで分けてやり直した）ので、例は変えていない

## 解消済み（往復 7）

- **N12 印を読む偽の分類器の下では、記述と代表の成果物の食い違いがどのテストにも出ない**: 解消。adopting.md 第15.1節に、限界（MarkerClassifier と台本の分類は記述を読まない）と手順（全変種を踏む実行の集まりのコーパスを、印を除いた状態文書 `unmarked(item.state)` と選択肢の記述だけで人がラベル付けし、`oracle_report(MarkerClassifier(), corpus, labels)` の混同行列で印との食い違いを探す）が書かれ、`unmarked` が公開された。手順を試した: markov と divergent の 400 回ずつ（種 20000、30000）を一つの置き場で走らせ、`build_corpus(..., unique_states=True)` のステージの 315 項目から (ステージ, 印) ごとに一つ、30 項目を選び、並びを混ぜて、印を除いた状態文書と選択肢の記述だけを読んで試しのラベルを付けた（人手のラベルではない。例のテストには入れていない）。`unmarked` の後に印は残らない（review.json の "marker" の鍵だけが空で残る）。κ は 0.915 で、食い違いが 2 件あった
  - acceptance の requirement\_misread の代表: 「## 依頼との食い違い」は、依頼と intake.md が「購入者がレジの画面でコードを入力する」前提だとするが、その前提は precise\_pm の回答にしか無い。vague\_founder と terse\_engineer の intake.md と組むと、記述の上では食い違いの根拠が無く unknown になる（試しのラベルは unknown、印は requirement\_misread）
  - plan\_tasks の design\_incomplete の代表: tasks.yaml と記憶は「design.md の構成に REQ-3 と REQ-4 を受け持つ箇所が無い」とするが、plan\_tasks は design が goal の後にしか走らず、goal の代表の design.md は REQ-3（parse\_code）と REQ-4（Cart.total）を受け持たせている。記述の上ではいつも unknown になる
  - 選んだ 30 項目の外で、同じ見方から、analyze の goal の代表（requirements.md の REQ-1 の「nn は 1〜50」）も、vague\_founder の回答（「上限はまだ決めていない」）と組むと「どの要件も依頼か回答に根拠を持つ」を満たさない。ペルソナで intake.md が変わるのに、下流の代表は precise\_pm と terse\_engineer の回答を前提にしている
  - 三つとも、この例の代表の誤りで、手引きの不足ではない。人間のレビューに回す（README の「記述と代表の整合（試しのラベル）」）。315 項目すべてに人がラベルを付けるのは重いので、(ステージ, 印) ごとに選ぶと手順は回る。ただし三つ目のように、上流の成果物（ペルソナの回答）との組み合わせで初めて食い違う代表は、印ごとに一つ選ぶだけでは見落としうる。選ぶ時は上流の違い（この例ではペルソナ）でも分けるとよい

## 往復 6 で使った手引きの変更

検証役の指摘を受けてフレームワークの側が直した手引き（changelog.md の「未公開」の最後の三項目）は、どれもこの例を直すのに足りた。

- 第2.1節（memory\_out は訪問のたびに書く）: 各ステージの description に書き、偽の本体（確率的な本体の変種とシナリオの台本）が memory\_out のすべての項目を毎回書くことを tests/test\_stochastic.py で確かめる
- 第4節（異常終了を覚えない、測定の失敗が無いことを確かめる）: 指標が意味の決まった終了コードだけを覚え、異常終了は MetricError にするようにした。実行記録の evaluation の `metrics.<指標名>.error` で、分布テストに使う実行の集まりに測定の失敗が無いことを確かめる。pytest の終了コード 2 は「中断」で、テストの収集の失敗（実装が import できない）でも返るので、それだけは「通らない」として覚えた（手引きの「0 と 1 など」の例からは分からなかったが、判断には困らなかった）
- 第12節（0 か 1 に近い割合の幅）: release の訪問 2 以降の goal（p = 0.97、E[n] = 65.1、外れる側の期待件数 約 2）の min を、二項分布の裾の確率から 0.90 から 0.88 に直した（誤って落ちる確率 0.33% → 0.07%）

## 解消済み（往復 5）

- **N11 変更の記録に、このリポジトリの中に例を置く時の決まりの変化が一部載っていない**: 解消。docs/changelog.md の「変えたもの」に「このリポジトリの中に例を作る場合（adopting.md 第11節）」がまとめられ、fixtures の除外に加えて、例の語の検査で本体の公開の名前と本体のワークフロー定義の例の語を除き、重なりを一度にすべて一行ずつ出すこと、時間の目安を一つの例で一分以内からおよそ二分以内（カバレッジの計測の下）に改めたことが載った。adopting.md 第11節の今の文と食い違いが無いことを読んで確かめた（往復 1 の B2、往復 2 の N3 と N7 で確かめた振る舞いとも合う）

## 解消済み（往復 4）

- **N10 公開の振る舞いの変化を知る場所が無い**: 解消（載っていない小さな変化は N11。往復 5 で解消）。docs/changelog.md が公開 API の文書の一つになり、api.md の冒頭と文書の一覧から指されている（README は読んでよい文書に入らないので見ていない）。changelog.md だけを読んで確かめた: 「未公開（v0.1.0 の後）」の節の先頭の「互換性に注意する変更」に、`compare_prediction` の量の追加と、量の種類を固定の集合で確かめるテストは `gate` を足す必要があることがあり、往復 3 でこの例のテストが落ちた理由と直し方がそのまま分かる。この例が使う往復 1〜3 の変更はすべて載っている: api-reference.md、tests/fixtures/ の除外、シナリオの `{from: パス}`、`run_scenario` と `run_coverage` の `user`、`Prediction` の `evaluations`、`visit_outcomes`、`visits_variance`、`build_corpus(..., unique_states=True)`、`entries` と `entry_dependence`、`RandomGateClassifier`、`conformance_dir` と `conformance_scenarios`、足された型（`EndState`、`SCHEMA_FILES` など）、synthesize とトリアージが速くなったこと、契約 第10節の明記。v0.1.0 からの公開の文書の差分（contract/、schema、api.md）と突き合わせて、ほかに載っていない API の変化は見つからなかった

## 解消済み（往復 3）

往復 3 の判定と確かめ方。ここで N10 とした残りは、上の往復 4 で確かめた。

- **N8 compare\_prediction がゲートの評価の結果を比べない**: 解消。api-reference.md の compare\_prediction に比べる量（status、visits、outcome、gate）が書かれた。試した: assurance のゲートを揺らした実行（markov\_gated.yaml の 400 回）で、比べる量が 41 から 47 になり、`gate:assurance=goal` と `gate:assurance=changes_requested` を含むすべてが一致した。tests/test\_e2e.py でゲートの評価の回数を visit\_outcomes と訪問の区分ごとに手で比べていた部分を外し、ゲートの量が比べる量に入ることを確かめる形にした。ゲートの量は訪問の区分に分けないが、ステージの量も同じで、区分ごとの割合は markov\_gated.yaml の基準（訪問 1 と 2 以降）が確かめる。量の種類を固定の集合で確かめていたテストは、gate を足して直した（変化を知る場所は N10）
- **N9 予測と実測が合っても、入り方による違いは隠れうる**: 解消。第14節に「予測と実測が合っても、仮定が成り立つとは限らない」と `entry_dependence`、`entries` が書かれた。試した: 往復 2 のスクラッチの carry で振る舞いが変わる本体（implement が自分自身から impl\_violations を受けた時だけ goal 0.5）で、`entry_dependence` は implement の訪問 2 以降を violated（p = 0.0005、入り方 5 通り）と判定した。markov、ゲートを揺らす実行、divergent の本体では violated が無く、implement は not\_detected（markov で p = 0.62）。一回 0.3〜0.4 秒。往復 2 で手で辿った十数行は要らない。例のテストに、markov とゲートを揺らす実行の両方で、入り方が二つ以上あるステージに violated が無いこと（test\_class\_distributions\_do\_not\_depend\_on\_the\_entry）を足した。気づいたこと: ゲートの不合格による戻りと、ステージの評価による戻りは、同じ辺なら同じ入り方（`rollback:review=changes_requested`）になる（docstring にそう書いてある）。持ち帰る記憶の中身で振る舞いを変える本体は、この二つを分けられない

## 解消済み（往復 2）

往復 2 の判定と確かめ方。ここで N8、N9 とした残りは、上の往復 3 で確かめた。

- **N1 signature に出てくる型が書かれていない**: 解消。api.md と api-reference.md に `Criterion`、`EndState`、`Goal`、`Phase`、`Rollback`、`Event`、`Key`、`Dist`、`writes_hash`、`SCHEMA_FILES` があり、どれも import できることを試した。tests/test\_oracle.py が使う `EndState.id` も書かれた。小さなこと: `Event` は runtime（`dict[str, JSONValue]`）と testing.stages（`Mapping[str, Any]`）で定義が違う。api-reference.md の `SCHEMA_FILES` の値は末尾が `…` で切れる（import すれば 8 つの名前が見える）。どちらも使う上では困らない
- **N2 契約に決定の番号が残る**: 解消。contract.md 第1節と self\_rollback.yaml の description から消えた。contract/、schema/workflow.schema.json、api.md、api-reference.md、adopting.md を「決定」、plan.md、decisions.md で検索して、残りが無い
- **N3 語の重なりの報告が切れる**: 解消。workflow.yaml の記憶の名前を一時的に本体にありそうな三つの語（`checkpoint`、`runner`、`fakes`）に変えて check.sh を実行すると、tests/test\_package.py の失敗が、三つの語の 16 か所を `ファイル:行:語` の一行ずつで出した（その後に切れた一覧も出るが、上の行で全部見える）。workflow.yaml は元に戻した
- **N4 synthesize が訪問の回数の分散を出さない**: 解消。`Prediction.visits_variance` の implement は 1.368（標準偏差 1.170）で、前に標本で出した 1.168 と合う。adopting.md 第12節に mean\_visits の幅の出し方。design.simulate（遷移規則を例の中で辿る標本）と、それを確かめるテストを外し、mean\_visits の幅は visits\_variance から出すようにした（tests/test\_stochastic.py、markov.yaml の注記）。気づいたこと: この大きさのワークフローで synthesize が約 0.8 秒から約 3.4 秒に（計測の下で約 2.5 秒から約 6 秒に）遅くなった。目安（N7）には収まる
- **N5 ゲートを揺らす偽の分類器**: 解消。`RandomGateClassifier` と第14節の書き方で、スクラッチでの往復 1 の試し（自前の偽の分類器）と同じことができた。例に取り込んだ: run\_set に gates を足して実行ごとに組み立て、assurance のゲートを {goal: 0.8, changes\_requested: 0.2} で揺らす実行の集まり（tests/expectations/markov\_gated.yaml、400 回、種 50000）を足した。四つの基準（ゲートの訪問 1 と 2 以降の changes\_requested、完了の割合、implement の訪問の回数の平均）が通り、ゲートの分布を足した設計値のモデルの予測が 41 の量で実測と合い、ゲートの評価の回数も予測と合い、独立性検証は違反を出さない。比べる関数がゲートを比べないことは N8
- **N6 実ハーネスでの合成の読み方**: 解消（残りは N9）。第14節に、仮定が近似になる所（入り方が複数あるステージの二回目以降と、その後）、合わない時の調べ方（直前の辺で分けて比べる）、そういう量は実測で確かめることが書かれた。往復 1 で分からなかった「見分け方」と「どこまで信じてよいか」に答えている。調べ方はスクラッチで試し、carry で変わる本体を見分けられた（N9）
- **N7 時間の目安**: 解消。第11節の目安が、カバレッジの計測の下で一つの例でおよそ二分以内になり、統計のテストの回数を減らさないこと、推定の集まりは推定の手順を確かめたい時だけ足すことが書かれた。この例は往復 2 の前で約 88 秒、ゲートを揺らす集まりを足して約 107 秒（check.sh 全体は約 2 分 15 秒）。推定の集まりは estimate\_model をこのワークフローで確かめるために残した

## 解消済み（往復 1）

往復 1 の判定と確かめ方。ここで「N」を付けた残りは、上の往復 2 で確かめた。


### A. 文書と API の参照

- **A1 api.md に引数と属性が無い**: 解消。api-reference.md に、前に挙げた名前（Question、record\_run、ConfusionClassifier、FlakyClassifier、enqueue、decide、plan\_coverage、MarkovModel、OracleReport など）の signature、属性、docstring があることを読んで確かめた。StageContext の項は使ってよい属性だけを挙げ、adopting.md 第5節が `dir(context)` で見えるほかの名前を使わないよう書く。signature の中の一部の型が無いことは N1
- **A2 StageContext の属性の一覧の食い違い**: 解消。adopting.md 第5節と api-reference.md の StageContext に `stage_id` と `visit` がある
- **A3 契約が読めない文書を根拠として指す**: 一部（往復 2 で解消。N2）。contract/、schema/workflow.schema.json、api.md、api-reference.md を plan.md、decisions.md、「決定 #」で検索し、残りは二か所だけ（N2）
- **A4 記憶がまだ無い時の read\_memory**: 解消。adopting.md 第5節と StageContext.read\_memory の docstring に「値がまだ無ければ None」
- **A5 保留中の質問の形**: 解消。adopting.md 第7節の手順 1 と RunState の docstring に `{"kind": "user", "question": {"text": ..., "choices": [...]}}`
- **A6 置き場から状態文書を読む方法**: 解消。adopting.md 第7節（`store.get(snapshot.files[パス])`）、第15節（evaluation の `classification.state`）、第16節（`store.get(item.state)`）と BlobStore.get の docstring
- **A7 OracleReport.by\_target の鍵**: 解消。adopting.md 第15節と OracleReport の docstring に `stage:<id>` か `phase:<id>`

### B. リポジトリの中に例を置くこと

- **B1 壊れたコードのフィクスチャとリポジトリ全体の検査**: 解消。adopting.md 第11節に「tests/fixtures/ の下は ruff、mypy、pytest の収集から外れる」。試した: tests/fixtures/.code/ を普通のディレクトリ（tests/fixtures/implement/、unit\_test/、inputs/repo/）に移し、tests/fixtures/ruff.toml と tests/conftest.py の collect\_ignore を外した。check.sh が通る（ruff check、ruff format、mypy strict がこの例で 19 ファイル（前と同じ）、pytest 602 件）。意図的に lint に反するコード、構文の誤り、失敗するテスト、同じ名前のモジュールの 8 変種がそのまま置ける
- **B2 例の id が本体の語と重なってはいけない**: 解消（報告の見え方は N3）。adopting.md 第11節に制約と除外が書かれた。試した: workflow.yaml を一時的に前の名前（`verify`、`request.md`、`open_questions`）に戻して tests/test\_package.py を実行すると、全部通った。記憶の名前を本体にありそうな語（`checkpoint` と `runner`）に一時的に変えると、一回の失敗で両方の語が一覧に出た。戻した名前は採らなかった（`acceptance`、`feature_request.md`、`intake_questions` でも自然で、`verify` に戻すとステージの種が変わり、全テストの数値を取り直すことになるため）
- **B3 指標の args の型**: 解消。adopting.md 第4節と MetricRegistry.measure の docstring に「読み取り専用の Mapping。必要なら dict(args)」
- **B4 実在のツールに裏づけられた指標の費用**: 解消。adopting.md 第4節と第11節、MetricRegistry.measure の docstring に「読むファイルの内容のハッシュと args を鍵に覚えてよい」。この例の覚え方（指標名、引数、内容のハッシュ）がそのまま当てはまる。recorder に任せられるかは書かれていないが、覚えてよいと分かったので要らない
- **B5 変更パスの範囲の指標と writes**: 解消。adopting.md 第4節に「writes より狭い範囲と比べる」と理由
- **B6 例のテストの時間**: 解消（この例が目安を超えることは N7）。adopting.md 第11節に、一つの例で一分以内の目安、実行の集まりを session の fixture で共有すること、synthesize の時間が到達しうる状態の数に比例することが書かれた。試した: 9 ステージ 12 辺の synthesize は約 8 秒から約 0.8 秒に（カバレッジの計測の下では約 17 秒から約 2.5 秒に）
- **B7 契約適合テストの意味**: 解消。契約第10節、contract/conformance/README.md、adopting.md 第9節に「判定の対象はランタイムの実装。参照ランタイムを使うハーネスは自分で通す必要は無く、ハーネスの側が守ることはランタイムが実行のたびに検査する」。シナリオ一式は `conformance_dir()` と `conformance_scenarios()` で場所が分かる（25 件）。tests/test\_conformance.py はリポジトリのパスをやめて `conformance_scenarios()` を読み、必須ではない版の確認として残した。形式の schema も `load_contract_schema` で読むようにした（tests/test\_oracle.py、test\_triage.py）

### C. ワークフロー定義

- **C1 ゲートの不合格を end\_state で戻すことと「goal に優先」の衝突**: 解消。adopting.md 第2.4節の注意に、goal の時に空になる記憶を証拠にしたクラスにはフェーズ全体の条件を書かず、goal の時にも中身を持てる記憶のクラスに限るとある。この例の書き方（review の changes\_requested だけ）と同じ
- **C2 goal 到達扱いと後のゲートの実在の指標**: 解消。adopting.md 第7節の末尾と ContinueAsGoal の docstring に「後のゲートの指標は免れない。テストでは後の指標を満たす成果物の状態で使う」

### D. 確率的な本体と分布テスト

- **D1 ユーザーシミュレータに実行の種が届かない**: 解消。adopting.md 第12節に、`run_many` に渡す関数の中で選んだシミュレータのランタイムを実行ごとに組み立て、置き場と作業ディレクトリは共有する形と、回答を保留するシミュレータを束縛すると実行が中断のまま記録される注意がある（record\_run の docstring にも）。この例の run\_set と同じ形
- **D3 visit で絞った基準の分母の期待値**: 解消（分散の残りは N4）。`synthesize(design_model, workflow).evaluations[("stage", 対象, 区分)]` と `visit_outcomes` で、markov.yaml の 10 の outcome\_rate の基準の E[n] と設計値の割合が出ることを試した。前に標本で出した値との差は 400 回の実行で最大 0.7（例: analyze の訪問 1 は 388.1 → 388.0、implement の訪問 2 以降は 320.9 → 320.3）で、基準の値は変わらない。markov.yaml の注記を厳密な値に直し、各基準が設計値の両側に標準誤差の 3 倍以上あることを synthesize の値から確かめるテスト（tests/test\_stochastic.py の test\_correct\_expectations\_follow\_the\_design）を足した。design.simulate から訪問ごとの評価の数え上げを除いた（往復 2 で simulate ごと外した。N4）
- **D5 実在の指標と偽の本体のクラスの整合**: 解消。adopting.md 第12節の「偽の本体と実在の指標を組み合わせる時」。この例の設計値の metrics\_fail と tests/test\_metrics.py と同じ形
- **D6 種の分布を疑った**: 解消。adopting.md 第5節と StageContext.seed の docstring に「`random.Random(seed)` にそのまま渡してよい。訪問ごとに独立な一様の種とみなせる」

### E. 分類器の検証とトリアージ

- **E1 コーパスの重複と FlakyClassifier**: 解消。`build_corpus(..., unique_states=True)` と、adopting.md 第15節、ConfusionClassifier と FlakyClassifier の docstring の注意。tests/test\_oracle.py の手書きの重複除きをこれに替えた（ステージの項目に絞る）。markov の最初の 60 回で、手書きの重複除きと同じ 127 項目、同じ順になることを試した。κ、ECE、再実行の一致率のテストはそのまま通る
- **E2 ゲートの項目のラベル**: 解消。adopting.md 第15節に、MarkerClassifier の印はステージのクラスでゲートの状態文書には無いので、ステージの項目に絞るかゲートには人手でラベルを付けるとある
- **E3 トリアージの関数の費用**: 解消。試した: 確信度 0.6 の MarkerClassifier と review\_below 0.7 で 24 回の実行の全評価（361 項目）を待ち行列に足すのに約 0.25 秒、全項目に判定を付けるのに約 0.17 秒（前は約 360 項目で約 18 秒）。tests/test\_triage.py の Hesitant（review と assurance のゲートだけ確信度を下げる偽の分類器）を外し、全評価を待ち行列に入れる形にした。テストは約 4 秒
- **E4 トリアージの項目とコーパスの項目の id**: 解消。adopting.md 第16節と CorpusItem、TriageItem の docstring に、同じ形 `<実行の id>-<評価の seq>` で突き合わせられるとある

### F. 決定論テストと E2E

- **F1 シナリオの inputs にディレクトリやフィクスチャを指せない**: 解消。contract/conformance/README.md の「ファイルの内容」と adopting.md 第8節に `{from: パス}`（ディレクトリは鍵と from を / で終える）。software\_factory/scenarios.py が inputs と expect.starts の files をフィクスチャへの参照（`repo/: {from: ../fixtures/inputs/repo/}` など）で書くようにした。14 のシナリオの YAML は 2841 行から 1635 行になり、load\_scenario で読んだ inputs、visits、gates、台本、期待が前と同じ（フィクスチャのパスの `.code/` を除いて）ことを全項目で比べた。フィクスチャの中身を変えても作り直さなくてよくなった。遷移の列を手で並べる道具としては残した。`plan_coverage` の inputs は文字列だけを取るが、inputs() を読めば足りる
- **F2 シナリオと E2E にユーザーシミュレータを束縛できない**: 解消。`run_scenario(..., user=...)` と `run_coverage(..., user=...)`。三つのペルソナを、持ち帰った問いを尋ねるシナリオ（needs\_unclear\_asks\_again）と、最初の質問で回答を保留するシナリオ（happy\_path\_user\_suspend。再開の回答は台本の user から取る）に束縛し、どちらも期待どおりに通ることをテストにした。E2E のカバレッジでは intake の goal の台本に三つの質問を足し、ペルソナに答えさせて全 (ステージ, クラス) を踏む

## 直さないと言われたもの

### D2. carry を受けたかで分布が変わる本体と、(ステージ, 訪問) のマルコフモデル

adopting.md 第14節に「モデルの区分は (ステージ, 訪問の区分) だけで、carry を受けたかは入らない。そのステージに戻ってくる辺が carry を持つ一本だけでない限り仮定を壊し、予測が合わない。偽の本体で確かめる時は、戻ってくる辺が一本のステージに置く」とある。

判断（往復 1）: この例にとっては十分。前に自分で選んだ置き方（release に戻る辺は自分自身への一本だけで、訪問 2 以降と carry を受けたことが一致する）が、そのまま文書の勧めになっている。制限として明示されたので、合成が合わない時の第一の疑いにできる。実際のハーネスでの扱いが足りないことは N6 に書いた。

判断（往復 2）: 第14節に「実ハーネスでの合成の読み方」が足され、モデルに carry を入れないままでの扱い（どの量が近似になるか、どう見分けるか、そういう量は実測で確かめる）が分かるようになった。直さないことの説明として十分。合っている時にも隠れうることは N9 に書いた。

判断（往復 3）: 第14節に、合っていても `entry_dependence` で確かめることが足され、この例でも markov とゲートを揺らす実行で確かめるようにした（上の N9）。モデルに carry を入れないことの説明と、その下での確かめ方がそろった。

### D4. MarkerClassifier の下でのゲートの分布

adopting.md 第14節に「ゲートを落とすには最終ステージの goal の成果物の一部にゲートの印を入れるしかなく、その成果物は goal の中で下流が違う代表になり、独立性検証は violated と判定する（正しい判定）。ゲートからの戻りはシナリオで確かめ、確率的な実行のゲートはいつも goal にする」とある。

判断（往復 1）: MarkerClassifier を使う限りの説明として正しく、この例のやり方（確率的な実行のゲートは goal、ゲートからの戻りはシナリオの assurance\_gate\_rolls\_back）と一致する。ただし「しかない」は強すぎる。実行ごとの乱数でゲートを揺らす偽の分類器で、ゲートの分布を持つマルコフ合成を偽の本体のまま確かめられた（N5）。

判断（往復 2）: 第14節は「成果物の印で落とすと violated になる。成果物によらずに揺らすには RandomGateClassifier を実行ごとに組み立てる」に直り、その偽の分類器が入った。もう「直さない」項目ではなく、この例も markov\_gated.yaml の実行の集まりでゲートの分布を持つマルコフ合成を確かめる（上の N5）。markov.yaml の実行のゲートは、前の数値を保つためにいつも goal のまま。
