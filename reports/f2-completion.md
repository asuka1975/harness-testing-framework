# F2 完了判定（検証役）

- 日付: 2026-10-22
- 役割: 検証役（第三者。plan.md 第5.9節）。実装の作業過程（docs/progress.md、過去の reports/）は判定の根拠にしていない。読んだのは仕様（docs/plan.md の第2節・第5.8節・第6節 F2・第7節、docs/decisions.md の A2・D-2〜D-5 ほか、contract/contract.md、contract/conformance/README.md、各 JSON Schema）と成果物だけ
- 対象: src/harness\_testing\_framework/runtime/、testing/harness/、contract/conformance/（合成ワークフローとシナリオ 20 件）、examples/toy-minimal/（シナリオ 7 件、フィクスチャ、toy\_minimal/stages/deterministic.py、指標）、tests/、docs/adopting.md、docs/api.md、scripts/check.sh
- 書いたもの: この文書だけ。実験はリポジトリの写しを一時ディレクトリに作って行い、原本は変更していない。git は使っていない

## 総合判定: 準正常（直せば満たす）

第6節 F2 の完了条件五つは、字義どおりにはすべて満たしている。toy-minimal のシナリオで六種の遷移と escalate の四択を通し、参照ランタイムは契約適合テスト 20 件を通し、記録再生でスナップショットの列が一致し、runtime の行カバレッジは 98%。期待する実行記録は、指定の 9 件を契約と要約規則から自分で導き直し、すべて一致した。参照ランタイムの restore、overlay、回数、ゲートの無効化と再評価、訪問の番号は、自作のシナリオでも契約どおりに動いた。決定 A2・D-4・D-5 は反映されていて、本体に玩具や特定のツール・LLM の名前は無い。

それでも「正常」にしないのは、次の理由による。

1. **高-1: 契約適合テストがスナップショットを見ていない。** 契約 第10節は、契約適合テストを「期待する実行記録とスナップショットの列の組」と定める。一方、contract/conformance/README.md の実行手順 5 が比べるのは、実行記録の要約、最後の状態、記憶（含むかどうか）、注記の数だけで、スナップショットに触れていない。scenario.schema.json の `expect` にも、スナップショットを書く欄が無い。そのため、restore をしない（戻っても前の区間のファイル・記憶・ゲートをそのまま持ち越す）ランタイムが 20 件すべてを通る。変異で確かめた結果、restore を外す・ゲートを無効化しない・carry 以外の記憶やファイルを捨てない、の各変異で 271 件のテストがすべて通った。三操作の一つ（restore + overlay）とフェーズ境界越えの意味論（ゲートの無効化）を、「契約を満たすかを判定する唯一の手段」（第5.8節）が判定できない。参照ランタイム自身も、restore の正しさをどのテストも固定していない
2. 参照ランタイムに、契約の文言からの逸脱が二つある。中-1: 中断時に保留中の質問を保存しない（契約 3.3）。中-2: 記録の鍵に実行の種が入っていない（契約 第9節）
3. 記録再生と中断の仕組みに穴がある。中-3: 記録しながら中断・再開すると、LLM を同じ鍵で二度呼び、再生が記録と違う並びになる（実証した）。中-4: 本体が `AwaitingAnswer` や `ReplayOnly.Missing` を握りつぶすと、中断や再生の停止が起きない

直す点は二つに分けた。

判定を変えるもの（これが残る限り準正常）:

- 高-1: シナリオに開始時スナップショット（ファイル、記憶の完全一致、ゲート）の期待を加え、戻りのあるシナリオに書く。契約 第10節の定義と成果物が食い違っている
- 中-1: 保留中の質問を実行の状態に保存して公開する。契約 3.3 の文言からの逸脱
- 中-2: 記録の鍵に実行の種を入れる。契約 第9節の文言からの逸脱
- 中-3: 記録中の再開で LLM の応答を再利用する（契約 3.3 にも書く）。完了条件「記録再生で同一スナップショット」の反例がある
- 中-4: 本体が握りつぶした中断の合図と再生の失敗を、文脈の側で覚えておいて実行に反映する。契約 3.3 と第9節の強制が崩れる反例がある

F2 の中で直すのが安いが、完了条件の判定は変えないもの:

- 中-5: 偽の本体が回答を観測できるようにし、回答の再生を確かめる（テストの強さ）
- 中-6: マニフェストの正規形のテストベクトルを置き、数の書き方を契約で決める（テストの強さと契約の細部）
- 中-7: 評価の入力（選択肢の順序、状態文書の中身）を確かめる（テストの強さ）
- 中-8: adopting.md / api.md の不足を補う。F4 の利用者が自分のテストを走らせる方法、Runtime の引数と結果の読み方（初版の不足。F4 が試す対象でもある）

高-1 と中-5〜中-7 の一部は、保護ファイル（contract/ の下）の変更になる。直せるのは計画エージェントだけ（第5.9節）。中-3 と中-6 は契約への追記になる。高-1 で加えるシナリオの原型として、自作のシナリオ 4 件を付録に載せた。

## 項目ごとの判定

### 1. 第6節 F2 の完了条件

