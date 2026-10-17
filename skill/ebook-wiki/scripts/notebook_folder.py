#!/usr/bin/env python3
"""노트북명을 10_raw 하위 폴더명으로 바꾼다.

규칙: `[` `]` 제거, `/`는 `_`로, `_` 주변 공백 정리, 앞뒤 공백 제거
예: "[e-Book / 인문] 사피엔스_유발 하라리" → "e-Book_인문 사피엔스_유발 하라리"
사용: python3 -I notebook_folder.py "<노트북명>"
"""
import re
import sys


def to_folder(name: str) -> str:
    s = name.replace("[", "").replace("]", "")
    s = re.sub(r"\s*/\s*", "_", s)
    s = re.sub(r'[\\:*?"<>|#^]', "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit('사용: notebook_folder.py "<노트북명>"')
    print(to_folder(sys.argv[1]))
