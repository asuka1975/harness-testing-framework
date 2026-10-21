# F1 toy-minimal workflow.yaml 事前レビュー（検証役）

- 検証日: 2026-10-21
- 役割: 検証（第三者）。plan.md 第5.9節「workflow.yaml の MECE レビュー（人間に出す前の事前確認）」。実装の作業過程は見ておらず、成果物と仕様だけから判定した
- 対象: examples/toy-minimal/workflow.yaml、examples/toy-minimal/README.md、examples/toy-minimal/toy\_minimal/metrics.py（参考に tests/test\_definition.py、tests/test\_metrics.py、src/harness\_testing\_framework/testing/spec/checker.py）
- 判定の基準: plan.md 第2節（終了状態の三層、評価順序、分類器、ロールバック）、第6節 F1・F4 の人間ゲートの観点、付録 B。contract/contract.md 第2・3節。decisions.md #5、#7、追加の論点 A、D-1、D-2
- 書いたもの: このファイルだけ。workflow.yaml などは保護ファイルなので、下の書き換え案はすべて計画役への提案である

## 総合判定: 直してから出すべき

整合性検査は違反なしで通り（下記「証拠」）、遷移の六種は定義の上でどれも起こりうる。四つのステージの end\_state の戻り先も、状態を解消できるステージを指している。ただし、人間のレビューの観点（MECE、観測可能性、戻り先）で崩れている所が二つある。

1. compose のフェーズゲートの qualitative が brief.txt を参照するが、compose のどのステージも brief.txt を読まず書かない。ゲートの状態文書をどう読んでも分類器に見えない（観測可能性の崩れ）
2. write\_note の goal と outline\_unfit が重なりうるのに、優先が書かれていない（MECE の崩れ）

加えて、三つの end\_state すべてで「end\_state に分類されても carry が空でありうる」書き方になっている（中 M-2）。両フェーズゲートとも、正しく分類すれば goal を満たさない状態は必ず unknown に落ちる（中 M-3）。この二つは、F4 の利用者が手本にする玩具として直しておくべきである。どちらも分類体系の変更（end\_state の追加・分割・統合）なしで直せる。M-3 の別案だけが分類体系の変更を伴う。

## 前提と方法

### 分類器が見るもの

契約 2.4 により、ステージの評価で分類器に渡るのは、そのステージの reads と writes のファイルの内容と、memory\_out の記憶の値だけである。memory\_in は入らない。各記述について、そこに書かれた条件がこの投影から判定できるかを機械的に確かめた。

フェーズゲートの分類で分類器に何を渡すかは、契約に定義が無い。2.4 はステージ単位で書かれ、3.2 は指標の入力（「フェーズ内の全ステージの writes の和」）しか言っていない。そこで、ゲートの qualitative は次の二つの読みの両方で確かめた。

- 読み (i): 最終ステージの投影
- 読み (ii): フェーズ内の全ステージの writes の和

### 証拠

- `uv run --offline pytest -q examples/toy-minimal/tests -p no:cacheprovider` → 10 passed。test\_passes\_checker\_without\_warnings は `check_workflow_file(WORKFLOW, REGISTRY.names()) == []` を確かめるので、検査器の違反と警告は無い
- 指標の正規表現の挙動を、リポジトリ外の一時実行で確かめた。`_outline_sections` の正規表現 `^- ([^:：\n]+)[:：]` は、`- 背景: 経緯` の後に「ユーザーに尋ねるべき問い」として `- 読者: 初心者か専門家か？`・`- 範囲: …？`・`- 目的: …？` を並べた outline.md から、`['背景', '読者', '範囲', '目的']` を返した（section\_count = 4 ≥ 3）。要約が空の `- 背景:` も節として数える。blocking\_findings は `{"blocking": "false"}` を 1 と数えた

## ステージとゲートごとの所見

### ask\_topic（intake、最初のステージ、awaits\_user）