| 完了条件 | 判定 | 証拠 |
| --- | --- | --- |
| toy-minimal で6種の遷移を全て通す | 満たす | `test_all_six_transition_kinds` が通る。`transition_coverage` の判定規則も読んで確かめた（next/complete、edge 付きで境界を越えない rollback、max\_exceeded、それ以外の理由の escalation、suspend の後の resume、境界越えの rollback の後の同じフェーズのゲート評価）。被覆するシナリオは happy\_with\_user（next、中断と再開）、topic\_unclear\_rollback（rollback）、review\_max\_exceeded（max 超過）、outline\_unknown\_rerun ほか（unknown）、review\_and\_outline\_rollbacks（境界越え）。ただし 6 の「ゲートの無効化」は実行記録に現れず、確かめられていない（高-1） |
| escalate の4つの選択肢が動く | 満たす | `test_all_four_escalation_decisions` が通る。再実行（outline\_unknown\_rerun）、運用者のロールバック（review\_operator\_rollback）、goal 到達扱い（review\_max\_exceeded、注記 1）、中止（write\_error\_abort）。選んだ後の並びは期待の実行記録で確かめている。運用者のロールバックで復元が正しいかは確かめていない（高-1） |
| 参照ランタイムが契約適合テストを通す | 満たす（ただしテストが弱い） | contract/conformance のシナリオ 20 件が通り、実行記録の各出来事が trace.schema.json に、スナップショットが snapshot.schema.json に適合する。ただし契約適合テストは restore を判定できない（高-1） |
| 記録再生で同一スナップショットが得られる | 満たす（ただし穴がある） | 再生の検査（契約適合 3 件、toy-minimal 2 件）が通る。自分でも 20 件すべてを記録してから再生し、スナップショットの列と実行記録の全体が一致した。ただし中断・再開と揺らぐ LLM を併用すると一致しない（中-3） |
| runtime の行カバレッジ 90% 以上 | 満たす | 98%（checkpoint 97%、loader 100%、model 98%、oracle 100%、recorder 100%、runner 98%）。scripts/check.sh が `--fail-under=90` で確かめる。未被覆の行に、本体が memory\_in を読む成功経路（runner.py の `read_memory` の return）が含まれる（低-10） |

### 2. 期待する実行記録が契約に照らして正しいか（最重要）: 満たす

指定の 9 件について、契約 2.2・2.3・3.1〜3.4.1 と conformance/README.md の要約規則だけから並びを導き、ファイルの期待と比べた。9 件とも一行ずつ一致した。実行して、各評価の指標の値と選択肢、各訪問の開始時スナップショットも導いたとおりであることを確かめた。

判断が入る点と、導いた結果:

- **phase\_crossing\_rollback**: s3#1 は指標を満たすので選択肢は [goal, e3\_back, e3\_retry, unknown]。台本で e3\_back を選ぶ。辺 s3/e3\_back は max 1 で回数 0 なので、回数を 1 にして戻る。p2 から p1 へ戻るので `rollback s3 -> s2 [e3_back 1] crossing`。s2 の直近の開始時スナップショット（s1#1 の終了時。ゲートは空）を復元し、m32 を重ねる。s2#2 が goal になると、ゲートの鍵は最終ステージの訪問の回数で p1#2。ゲートを評価し直して `gate_pass s2`、`next s2 -> s3` と進む。s3#2 から p2#2 を経て complete になる。記憶 m32 は s2 の開始時に重なった後、誰も消さないので最後まで残る
- **gate\_failure\_rolls\_back**: s2#1 はステージとしては goal。ゲートでは gate1.flag が偽で指標を満たさないので、選択肢から goal を除いて [e2\_back, unknown] になる（2.2）。台本 p1#1 で e2\_back を選ぶ。最終ステージの e2\_back の辺で戻り、回数も同じ辺で数える（3.2）。同じフェーズなので `rollback s2 -> s1 [e2_back 1]` で、crossing は付かない。carry の m21 は goal に達した実行の memory\_out から取る（3.2 の帰結）。再びゲートに達した時の鍵は p1#2
- **max\_exceeded\_continue\_as\_goal**: s2 は s2.flag が偽で選択肢は [e2\_back, unknown]。1 回目と 2 回目は戻る（回数 1、2）。3 回目は回数 2 = max なので escalate する（3.1「三回目に escalate」）。escalate の transition は要約に出ないので、`escalation s2 max_exceeded -> continue_as_goal` の一行になる。ステージの評価からの escalate で、s2 はフェーズの最終ステージなので、ゲート（p1#3）を評価してから gate\_pass に進む（3.4 末尾）。注記は 1
- **low\_confidence\_operator\_rollback**: s3#1 の確信度 0.3 は閾値 0.5 未満なので unknown になる。運用者は s2 へ carry [m32] で戻すことを選ぶ。m32 は s2 の memory\_in にあるので、この選択は有効。`escalation s3 unknown -> rollback` の後に、edge が null の `rollback s3 -> s2 [operator] crossing` が続く。s2#2 からゲート p1#2、p2#2 と評価し直す
- **operator\_defers**: s1#1 の台本は choice null で「答え無し」なので unknown。運用者が保留し、`escalation s1 unknown -> pending`、`end awaiting_operator` で止まる。再開すると escalation（選択つき）を書き直してから続け、再実行は新しい訪問なので `start s1#2`（3.3、D-4）
- **resume\_replays\_answers**: s1#1 は一つ目の質問に回答 A を得て、二つ目で保留されて中断する（stage\_end は書かない）。再開すると `resume s1` の後に同じ訪問の `start s1#1` を書く（3.3）。一つ目は保存した A を再生し、二つ目に新しい回答 B を使う。ただし回答の中身は要約にも記憶にも現れないので、「一つ目を再生した」ことは並びからは確かめられない。確かめられるのは、台本を使い切らないことだけ（中-5）
- **self\_rollback**: s3#1 で e3\_retry を選び、辺は自分自身へ戻る（A2）。max 1、同じフェーズなので `rollback s3 -> s3 [e3_retry 1]`。いま終わった訪問の開始時（ゲートは [p1]）を復元し、m33 を重ねる。p2 のゲートの鍵は p2#2
- **toy-minimal review\_max\_exceeded**: review\_note は blocking\_findings が 1 で max 0 を超え、指標を満たさないので選択肢は [findings\_blocking, unknown]。回数 1、2 と戻り、3 回目で max 2 を超えて escalate する。goal 到達扱いの後、review\_note は compose の最終ステージなのでゲート compose#3 を評価する。sections\_covered が 1.0 で goal を選択肢に含み、goal、gate\_pass、complete と続く。注記は 1
- **toy-minimal review\_and\_outline\_rollbacks**: write\_note#2 は gaps のフィクスチャで sections\_covered が 1/3 になり、選択肢は [outline\_unfit, unknown]。辺は max 1 で回数 1。compose から intake へ戻るので crossing が付く。plan\_outline の直近の開始時（ask\_topic#1 の終了時。ゲートは空）を復元し、outline\_gaps を重ねる。直前に持ち帰った review\_findings は捨てられる。plan\_outline#2 の後に intake#2 でゲートを評価し直し、review\_note#2（指摘 0）から compose#2 を経て complete になる

