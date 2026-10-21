# toy-minimal

玩具 1。依頼（brief.txt）から短いノートを書くワークフローで、ハーネス契約と遷移の全種別を最小構成で覆う。フレームワーク本体はこの玩具を参照しない。

- workflow.yaml: ワークフロー定義（2 フェーズ、4 ステージ）
- toy\_minimal/metrics.py: 指標レジストリ
- toy\_minimal/stages/: 偽のステージ本体（決定論的なものは F2、確率的なものは F3）
- tests/: 定義と指標のテスト、（F2 以降）決定論テスト、fixtures と expectations

## 構成

| フェーズ | ステージ | 読む | 書く | end\_state → 戻り先（carry、max） |
| --- | --- | --- | --- | --- |
| intake | ask\_topic（ユーザー待ち） | brief.txt | topic.txt | （unknown のみ） |
| intake | plan\_outline | topic.txt | outline.md | topic\_unclear → ask\_topic（topic\_questions、2） |
| compose | write\_note | topic.txt, outline.md | note.md | outline\_unfit → plan\_outline（outline\_gaps、1）。フェーズ境界越え |
| compose | review\_note | topic.txt, outline.md, note.md | review.json | findings\_blocking → write\_note（review\_findings、2） |

## 遷移の六種の被覆

定義の上で起こりうることを tests/test\_definition.py が確かめる。実際に通すのは F2 の決定論テスト。

| 種類 | この玩具での例 |
| --- | --- |
| next | ask\_topic → plan\_outline → （intake のゲート）→ write\_note → review\_note → （compose のゲート）→ 完了 |
| rollback | review\_note → write\_note（review\_findings を持ち帰る） |
| max 超過 | findings\_blocking が三回目に起きると escalate |
| unknown | どのステージでも、goal にも end\_state にも当たらなければ escalate |
| 中断と再開 | ask\_topic がユーザーに尋ね、回答がまだ無ければ中断する |
| フェーズ境界越え | write\_note → plan\_outline（compose → intake）。intake のゲートは再び plan\_outline が goal に達した時に評価し直す |

## フェーズゲートの不合格

この玩具の最終ステージ（plan\_outline、review\_note）の end\_state は、そのステージ自身の不足だけを述べる。ゲートは最終ステージが goal に達した直後に評価するので、ゲートの不合格はどの end\_state にも当たらず unknown（escalate）になる（契約 3.2 の帰結）。主題の範囲外の節は、write\_note が見つければ outline\_unfit で自動に戻り、intake のゲートで見つかれば escalate する。最小構成を保つためにこのままにする。ゲートから end\_state で戻る経路は、契約適合テストのシナリオで確かめる（F2）。

## 成果物の形式

- outline.md: 「## 節」の見出しの下に「- 節の名前: 一行の要約」を並べる。他の見出しの下の行は節として数えない
- note.md: 節ごとに「## 節の名前」の見出しと本文
- review.json: `{"findings": [{"section": 節の名前, "blocking": 真偽値, "comment": 指摘}]}`