- クラス: goal、unknown
- MECE: 成り立つ。最初のステージは前に戻り先が無い。戻り先の前方性と論点 A により end\_state を持てず、goal でなければすべて unknown になる。構造から決まる形で妥当
- 観測可能性: goal は topic.txt（writes）と brief.txt（reads）だけを参照するので観測できる。次の二点は投影から見えない
  - ユーザーの回答は投影に無い。ユーザーが依頼を意図して変えた場合は「brief.txt の依頼と矛盾しない」が偽になり unknown に落ちる。人間に返すのは妥当なので、記録だけでよい（低 L-6）
  - 再訪時に持ち帰った topic\_questions は memory\_in なので投影に入らない。持ち帰った問いに答えたかを goal で判定できない。答えずに同じ topic.txt を書いても goal に達し、plan\_outline でまた topic\_unclear になる。topic\_unclear の max 2 で escalate に至るので有界ではあるが、問いと回答を topic.txt に書き添える運用にすると観測できる（低 L-2）
- 指標と qualitative: file\_nonempty は qualitative の必要条件で、矛盾しない
- goal の強さ: goal は「主題と読者がそれぞれ一文以上」で、曖昧さが無いことまでは求めていない。曖昧な topic.txt でも goal に達するので、plan\_outline の topic\_unclear に到達できる。玩具として必要な弱さだが、意図であることを README に書くとよい（低 L-2）

### plan\_outline（intake の最終ステージ）

- クラス: goal、topic\_unclear、unknown
- MECE: goal と topic\_unclear が重なりうる。暫定の節を三つ以上（各節に要約つき）書き、末尾に問いを並べた outline.md は goal に当たる。topic.txt が曖昧で問いが列挙されているので topic\_unclear にも当たる。topic\_unclear の「節を決められない」が部分的に排他にしているが、暫定の構成と問いを両方出すのは自然な振る舞いで、優先が書かれていない（中 M-1）
- 残余: 主題は明確だが三節に分けるには狭すぎる、などは unknown に落ちる。自己ループが禁止（論点 A）なので構造上こうなる。許容する（低 L-8）
- 観測可能性: topic\_unclear の「曖昧」は topic.txt（reads）から判定でき、「問いが outline.md の末尾に列挙」は writes から判定できる
- 戻り先: ask\_topic はユーザーに尋ねられる唯一のステージで、状態を解消できる。ただし carry の topic\_questions は記憶である。記述が要求しているのは outline.md の末尾の問いであり、記憶が埋まっていることは要求していない。restore で outline.md は捨てられるので、本体が問いをファイルにだけ書いた場合、topic\_unclear に分類されても ask\_topic には何も届かない（契約 2.3 の 2「現在のスナップショットに無い項目は重ねない」）（中 M-2）
- 指標と qualitative: section\_count が数えるのは「- 名前:」の形の行で、outline.md の中の位置を問わない。topic\_unclear が指示する末尾の問いがこの形だと節として数えられ、節が一つでも指標が通る（上記の証拠）。要約が空の行も数える。形式（「- 名前: 要約」）は metrics.py にしか書かれていない（中 M-4）

### intake のフェーズゲート

- 選択肢: フェーズの qualitative、topic\_unclear、unknown（契約 3.2）
- 観測可能性: topic.txt と outline.md はどちらも intake の writes で、plan\_outline の reads と writes でもある。読み (i) でも (ii) でも観測できる。ただし「outline.md が…読者を前提にしており」は、節の名前と一行の要約だけの outline.md からは推し量るしかない（低 L-7）
- 指標: files\_nonempty は、ゲートの時点では「goal 到達扱いで続行」を経た場合を除いて必ず真になる。topic.txt が空でないことは ask\_topic の goal 指標が保証する。outline.md が空でないことは section\_count ≥ 3 が保証する。ステージの指標の繰り返しで、集約述語（決定 #5）の例になっていない（低 L-1）
- goal を満たさない状態の落ち方: plan\_outline が goal に達した直後なので、outline.md には要約つきの節が三つ以上ある。この状態は topic\_unclear の「節を決められない」と両立しない。ゲートで見つかる不足（読者のずれ、主題の範囲外の節）はすべて unknown に落ちる（中 M-3）
- 検出場所による落ち方の違い: 「outline.md の各節がその主題の一部を扱っている」に反する状態（主題の範囲外の節）は、write\_note の outline\_unfit と同じ不足である。このゲートで見つかれば escalate になり、ゲートが見逃して write\_note で見つかれば plan\_outline への自動のロールバックになる。早く見つけた方が人間に回る。論点 A（自己ループ禁止）と #5（ゲートの戻り先は最終ステージの辺）から構造上こうなるので、玩具の誤りではない。ただし README に書いておかないと F4 の読み手を誤らせる（中 M-3）

### write\_note（compose の最初のステージ）