残りの契約適合シナリオ 13 件と toy-minimal 5 件も同じ規則で読み、矛盾は無かった。ただし missing\_carry\_item\_warns は、警告を rollback の transition の後に置くことを期待している。契約 3.4.1 は warning の位置を定めていないので、警告を先に書く別の実装は落ちる（低-7）。

実装と期待が同じ誤解を共有している箇所は、並びの上には見つからなかった。危ういのは並びではなく、並びに現れないもの（復元の中身、評価の入力）のほうで、そこはどちらのテストも見ていない（高-1、中-7）。

### 3. 実行時の強制（契約 第8節、2.1 の 3〜5）を負の例で確かめる: おおむね満たす（穴あり）

合成ワークフロー（contract/conformance/workflows/basic.yaml）に、自分で書いた本体を束縛して実行した。

| 負の例 | 結果 | 判定 |
| --- | --- | --- |
| s1 が、範囲内で自分の writes に無い s3.txt を書く | contract\_violation。評価をせずに escalate | 契約どおり |
| s2 が、s1 の書いた s1.txt を消す | contract\_violation | 契約どおり（削除も変化） |
| s1 が、inputs の in.txt を書き換える | contract\_violation | 契約どおり |
| s2 が、s3 の writes にあるディレクトリ（out/）の下に書く | contract\_violation | 契約どおり |
| s3 が、自分の out/ の下の深い階層に書く | 通る | 契約どおり |
| 範囲外のファイル（junk.log、tmp/a）を書く | 警告 2 件。スナップショットには入らない | 契約どおり |
| 宣言した writes を書かない | 違反にならず、評価で unknown | 契約どおり（D-4） |
| memory\_in に無い記憶を読む／memory\_out に無い記憶を書く | contract\_violation | 契約どおり |
| 上の違反を本体が握りつぶす | それでも contract\_violation | 契約どおり |
| awaits\_user の無い s2 が `context.user_io.ask` を呼ぶ | contract\_violation | 契約どおり |
| awaits\_user の無い s2 が、文脈オブジェクトの `ask()` を直接呼ぶ | 回答を受け取って完了する。検出されない | 穴（低-1） |
| awaits\_user の無い s2 が、`AwaitingAnswer` を自分で送出する | 実行が中断する | 穴（低-2） |
| awaits\_user の s1 が、ユーザーの保留（`AwaitingAnswer`）を握りつぶす | 中断せずに goal に進み、完了する | 穴（中-4） |
| 再生中に本体が `ReplayOnly.Missing` を握りつぶす | 再生が止まらずに完了する | 穴（中-4。契約 9「再生の失敗として止める」） |
| 本体が自分の例外を握りつぶす | そのまま進む | 本体の自由で、検出の対象外 |
| 作業領域の外（親ディレクトリ）に書く | 何も記録されない | 低-5 |
| 範囲内のパスを、作業領域の外のファイルへの記号リンクにする | リンク先の内容がスナップショットと状態文書に入る | 低-5 |
| 分類器が確信度 NaN、または 7.0 を返す | goal として採る。7.0 は trace.schema（0〜1）に反する値のまま実行記録に書かれる | 低-3 |
| 分類器が例外を出す／指標が `MetricError` 以外の例外を出す | `start()` が例外で抜ける。run\_end も、再開できる状態も残らない | 低-3 |
| 運用者が後ろのステージへのロールバックを返す | escalation（選択つき）を書いた後に `OperatorDecisionInvalid` で止まる。run\_end は無い | 低-4 |

### 4. restore と overlay、回数、ゲート、訪問の番号: 実装は契約どおり。ただしテストが固定していない

実装の確認（シナリオを実行し、訪問ごとの開始時スナップショットを出力した）:

- phase\_crossing\_rollback: s2#2 の開始時は files [in.txt, s1.flag, s1.txt]、gates []、memory {m32}。s3 の書いたファイルは消え、p1 のゲートは未通過に戻る。s3#2 の開始時は gates [p1]
- self\_rollback: s3#2 の開始時は s3#1 の開始時と同じファイルで、gates [p1]、memory {m33}
- 自作のシナリオ（契約適合のシナリオと同じ形式）:
  - latest\_start\_restored: s2 を二度訪れてから s3 が e3\_back で戻る。s2#3 の開始時は s2#2 の開始時（m21 を持つ）から作られ、s3 が書いた m33 と out/x は捨てられる。「直近の訪問の開始時」を守っている
  - rerun\_then\_edge\_again: max 超過から再実行した s2#4 が再び e2\_back になると、すぐに max\_exceeded で escalate する。回数は数え直さない（3.1）
  - suspend\_after\_rollback: s1#2 で中断して再開すると、同じ訪問（`start s1#2`）で、種も同じ値になる。その後の再実行は s1#3 で、種が変わる（3.3、3.4）
  - gate\_unknown\_rerun: ゲートが unknown になり再実行を選ぶと、最終ステージを s2#2 として実行し直し、ゲートの鍵は p1#2 になる
  - continue\_after\_stage\_error: 本体の例外の後に goal 到達扱いを選ぶと、次のステージは失敗したステージの開始時スナップショットから始まる（本体の書き込みは捨てられる）。妥当な振る舞いだが、契約に書かれていない（低-6）
- 運用者が escalate したステージ自身へ戻すことは受け付け、後ろのステージへ戻すことは拒む（A2、3.4）

テストが固定していないこと（変異テスト）: 参照ランタイムに一つずつ変異を入れ、全テスト（271 件）を走らせた。

