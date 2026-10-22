"""examples/ の下の各ワークフローのディレクトリを import パスに加える。

パッケージを examples/<名前>/<パッケージ>/ に置けば、設定を直さずにテストから import できる。
examples/<名前>/tests/fixtures/ の下は、ステージ本体が写す成果物の置き場で、テストとして収集しない
（意図的に失敗するテストのコードを置ける）。
"""

import sys
from pathlib import Path

collect_ignore_glob = ["examples/*/tests/fixtures"]

for example in sorted((Path(__file__).parent / "examples").iterdir()):
    if example.is_dir() and str(example) not in sys.path:
        sys.path.insert(0, str(example))