- クラス: goal、outline\_unfit、unknown
- MECE: goal と outline\_unfit が重なる。outline.md に重複した節がある時に、両方の節を見出しと本文つきで書き、末尾に「書けない節（重複）」を書き出した note.md を考える。sections\_covered = 1.0 なので goal が選択肢に残る。goal（全節を順に見出しとして持ち、本文がある）と outline\_unfit（書けない節があり、末尾に書き出されている）の両方に当たり、優先が書かれていない（高 H-2）。goal を選ぶと review\_note が重複を修正要と指摘し、write\_note では直せないので、findings\_blocking の往復で max を使い切ってから escalate する。outline\_unfit を優先すべき
- 言い換え: outline\_unfit は具体的な原因（主題の範囲外、重複、順序の矛盾）と戻り先を持ち、goal の言い換えではない
- 観測可能性: outline.md と topic.txt（reads）、note.md（writes）だけを参照するので観測できる
- 戻り先: plan\_outline は outline\_gaps を memory\_in に持ち、構成を直せるので適切。フェーズ境界を越える（README のとおり）。carry の outline\_gaps については、記述が note.md の末尾への書き出ししか要求しておらず、記憶が埋まる保証が無い（中 M-2）
- 指標と qualitative: sections\_covered は「見出しとして持つ」の必要条件で、順序と本文は qualitative が担う。矛盾しない。見出しの形（`## 節の名前` に完全一致）は metrics.py にしか書かれていない。`## 1. 背景` のような見出しは、qualitative は満たすのに指標は落ちる（中 M-4）

### review\_note（compose の最終ステージ）

- クラス: goal、findings\_blocking、unknown
- MECE: 「修正を要する指摘」の有無で goal と findings\_blocking は排他になる。残余（査読が全節に及ばず修正要の指摘も無い、note.md だけでは直せない指摘を含む、review.json が壊れている）は unknown に落ちる。いずれも人間に返すのが自然で妥当
- 言い換え: findings\_blocking は「どの指摘も note.md を直せば解消する」という戻り先の条件を持ち、goal の否定の言い換えではない
- 例示の矛盾: findings\_blocking の例にある「節の抜け」は、意味が二通りに取れる。outline.md の節が note.md に無いという意味なら、write\_note の goal（sections\_covered = 1.0）がすでに保証しているので review の時点では起きない（強制通過を除く）。outline.md に無い節という意味なら、note.md だけでは直せず、同じ記述の「どの指摘も note.md を直せば解消する」と矛盾する（中 M-5）
- 観測可能性: review.json（writes）の指摘の中身として書かれており観測できる。「事実の誤り」も、分類器が事実を判定するのではなく review.json の指摘として読むので問題ない
- 戻り先: write\_note は review\_findings を memory\_in に持ち、note.md を書き直せるので適切。restore で note.md も review.json も捨てられるので、write\_note は review\_findings だけを頼りに一から書き直す。そのため review\_findings の各指摘は、note.md の中の位置ではなく outline.md の節の名前で場所を示す必要がある（低 L-3）。記述が review\_findings が埋まることを要求していない点は中 M-2
- 指標と qualitative: blocking\_findings（max 0）は「修正を要する指摘が一つも無い」と対応する。review.json の形（`{"findings": [{"blocking": …}]}`）は metrics.py にしか書かれていない（中 M-4）。真偽値でない blocking を真と数える（低 L-5）

### compose のフェーズゲート

- 選択肢: フェーズの qualitative、findings\_blocking、unknown
- 観測可能性: qualitative の「note.md が brief.txt の依頼に…答えており」は観測できない。brief.txt は compose のどのステージの reads にも writes にも無いので、読み (i) でも (ii) でも分類器に渡らない。しかも write\_note は brief.txt を読まないので、フェーズの中でこの状態を作る手段も無い（高 H-1）。読み (ii) では topic.txt と outline.md も見えなくなる。ゲートの状態文書の定義は計画役に上げる（下記「計画役へ上げる事項」）
- 指標: sections\_covered の args は write\_note の goal 指標と同じである。review\_note は note.md も outline.md も書かないので、ゲートの時点の値は write\_note が goal に達した時と同じ 1.0 になる。強制通過を除いて必ず真で、集約述語になっていない（低 L-1）。さらに、この指標は outline.md（intake の writes）を読む。契約 3.2 の「入力はフェーズ内の全ステージの writes の和」を、見えるファイルの制限と読むと outline.md が見えず、MetricError で未達になる。goal が選択肢から消えるので、玩具は一度も完了できない。7.2 の「フェーズ内の全 writes を含む終了時」と読めば動く。契約の読みに依存している（中 M-6）
- goal を満たさない状態の落ち方: review\_note が goal に達した直後なので、review.json に修正要の指摘は無い。findings\_blocking（修正要の指摘が一つ以上ある）は成り立たず、ゲートの不足はすべて unknown に落ちる（中 M-3）