| 変異 | 結果 |
| --- | --- |
| restore をしない（現在のスナップショットに carry を重ねるだけ） | 271 件すべて通る |
| ゲートを無効化しない（restore の後も現在のゲートを残す） | 271 件すべて通る |
| carry 以外の記憶を捨てない | 271 件すべて通る |
| 戻った区間のファイルを捨てない | 271 件すべて通る |
| escalate 後の選択で辺の回数を数え直す | 271 件すべて通る |
| 本体の種をステージと訪問の回数に依存させない | 271 件すべて通る |
| 状態文書に memory\_in を含める（2.4 違反） | 271 件すべて通る |
| ゲートの状態文書からフェーズのファイルを除く（2.4 違反） | 271 件すべて通る |
| 選択肢の順序で goal を最後にする（2.2 違反） | 271 件すべて通る |
| マニフェストを正規形でなく書く（キー順を保たない、空白・改行あり、ASCII エスケープ） | 271 件すべて通る |
| 再開時に保存した回答の代わりに別の文字列を返す | 271 件すべて通る |
| ゲートの指標を測らない | 落ちる（検出される） |
| 分類器を recorder を経由せずに呼ぶ | 再生の検査で 6 件落ちる（検出される） |

参照ランタイムがいま正しいことは上の実験で確かめた。しかし restore、overlay、ゲートの無効化、回数の規則（3.1）の退行は、テストでは捕まらない。契約適合テストとしては、これらを実装しない他のランタイムを適合と判定してしまう（高-1）。

### 5. 記録再生の検査が、外を呼ばずに再生していることを示しているか: おおむね示している（甘い点あり）

示していること:

- `ReplayOnly` は `live` を一度も呼ばず、記録に無ければ `ReplayOnly.Missing` を送出する。`test_replay_with_missing_record_fails_loudly` が、記録の最後の一行を削ると止まることを確かめる
- 再生では、指標・分類器・運用者・ユーザーの代わりに `Unreachable` を束縛する。recorder を迂回した呼び出しはこれで捕まる。分類器を迂回させる変異は 6 件の失敗で検出された
- 再開の入力も記録を通る。再生では、ユーザーの回答に空文字、運用者の選択に「中止」を渡す。それでも記録どおりに進むことを、契約適合の 20 件すべてで確かめた（記録から再生して、スナップショットの列と実行記録の全体が一致）。operator\_defers（escalate 待ちからの再開）も一致した

甘い点:

- 回答の中身を誰も観測しない。偽の本体は回答を捨てるので、保存した回答を取り違えて再生する変異は 271 件すべてを通る。再生で再開の回答を記録でなく引数から取る変異も、再生の検査を通る（中-5）
- 再生の検査の対象は、契約適合 3 件と toy-minimal 2 件だけ。escalate 待ちからの再開（記録の `resume_decision`）を含むシナリオは、再生の検査に入っていない。比べるのも要約とスナップショットの id で、実行記録の全体ではない（低-11）
- LLM を伴う再生は単体テスト 1 件だけで、中断・再開と組み合わせた場合を見ていない。組み合わせると一致しない（中-3）
- 記録の鍵に種が入っていないので、種を 1 から 999 に変えて再生しても `Missing` にならず完了する（中-2）。契約 第9節は種を鍵に含めると定めている

### 6. F4 の利用者の立場で、adopting.md と api.md（と toy-minimal、公開 API の文書）だけでハーネスを作れるか: おおむね作れる（不足あり）

ワークフロー定義の書き方、三層、carry と max、ゲートの帰結、整合性検査、指標レジストリ、ステージ本体の文脈、束縛するもの、最小の組み立て例（`test_docs.py` で実際に動く）、シナリオの書き方、六種と四択、契約適合テストの位置づけは書かれている。ハーネスを作り始めることはできる。

足りないもの:

- **自分のテストと型検査を走らせる方法（中-8）**: toy-minimal のテストが動くのは、最上位の pyproject.toml の pytest の testpaths と pythonpath、mypy の files と mypy\_path に examples/toy-minimal が直書きされているから。F4 の利用者は examples/software-factory/ の下しか書けないので、自分のパッケージを import できる形でテストを走らせ、scripts/check.sh と CI に乗せる手順が要る。adopting.md に記述が無い
- **Runtime の引数と結果の読み方（中-8）**: api.md は `Runtime` を start / resume としか書いていない。workdir の使われ方（workspaces/ の作り方）、threshold の既定値、state\_limit（状態文書の上限。契約は「ハーネスの設定」とする）、recorder、llm、user\_io の意味が無い。最後のスナップショットや成果物の取り出し方（`RunState.current`、`Runtime.snapshot`、`BlobStore.get`）も無い
- **中断中の質問の取り出し方**: 別のプロセスで再開する運用では、何を尋ねているかが要る。しかし状態に保存されていない（中-1）
- **整合性検査の `--metrics-file` の形式**（`metrics: [名前, ...]`）が api.md と adopting.md に無い。`--registry` の import パスの通し方も書かれていない（低-13）
- **実在のツールに裏づけられた指標の作り方**: 指標は読み取り専用の view しか受け取らない。ビルドやテストを走らせるには、view を一時ディレクトリに書き出す必要があるが、その指針が無い。F4 が求める「変更パスの範囲」の指標は、終了時の view だけからは測れない。本体が変更を成果物に書く、などの回避が要る。F4 の adopting-gaps に出る見込みが高い（低-13）
- **雛形 harness-plan-template.md が未作成**: 計画書では F5 の成果物だが、F4 のプロンプトは読むものに挙げている。F2 の不足ではないが、F4 の着手前に扱いを決める必要がある（低-14。計画書の不整合）

### 7. 汎用性の規律（第5.8節）: 満たす

- src/ の下を、玩具のステージ名・フェーズ名・成果物名（topic、outline、note、review、brief、intake、compose）、software factory、特定の分類器（Jev、System One）、LLM ベンダー、定理証明器の名前で検索した。一致は `default_factory` の部分一致だけだった
- 契約適合テストは合成ワークフロー（s1〜s3、p1〜p2）を使い、玩具を参照しない（D-4）
- 偽物（`ScriptedBody` ほか）と `ConformanceRegistry` は、シナリオの形式だけに依存する。玩具の本体は、玩具のフィクスチャと指標レジストリを束縛するだけ
- 状態文書の見出し行の日本語は、契約 2.4 で定めたもので、本体の前提ではない

