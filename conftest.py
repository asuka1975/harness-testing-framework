"""examples/ の下の各ワークフローのディレクトリを import パスに加える。

パッケージを examples/<名前>/<パッケージ>/ に置けば、設定を直さずにテストから import できる。
"""

import sys
from pathlib import Path

for example in sorted((Path(__file__).parent / "examples").iterdir()):
    if example.is_dir() and str(example) not in sys.path:
        sys.path.insert(0, str(example))