### 玩具としての過不足（plan.md 第6節 F1）

| 求められるもの | 判定 |
| --- | --- |
| 3〜4 ステージ、2 フェーズ以上 | 4 ステージ、2 フェーズ。最小 |
| ロールバック、carry、フェーズ境界越え、ユーザー待ち | すべてある（write\_note → plan\_outline、ask\_topic） |
| 遷移の六種（3.5） | 定義の上ではすべて起こりうる（test\_definition.py）。中断と再開は最初の訪問と、topic\_unclear の後の再訪の両方で起こりうる |
| 契約 3.2 の「ゲートで end\_state → 同じ辺で rollback」 | 記述の上では起こらない（M-3）。F2 では偽の分類器に id を返させて機構だけを試すことになる |
| 契約 2.2 の「指標が未達ならゲートの選択肢から goal を除く」 | ゲートでは強制通過の後にしか起こらない（L-1） |
| 決定 #7 の「〜に優先する」 | unknown 以外の end\_state を二つ持つステージが無く、例が無い。H-2 と M-1 を直すと、goal に対する優先として例が二つできる |

余分なものは無い。不足は上の二つのゲートの分岐と、優先の例である。六種の遷移の要件は満たしているので、どれも F1 の完了条件の不足ではない。ただし F4 の利用者は toy-minimal を手本に読む（plan.md 第5.9節、第6節 F4）。ゲートがどう落ちるかは README に明記すべきである（M-3）。

## 指摘の一覧

書き換え案はすべて提案で、保護ファイル（workflow.yaml）の編集は計画役が行う。記述の改訂は人間の承認を経る（plan.md 第2節「end\_state 記述は仮説」）。

### 高

#### H-1 compose ゲートの qualitative が観測できない brief.txt を参照している

- 所在: workflow.yaml 第72〜74行
- 問題: brief.txt は write\_note と review\_note のどちらの reads にも writes にも無い。ゲートの状態文書を読み (i) と読み (ii) のどちらで取っても分類器に見えない。write\_note が brief.txt を読まないので、フェーズの中でこの条件を満たす手段も無い
- 直し方（推奨、分類体系の変更なし）: compose の goal の記述を、compose の投影に入るものだけで書く

  ```yaml
  qualitative: >-
    note.md が topic.txt の主題を topic.txt の読者に向けて述べており、outline.md の全節を述べている。
  ```

  この案では、依頼（brief.txt）との整合を見るのは ask\_topic の goal（「brief.txt の依頼と矛盾しない」）だけになる。topic.txt が依頼を写していることはそこで確かめ、compose は topic.txt を依頼の代わりとして扱う

- 別案: write\_note と review\_note の reads に brief.txt を加える。読み (i) では観測できるようになるが、読み (ii) では依然として見えないので、推奨案の方が頑健である

#### H-2 write\_note の goal と outline\_unfit が重なり、優先が無い

- 所在: workflow.yaml 第90〜91行、第98〜101行
- 問題: 全節を見出しと本文つきで書いたうえで、末尾に書けない節を書き出した note.md は、goal と outline\_unfit の両方に当たる。sections\_covered = 1.0 なので goal が選択肢から除かれない
- 直し方（分類体系の変更なし。境界の明記）: outline\_unfit に goal への優先を書く。M-2 の直しと合わせた形を示す

  ```yaml
  - id: outline_unfit
    description: >-
      outline.md に、topic.txt の主題と読者に照らして書けない節（主題の範囲外、他の節との重複、順序の矛盾）がある。
      書けない節とその理由が記憶 outline_gaps に列挙されている。note.md が全節の見出しと本文を持っていても、
      書けない節が列挙されていればこの状態とし、goal に優先する。
  ```