### 8. 決定の反映（A2、D-4、D-5）: 満たす（細部に指摘あり）

- **A2**: 自分自身への戻りは、ワークフロー（basic.yaml の s3/e3\_retry）、シナリオ self\_rollback、運用者のロールバックで通る。後ろへの戻りは拒む。restore は、いま終わった訪問の開始時スナップショットになる
- **D-4**:
  - 再開は同じ訪問で、再実行は新しい訪問（自作シナリオで確認）
  - 実行記録の並びは 3.4.1 どおり。保留からの再開では escalation を書き直す。seq は中断を跨いで続き、run\_end は複数ありうる
  - 宣言した writes を書かなくても違反にならず、範囲内の削除は違反になる
  - 状態文書の見出し行がある
  - マニフェストの正規形を実装している（キーの順序、区切り、UTF-8、末尾の改行なし、ゲートはフェーズの順、注記は古い順）。ただし正規形を固定するテストベクトルが無く、数の書き方も決まっていない。「他の言語の実装が同じ id を出せる」という D-4 の目的は、まだ確かめられない（中-6）
  - シナリオの形式は contract/conformance/ にあり、玩具も同じ形式で書いている
- **D-5**: api.md は、公開 API の文書として、言語に依存しない仕様（workflow.schema.json、contract.md、snapshot / trace / scenario の schema、conformance/README.md）を列挙している。test\_docs.py は、adopting.md と api.md が plan / progress / decisions / src を参照しないこと、公開名がすべて api.md にあることを確かめる。いずれも満たす
- **D-2**: 回数をスナップショットに入れず、数え直さない。ゲートの状態と注記はスナップショットに入れる。作業領域は毎回作り直す。範囲外は捨てて警告する。いずれも実装どおり。ただし「数え直さない」はテストで固定されていない（高-1 の変異表）

## 実行したコマンドと出力の要旨

すべてリポジトリの写しで実行した。

- `scripts/check.sh`
  - ruff check、ruff format --check、mypy（38 ファイル）は通過
  - pytest は 271 passed
  - runtime の行カバレッジは 98%（`--fail-under=90` を通過）
  - wheel にスキーマ 4 件が同梱されている
- `coverage report --include=".../runtime/*"`: runtime の合計は 780 文中 12 行が未被覆で 98%。未被覆の行は checkpoint 4、model 2、runner 6
- 開始時スナップショットの観察: 契約適合のシナリオを `run_scenario` で実行し、実行記録の stage\_start / stage\_end が指すスナップショットの files / memory / gates を訪問ごとに出力した（第4項の結果）
- 自作シナリオ 5 件を `run_scenario` で実行し、偽の本体を包んで各訪問の種も出力した（第4項）
- 負の例: 合成ワークフローに自作の本体を束縛して `Runtime.start` を実行した（第3項の表）
- 変異テスト: pytest のプラグインで、参照ランタイムの関数を一つずつ差し替えてから全テストを実行した（第4項の表）。たとえば restore を外す変異は、runner の `restore_overlay` を `lambda start, current, carry: orig(current, current, carry)` に差し替えたもの
- 記録再生:
  - 契約適合の 20 件をすべて記録してから再生し、スナップショットの列と実行記録の全体が一致した
  - phase\_crossing\_rollback を種 1 で記録し、種 999 で再生すると、`Missing` にならず完了した。記録の鍵の例は `["metric", ["stage", "s1", 1, "flag"], <要求のハッシュ>]` で、種が無い
  - 中断・再開と LLM の併用: 本体が LLM の一回目の応答なら質問し、二回目の応答なら質問しない、という形にした。記録すると LLM が 2 回呼ばれ、記録に同じ鍵が二つ残った。再生では後の応答が使われて中断が起きず、実行記録が記録時と一致しなかった
  - 再生中に本体が `ReplayOnly.Missing` を握りつぶすと、実行は completed で終わった
- 中断の直後に `RunState.to_json()` を出力すると、`"pending": {"kind": "user"}` だけで、質問が無かった

## 指摘の一覧

| # | 重大度 | 内容 | 直し方 |
| --- | --- | --- | --- |
| 高-1 | 高 | 契約適合テストがスナップショットを見ない。契約 第10節の「期待する実行記録とスナップショットの列の組」になっていない。restore・ゲートの無効化・carry 以外の記憶とファイルの破棄・回数を数え直さないこと（3.1）を外した変異が、271 件すべてを通る。`expect.memory` は「含む」だけなので、捨てられるべき記憶が残っていても気づかない。toy-minimal の決定論テストも同じ | scenario.schema.json と conformance/README.md に、開始時スナップショットの期待を加える。例: `expect.starts["s2#2"] = {files: {path: 内容}, memory: {...}, gates: [...]}`。記憶は完全一致で比べる。少なくとも phase\_crossing\_rollback、self\_rollback、gate\_failure\_rolls\_back、low\_confidence\_operator\_rollback、rollback\_with\_carry、missing\_carry\_item\_warns と、回数の規則を見る max 超過からの再実行で同じ辺を再び踏むシナリオに書く。toy-minimal の戻りのシナリオにも書く。保護ファイルなので計画エージェントが行う |
| 中-1 | 中 | 中断時に保留中の質問を保存しない。`RunState.pending` は `{"kind": "user"}` だけで、契約 3.3「保留中の質問…を保存する」に反する。別のプロセスで再開する運用者やユーザー入出力は、何を尋ねているかが分からない | 中断時に質問（文と選択肢）を `pending` に保存する。api.md と adopting.md 第7節に取り出し方を書く |
| 中-2 | 中 | 記録の鍵に実行の種が入っていない（契約 第9節）。別の種で再生しても `Missing` にならない。F3 で種を変えて N 回記録すると、鍵が衝突する | recorder の鍵に実行の種を含める。種の違う再生が `Missing` になるテストを足す |
| 中-3 | 中 | 記録しながら中断・再開すると、再開で同じ鍵の LLM 呼び出しを外へもう一度出す。記録に同じ鍵が二つ残り、再生は後の応答を使う。応答が揺らぐ LLM では、記録した実行と再生した実行の並びが変わる（実証）。契約 第9節の「同じスナップショットの列と同じ実行記録」が崩れる | 記録中は、記録済みの鍵を記録から返す（記録か再生か）。または訪問の中の LLM 応答を実行の状態に保存し、再開時に再生する。契約 3.3 に、再開時の LLM 応答の扱いを書き足す |
| 中-4 | 中 | 本体が握りつぶすと強制が効かない経路が二つある。`AwaitingAnswer`（中断が消え、回答の保留のまま goal に進む）と `ReplayOnly.Missing`（再生が止まらない）。契約違反は握りつぶしても検出する作りなのに、この二つは同じになっていない | 文脈に「保留を受けた」「再生に失敗した」の印を持たせる。本体が返った後に印を見て、中断または再生の失敗にする。負の例のテストを足す |
| 中-5 | 中 | 回答の再生を確かめられない。偽の本体が回答を捨てるので、保存した回答を取り違える変異と、再開の回答を記録でなく引数から取る変異が、検査を通る。resume\_replays\_answers の説明（一つ目を再生し、二つ目に新しい回答を使う）を、テストが確かめていない | conformance/README.md の偽の本体に、回答を作業領域のファイルか記憶へ書く項目を足す（例: `answers_to: path`）。期待に回答の中身を含める。再生の検査に operator\_defers を足し、実行記録の全体を比べる |
| 中-6 | 中 | マニフェストの正規形（契約 第5節）を固定するテストベクトルが無い。正規形でない直列化に変えても全テストが通る。数の書き方も契約に無い（Python は 1.0、1e+20 と書く。他の言語では 1、100000000000000000000 になりうる）。D-4 の「他の言語の実装が同じ id を出せる」を確かめられない | contract/examples に、マニフェストと正規形のバイト列と id の組をテストベクトルとして置き、テストで照合する。数の正規形を契約に書く（RFC 8785 に従う、または記憶の数の範囲を決める）。契約への追記になる |
| 中-7 | 中 | 評価の入力をどのテストも見ていない。選択肢の順序（2.2）、状態文書に memory\_in を入れないこと、ゲートの状態文書がフェーズ内の reads と writes の和であること（2.4）が対象。どれも変異が全テストを通る。偽の分類器は見出し行しか読まないので、契約適合テストでも判定できない | 実行記録の evaluation の options を要約か期待に含める。シナリオの classify に、状態文書が含むべきもの／含んではならないもの（ファイルの見出し、記憶の名前）を書ける項目を足す。偽の分類器は、それが満たされない時に「答え無し」を返す |
| 中-8 | 中 | F4 の利用者向けの文書が足りない。(a) examples/software-factory/ のテストと型検査を走らせ、check.sh と CI に乗せる方法。pyproject の pytest / mypy の設定は toy-minimal を直書きしている (b) Runtime の引数（workdir、threshold、state\_limit、recorder、llm、user\_io）の意味と既定値 (c) 最後のスナップショットと成果物の取り出し方 | (a) adopting.md にハーネスのパッケージの置き方と、テストの登録方法を書く。利用者が本体の設定を書き換えずに済む仕組み（examples の下を自動で見つける設定など）を本体側で用意する (b)(c) api.md に引数の表と `RunState` の主な欄、`Runtime.snapshot` / `BlobStore.get` を加える |
| 低-1 | 低 | 文脈オブジェクトの `ask()` が公開名なので、直接呼ぶと awaits\_user の検査を迂回できる | `_ask` にするなど、迂回できない形にする |
| 低-2 | 低 | awaits\_user の無いステージの本体が、`AwaitingAnswer` を自分で送出すると中断する | awaits\_user の無いステージの中断の合図は、契約違反として扱う |
| 低-3 | 低 | 分類器の確信度が NaN や 1 を超える値でも採る。超える値はそのまま実行記録（スキーマは 0〜1）に書かれる。分類器の例外や、指標の `MetricError` 以外の例外で、run\_end も再開できる状態も残さずに落ちる | 不正な確信度と分類器の例外は「答え無し」（unknown）にする。指標の想定外の例外は測定の失敗にするか、少なくとも状態を保存してから止める |
| 低-4 | 低 | 運用者の不正な選択で、escalation（選択つき）を書いた後に例外で止まり、run\_end の無い実行記録が残る。契約に無効な選択の扱いが無い | 選択を検証してから escalation を書く。無効な選択の扱い（拒んで escalate 待ちに戻すなど）を契約 3.4 に書く |
| 低-5 | 低 | 作業領域の外への書き込みは記録されない。範囲内のパスを記号リンクにすると、リンク先（作業領域の外）の内容がスナップショットと状態文書に入る | 走査で記号リンクを拒む（契約違反にする） |
| 低-6 | 低 | 本体の例外・契約違反の後に goal 到達扱いを選ぶと、次のステージは失敗したステージの開始時スナップショットから始まる。妥当だが契約に無い | 契約 3.4 に明記する |
| 低-7 | 低 | 警告（carry の欠落など）を実行記録のどこに書くかが、契約 3.4.1 に無い。missing\_carry\_item\_warns は rollback の後を期待している | 3.4.1 に warning の位置を書く |
| 低-8 | 低 | `test_seed_depends_on_stage_and_visit` は実行の種を変えているだけで、ステージと訪問への依存を確かめていない。依存を外す変異が通る | 同じ実行の中で、ステージと訪問ごとに種が変わることを確かめる |
| 低-9 | 低 | 台本が尽きた時の偽のユーザーと運用者の振る舞いが、conformance/README.md に無い。参照実装はどちらも例外にする | README に書く。他の言語の実装が同じ振る舞いをできるようにする |
| 低-10 | 低 | 本体が memory\_in を読む成功経路を、どのテストも通らない（runner.py の `read_memory` の return が未被覆）。carry で持ち帰った記憶を本体が読めることが固定されていない | 偽の本体に記憶を読む項目を足すか、単体テストを足す |
| 低-11 | 低 | 再生の検査は要約とスナップショットの id を比べるだけで、実行記録の全体は比べない。escalate 待ちからの再開を含むシナリオが対象に無い | 全出来事の一致を比べる。operator\_defers を対象に加える（中-5 と同時に） |
| 低-12 | 低 | goal 到達扱いの注記の「誰が」（`by`）は任意で、シナリオの形式でも書けない。契約 3.4 は「注記（誰が、なぜ）」とする | 運用者の選択に `by` を必須にするか、ランタイムが運用者の識別を補う |
| 低-13 | 低 | adopting.md / api.md に無いこと: `--metrics-file` の形式、`--registry` の import パス、実在のツールに裏づけられた指標の作り方（view の書き出し）。「変更パスの範囲」は終了時の view だけからは測れない | 文書に書き足す。「変更パスの範囲」は、F4 の adopting-gaps を見て、指標に開始時の view を渡すかを決める |
| 低-14 | 低 | 計画書の不整合: F4 のプロンプトは harness-plan-template.md を読むものに挙げているが、雛形は F5 の成果物 | 人間が、F4 の時点で雛形を作るか、プロンプトから外すかを決める |