- 別案: goal の側に「書けない節の列挙（記憶 outline\_gaps）が無い」を足して排他にする。決定 #7 は優先を記述の中に書く方針なので、推奨案の方が筋がよい

### 中

#### M-1 plan\_outline の goal と topic\_unclear が重なりうる

- 所在: workflow.yaml 第50〜51行、第58〜61行
- 問題: 暫定の三節（要約つき）と末尾の問いを両方持つ outline.md は、両方に当たりうる。「節を決められない」で部分的には排他だが、暫定の構成を出すのは自然な振る舞いである
- 直し方（分類体系の変更なし）:

  ```yaml
  - id: topic_unclear
    description: >-
      topic.txt の主題か想定読者が曖昧で、節を一通りに決められない。決められない理由が、ユーザーに尋ねるべき問いとして
      記憶 topic_questions に列挙されている。outline.md に暫定の節が三つ以上あっても、問いが列挙されていれば
      この状態とし、goal に優先する。
  ```

#### M-2 三つの end\_state すべてで、分類されても carry が空でありうる

- 所在: workflow.yaml 第60〜61行（topic\_unclear）、第101行（outline\_unfit）、第127〜128行（findings\_blocking）
- 問題: 三つとも、end\_state の証拠をファイル（outline.md の末尾、note.md の末尾、review.json）に置いている。一方、carry は記憶（topic\_questions、outline\_gaps、review\_findings）である。restore でファイルは捨てられ、記憶が無ければ overlay されない（契約 2.3 の 2）。記述は記憶が埋まっていることを要求していないので、end\_state に分類されても、戻り先に解消の材料が届かないことがある。memory\_out は投影に入る（契約 2.4）ので、記憶を記述の条件にすれば観測できる
- 直し方（分類体系の変更なし）:
  - topic\_unclear: M-1 の案のとおり、「問いが記憶 topic\_questions に列挙されている」にする。outline.md の末尾への列挙はやめる。M-4 の誤計数もこれで消える
  - outline\_unfit: H-2 の案のとおり、「記憶 outline\_gaps に列挙されている」にする
  - findings\_blocking:

    ```yaml
    - id: findings_blocking
      description: >-
        review.json に、note.md の修正を要する指摘（主題や読者からの逸脱、節の本文が outline.md の要約の内容を
        述べていない、事実の誤り）が一つ以上あり、同じ指摘が記憶 review_findings に outline.md の節の名前とともに
        列挙されている。どの指摘も note.md を直せば解消する。
    ```

  - 各ステージの description にも、記憶に何を書くかを書き足す。例: plan\_outline は「主題か読者が曖昧で節を決められなければ、ユーザーに尋ねるべき問いを記憶 topic\_questions に書く」

#### M-3 両フェーズゲートとも、goal を満たさない状態は必ず unknown に落ちる

- 所在: workflow.yaml 第11〜13行、第58〜61行、第72〜74行、第125〜128行。README.md の「遷移の六種の被覆」
- 問題:
  - ゲートを評価するのは最終ステージが goal に達した直後である。topic\_unclear（節を決められない）も findings\_blocking（修正要の指摘が一つ以上）も、最終ステージが goal に達した状態とは両立しない。契約 3.2 の「ゲートで end\_state → 同じ辺で rollback」は、記述の上では起こらない。decisions.md #5 は「最終ステージの end\_state の記述は、フェーズ全体の不足も覆う必要があり、広くなる」と予告しているが、玩具はそうしていない
  - intake ゲートの「各節がその主題の一部」に反する状態は、write\_note の outline\_unfit と同じ不足である。ゲートで見つかれば escalate、write\_note で見つかれば自動のロールバック、と検出場所で落ち方が変わる
- 直し方（推奨、分類体系の変更なし。文書で明示する）: README.md に節を足す。案:

  > ## フェーズゲートの落ち方
  >
  > 両フェーズとも、最終ステージの end\_state は最終ステージが goal に達した状態と両立しない（topic\_unclear は節を決められない状態、findings\_blocking は修正を要する指摘がある状態）。このため、ゲートで goal を満たさない状態は unknown に落ち、escalate 後の人間の選択（再実行か、指定ステージへのロールバック）で扱う。主題の範囲外の節は、intake のゲートで見つかれば escalate、write\_note で見つかれば outline\_unfit で plan\_outline へ戻る。自己ループの禁止（論点 A）により、最終ステージ自身が直すべき不足はゲートから自動では戻せないためである。契約 3.2 の「ゲートで end\_state → rollback」の機構は、F2 の決定論テストで偽の分類器にその id を返させて確かめる。