## 付録 自作のシナリオ（高-1 の追加シナリオの原型）

第4項で使った自作のシナリオ 4 件。contract/conformance/scenarios/ に置ける形にしてある（workflow は `../workflows/basic.yaml`）。いまの scenario.schema.json に適合し、参照ランタイムで期待どおりに通ることを、写しの上で確かめた。期待の実行記録は契約 3.1・3.3・3.4・3.4.1 と照らして確かめたもの。各ブロックの末尾の注釈は、観測した開始時スナップショット。高-1 でスナップショットの期待の欄を加えたら、そこに書く値の候補になる。

```yaml
scenario: latest_start_restored
description: s2 を二度訪れた後に s3 が e3_back で戻ると、s2 の直近の訪問（s2#2、m21 を持つ）の開始時を復元し、s3 の書いた m33 と out/x を捨て、p1 のゲートを未通過に戻す
workflow: ../workflows/basic.yaml
metrics: conformance
seed: 1
inputs: {in.txt: x}
visits:
  s1#1:
    files: {s1.txt: s1, s1.flag: 'true'}
    classify: &id001 {choice: goal, confidence: 0.9}
  s2#1:
    files: {s2.txt: s2, s2.flag: 'false', gate1.flag: 'true'}
    memory: {m21: fix}
    classify: {choice: e2_back, confidence: 0.9}
  s1#2:
    files: {s1.txt: s1-v2, s1.flag: 'true'}
    classify: *id001
  s2#2: &id002
    files: {s2.txt: s2, s2.flag: 'true', gate1.flag: 'true'}
    classify: *id001
  s3#1:
    files: {s3.txt: s3, s3.flag: 'true', gate2.num: '0', out/x: y}
    memory: {m32: gap, m33: drop-me}
    classify: {choice: e3_back, confidence: 0.9}
  s2#3: *id002
  s3#2:
    files: {s3.txt: s3, s3.flag: 'true', gate2.num: '0'}
    classify: *id001
gates:
  p1#2: *id001
  p1#3: *id001
  p2#2: *id001
expect:
  status: completed
  trace:
  - start s1#1
  - eval stage s1 = goal
  - next s1 -> s2
  - start s2#1
  - eval stage s2 = e2_back
  - 'rollback s2 -> s1 [e2_back 1]'
  - start s1#2
  - eval stage s1 = goal
  - next s1 -> s2
  - start s2#2
  - eval stage s2 = goal
  - eval phase p1 = goal
  - gate_pass s2
  - next s2 -> s3
  - start s3#1
  - eval stage s3 = e3_back
  - 'rollback s3 -> s2 [e3_back 1] crossing'
  - start s2#3
  - eval stage s2 = goal
  - eval phase p1 = goal
  - gate_pass s2
  - next s2 -> s3
  - start s3#2
  - eval stage s3 = goal
  - eval phase p2 = goal
  - gate_pass s3
  - complete
  - end completed
# 観測した開始時スナップショット（高-1 で加える期待の候補）:
#   s1#1: files=['in.txt'] memory={} gates=[]
#   s2#1: files=['in.txt', 's1.flag', 's1.txt'] memory={} gates=[]
#   s1#2: files=['in.txt'] memory={'m21': 'fix'} gates=[]
#   s2#2: files=['in.txt', 's1.flag', 's1.txt'] memory={'m21': 'fix'} gates=[]
#   s3#1: files=['gate1.flag', 'in.txt', 's1.flag', 's1.txt', 's2.flag', 's2.txt'] memory={'m21': 'fix'} gates=['p1']
#   s2#3: files=['in.txt', 's1.flag', 's1.txt'] memory={'m21': 'fix', 'm32': 'gap'} gates=[]
#   s3#2: files=['gate1.flag', 'in.txt', 's1.flag', 's1.txt', 's2.flag', 's2.txt'] memory={'m21': 'fix', 'm32': 'gap'} gates=['p1']
```

```yaml
scenario: rerun_then_edge_again
description: max 超過で再実行を選んだ後に同じ辺を再び踏むと、回数を数え直さずにすぐ escalate する（3.1）
workflow: ../workflows/basic.yaml
metrics: conformance
seed: 1
inputs: {in.txt: x}
visits:
  s1#1: &id001
    files: {s1.txt: s1, s1.flag: 'true'}
    classify: {choice: goal, confidence: 0.9}
  s2#1: &id002
    files: {s2.txt: s2, s2.flag: 'false', gate1.flag: 'true'}
    memory: {m21: fix}
    classify: {choice: e2_back, confidence: 0.9}
  s1#2: *id001
  s2#2: *id002
  s1#3: *id001
  s2#3: *id002
  s2#4: *id002
operator:
- {kind: rerun}
- {kind: abort}
expect:
  status: aborted
  trace:
  - start s1#1
  - eval stage s1 = goal
  - next s1 -> s2
  - start s2#1
  - eval stage s2 = e2_back
  - 'rollback s2 -> s1 [e2_back 1]'
  - start s1#2
  - eval stage s1 = goal
  - next s1 -> s2
  - start s2#2
  - eval stage s2 = e2_back
  - 'rollback s2 -> s1 [e2_back 2]'
  - start s1#3
  - eval stage s1 = goal
  - next s1 -> s2
  - start s2#3
  - eval stage s2 = e2_back
  - escalation s2 max_exceeded -> rerun
  - start s2#4
  - eval stage s2 = e2_back
  - escalation s2 max_exceeded -> abort
  - abort
  - end aborted
# 観測した開始時スナップショット（高-1 で加える期待の候補）:
#   s1#1: files=['in.txt'] memory={} gates=[]
#   s2#1: files=['in.txt', 's1.flag', 's1.txt'] memory={} gates=[]
#   s1#2: files=['in.txt'] memory={'m21': 'fix'} gates=[]
#   s2#2: files=['in.txt', 's1.flag', 's1.txt'] memory={'m21': 'fix'} gates=[]
#   s1#3: files=['in.txt'] memory={'m21': 'fix'} gates=[]
#   s2#3: files=['in.txt', 's1.flag', 's1.txt'] memory={'m21': 'fix'} gates=[]
#   s2#4: files=['in.txt', 's1.flag', 's1.txt'] memory={'m21': 'fix'} gates=[]
```

```yaml
scenario: suspend_after_rollback
description: 戻った後の s1#2 で中断して再開すると同じ訪問 2 のまま。その後の再実行は訪問 3（3.3、3.4）
workflow: ../workflows/basic.yaml
metrics: conformance
seed: 1
inputs: {in.txt: x}
visits:
  s1#1:
    files: {s1.txt: s1, s1.flag: 'true'}
    classify: &id001 {choice: goal, confidence: 0.9}
  s2#1:
    files: {s2.txt: s2, s2.flag: 'false', gate1.flag: 'true'}
    memory: {m21: fix}
    classify: {choice: e2_back, confidence: 0.9}
  s1#2:
    ask: [q1, q2]
    files: {s1.txt: s1, s1.flag: 'true'}
    classify: {choice: null, confidence: 0}
  s1#3:
    ask: [q3]
    files: {s1.txt: s1, s1.flag: 'true'}
    classify: *id001
  s2#2:
    files: {s2.txt: s2, s2.flag: 'true', gate1.flag: 'true'}
    classify: *id001
  s3#1:
    files: {s3.txt: s3, s3.flag: 'true', gate2.num: '0'}
    classify: *id001
gates:
  p1#2: *id001
  p2#1: *id001
user:
- {answer: a1}
- {defer: true}
- {answer: a2}
- {answer: a3}
operator:
- {kind: rerun}
expect:
  status: completed
  trace:
  - start s1#1
  - eval stage s1 = goal
  - next s1 -> s2
  - start s2#1
  - eval stage s2 = e2_back
  - 'rollback s2 -> s1 [e2_back 1]'
  - start s1#2
  - suspend s1
  - end suspended
  - resume s1
  - start s1#2
  - eval stage s1 = unknown
  - escalation s1 unknown -> rerun
  - start s1#3
  - eval stage s1 = goal
  - next s1 -> s2
  - start s2#2
  - eval stage s2 = goal
  - eval phase p1 = goal
  - gate_pass s2
  - next s2 -> s3
  - start s3#1
  - eval stage s3 = goal
  - eval phase p2 = goal
  - gate_pass s3
  - complete
  - end completed
# 観測した開始時スナップショット（高-1 で加える期待の候補）:
#   s1#1: files=['in.txt'] memory={} gates=[]
#   s2#1: files=['in.txt', 's1.flag', 's1.txt'] memory={} gates=[]
#   s1#2: files=['in.txt'] memory={'m21': 'fix'} gates=[]
#   s1#2: files=['in.txt'] memory={'m21': 'fix'} gates=[]
#   s1#3: files=['in.txt'] memory={'m21': 'fix'} gates=[]
#   s2#2: files=['in.txt', 's1.flag', 's1.txt'] memory={'m21': 'fix'} gates=[]
#   s3#1: files=['gate1.flag', 'in.txt', 's1.flag', 's1.txt', 's2.flag', 's2.txt'] memory={'m21': 'fix'} gates=['p1']
```

```yaml
scenario: gate_unknown_rerun
description: p1 のゲートが unknown になり再実行を選ぶと、最終ステージ s2 を訪問 2 として実行し直し、ゲートの鍵は p1#2
workflow: ../workflows/basic.yaml
metrics: conformance
seed: 1
inputs: {in.txt: x}
visits:
  s1#1:
    files: {s1.txt: s1, s1.flag: 'true'}
    classify: &id001 {choice: goal, confidence: 0.9}
  s2#1: &id002
    files: {s2.txt: s2, s2.flag: 'true', gate1.flag: 'true'}
    classify: *id001
  s2#2: *id002
  s3#1:
    files: {s3.txt: s3, s3.flag: 'true', gate2.num: '0'}
    classify: *id001
gates:
  p1#1: {choice: null, confidence: 0}
  p1#2: *id001
  p2#1: *id001
operator:
- {kind: rerun}
expect:
  status: completed
  trace:
  - start s1#1
  - eval stage s1 = goal
  - next s1 -> s2
  - start s2#1
  - eval stage s2 = goal
  - eval phase p1 = unknown
  - escalation s2 unknown -> rerun
  - start s2#2
  - eval stage s2 = goal
  - eval phase p1 = goal
  - gate_pass s2
  - next s2 -> s3
  - start s3#1
  - eval stage s3 = goal
  - eval phase p2 = goal
  - gate_pass s3
  - complete
  - end completed
# 観測した開始時スナップショット（高-1 で加える期待の候補）:
#   s1#1: files=['in.txt'] memory={} gates=[]
#   s2#1: files=['in.txt', 's1.flag', 's1.txt'] memory={} gates=[]
#   s2#2: files=['in.txt', 's1.flag', 's1.txt'] memory={} gates=[]
#   s3#1: files=['gate1.flag', 'in.txt', 's1.flag', 's1.txt', 's2.flag', 's2.txt'] memory={} gates=['p1']
```