- 別案（分類体系の変更を伴う。findings\_blocking の拡張）: findings\_blocking を、review.json に修正要の指摘が無くても note.md が topic.txt の読者から外れている状態まで広げる。この案には次の手当てが要り、玩具の最小構成を崩すので推奨しない
  - ステージの評価で goal と重ならないよう、「このステージの goal に当たる場合は goal を優先する」と書く必要がある。ところがゲートの選択肢にはステージの goal が無く、この一文が何を指すか分類器が迷う
  - ゲートの時点の review\_findings は goal に達した実行の memory\_out なので空になりやすく、戻った write\_note に直す材料が届かない（下記「計画役へ上げる事項」の 3）。review\_note が修正不要の所見も review\_findings に書く運用にしないと成り立たない

#### M-4 成果物の形式が metrics.py にしか書かれておらず、section\_count が問いを節と数える

- 所在: metrics.py 第18〜20行（`_outline_sections`）、第23〜24行（`_note_headings`）、第52〜57行（`blocking_findings`）。workflow.yaml 第43行、第83行、第111行
- 問題: outline.md の「- 節の名前: 要約」、note.md の「## 節の名前」、review.json の `{"findings": [{"blocking": …}]}` という形は、workflow.yaml にも README にも書かれていない。そのため分類器も F4 の読み手も規約を知らない。section\_count は outline.md のどこにある「- X:」の行も節と数え、要約が空の行も数える。topic\_unclear が求める末尾の問いが「- 読者: …？」の形なら、節が一つでも指標が通る（証拠参照）
- 直し方:
  - ステージの description に形式を書く。例
    - plan\_outline: 「topic.txt から、ノートの節を『- 節の名前: 一行の要約』の行として outline.md に書く」
    - write\_note: 「outline.md の節の順に、各節を『## 節の名前』の見出しとして note.md を書く」
    - review\_note: 「…指摘を review.json に `{"findings": [{"section": 節の名前, "blocking": 真偽値, "message": 文}]}` の形で書く」
  - README の構成の表の下にも同じ規約を書く
  - M-2 の直しで問いを outline.md から記憶に移せば、誤計数は起きなくなる。あわせて、要約が空の行を数えないよう、正規表現を `^- ([^:：\n]+)[:：][ \t]*\S` にする（qualitative の「各節に一行の要約がある」に合わせる）

#### M-5 findings\_blocking の例「節の抜け」が記述の他の部分と矛盾する

- 所在: workflow.yaml 第127行
- 問題: outline.md の節が note.md に無いという意味なら、write\_note の goal がすでに保証しているので、review の時点では起きない。outline.md に無い節という意味なら、note.md だけでは直せず、同じ記述の「どの指摘も note.md を直せば解消する」と矛盾する
- 直し方（分類体系の変更なし）: 「節の抜け」を「節の本文が outline.md の要約の内容を述べていない」に替える（M-2 の findings\_blocking の案に反映済み）

#### M-6 compose ゲートの指標が compose の writes に無い outline.md を読み、動くかどうかが契約の読みに依存する

- 所在: workflow.yaml 第76〜79行。契約 3.2（第76行）と 7.2（第149行）
- 問題: 3.2 は「入力はフェーズ内の全ステージの writes の和」、7.2 は「フェーズ内の全 writes を含む終了時」と書く。前者を「見えるファイルの制限」と読んで F2 を実装すると、outline.md が見えず MetricError になる。そうなると goal が選択肢から消え、玩具は一度も完了できない
- 直し方: 計画役が契約の文言を確定する（下記「計画役へ上げる事項」の 1）。玩具の側だけで塞ぐなら、compose の writes（note.md と review.json）だけで測る指標に替える（L-1 の sections\_reviewed）

### 低

#### L-1 両ゲートの quantitative がステージの指標の繰り返しで、集約述語の例になっていない

- intake の files\_nonempty と compose の sections\_covered は、強制通過を除いてゲートで必ず真になる。契約 2.2 の「指標が未達ならゲートの選択肢から goal を除く」分岐が、自然には起きない
- 提案: compose に、二つのステージの writes を突き合わせる指標を置く。例

  ```yaml
  sections_reviewed:
    description: note.md の見出しのうち、review.json に査読結果があるものの割合
    min: 1.0
    args: {note: note.md, review: review.json}
  ```

  review\_note の goal の「全節を査読した結果がある」は、ステージでは分類器だけが判定する。この指標はその見落としをゲートで捕まえる。指標の追加と、review.json の形（M-4）への section の追加が要る

#### L-2 ask\_topic の goal の強さと、再訪時の観測

- goal が曖昧さの無さまで求めていないのは、topic\_unclear を到達可能にするための意図である。README に書いておく
- 再訪時の topic\_questions は memory\_in なので投影に入らない。ask\_topic の description に「持ち帰った問い（topic\_questions）があればユーザーに尋ね、問いと回答を topic.txt に書き添える」と書き、goal に「持ち帰った問いがあった場合は、その問いと回答が topic.txt にある」を足す。そうすれば、少なくとも回答の有無は観測できる

#### L-3 review\_findings の場所の示し方

restore で note.md が捨てられ、write\_note は一から書き直す。review\_findings の各指摘は、note.md の中の位置ではなく outline.md の節の名前で場所を示すべきである（M-2 の案に反映済み）。

#### L-4 連鎖で outline\_gaps が消える

write\_note → plan\_outline（outline\_gaps）→ topic\_unclear → ask\_topic と連鎖すると、ask\_topic の carry に outline\_gaps が無いので、再び plan\_outline に来た時には消えている。主題が変わるなら古い指摘は不要なので許容する。README に一行書いておくとよい。

#### L-5 blocking\_findings が真偽値でない blocking を数える

metrics.py 第55行の `if f["blocking"]` は、文字列の `"false"` も真と数える。`f["blocking"] is True` で数えるか、真偽値でなければ MetricError にする。

#### L-6 ユーザーが依頼を変えた場合は unknown になる

ask\_topic でユーザーが依頼を意図して変えた場合は、「brief.txt の依頼と矛盾しない」が偽になって unknown に落ちる。妥当なので変えない。README に記録する。

#### L-7 「outline.md が読者を前提にしている」は観測しにくい

節の名前と一行の要約だけからは推し量るしかない。intake の qualitative を「outline.md の節と要約が topic.txt の主題の一部を扱い、topic.txt の読者に合っている」とするか、outline.md の先頭に読者を一行書く形式にする。

#### L-8 plan\_outline の残余

主題は明確だが三節に分けるには狭すぎる・広すぎる状態は unknown に落ちる。自己ループ禁止の下では妥当である。記録のみ。

## 計画役へ上げる事項（契約と決定の帰結。玩具だけでは直せない）

#2 と #5 と論点 A は固定・承認済みなので、それを変える提案ではない。

1. **フェーズゲートの状態文書が契約に定義されていない**。2.4 はステージ単位で書かれ、3.2 は指標の入力しか言っていない。あわせて、3.2「writes の和」と 7.2「全 writes を含む終了時」の食い違いもある。案: 「ゲートの指標の view は最終ステージの終了時スナップショット（範囲全体）、分類器への状態文書は最終ステージの投影」と明記する。H-1 と M-6 の深刻さがこの定義で決まる
2. **最終ステージ自身が直すべき不足は、ゲートから自動では戻せない**。#5（ゲートの end\_state は最終ステージの辺）と論点 A（自己ループ禁止）からの帰結で、そうした不足は unknown に落ちる。adopting.md（F2）に書いておかないと、F4 で同じ疑問が出る
3. **ゲートで end\_state に分類された時の carry は、goal に達した実行の memory\_out である**。分類器は記憶を書かないので、ゲートで見つかった不足の情報は carry に乗らない。#5 の解釈「最終ステージの end\_state はフェーズ全体の不足も覆う」を実際に使うには、最終ステージの本体が「goal には達したがフェーズとして懸念がある」所見を常に記憶に書く必要がある。adopting.md か契約の注記として残すべきである

## 触ったファイル

- 書いた: reports/f1-toy-minimal-review.md（このファイル）
- 副作用: 証拠のために toy-minimal のテストを実行した。その際、pyproject.toml の addopts（`--cov`）により、リポジトリ直下の .coverage（.gitignore 済み）が書き換わった。`-p no:cacheprovider` を付けたので .pytest\_cache は触っていない。既存の \_\_pycache\_\_ が更新された可能性がある（.gitignore 済み）。git 操作はしていない
