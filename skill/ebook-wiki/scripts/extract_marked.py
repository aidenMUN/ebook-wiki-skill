#!/usr/bin/env python3
"""Aside 출력에서 <<<BEGIN>>> ~ <<<END>>> 사이 본문만 잘라 저장한다.

사용: python3 -I extract_marked.py <aside_출력.txt> <저장할.md>
- 터미널 색상 코드(ANSI)를 제거하고, 마지막 BEGIN/END 쌍을 사용한다.
- 본문이 비었거나 표식이 없으면 종료 코드 1.
"""
import re
import sys


def main():
    if len(sys.argv) != 3:
        sys.exit("사용: extract_marked.py <입력> <출력>")
    text = open(sys.argv[1], encoding="utf-8", errors="replace").read()
    text = re.sub(r"\x1b\[[0-9;]*m", "", text)
    start = text.rfind("<<<BEGIN>>>")
    end = text.rfind("<<<END>>>")
    if start < 0 or end < 0 or end < start:
        sys.exit("표식(<<<BEGIN>>>/<<<END>>>)을 찾지 못함 — 재시도 또는 수동 붙여넣기 필요")
    body = text[start + len("<<<BEGIN>>>"):end].strip()
    if len(body) < 200:
        sys.exit(f"본문이 너무 짧음({len(body)}자) — 잘림 의심, 재시도 필요")
    open(sys.argv[2], "w", encoding="utf-8").write(body + "\n")
    print(f"저장 완료: {len(body)}자, {body.count(chr(10)) + 1}줄 → {sys.argv[2]}")


if __name__ == "__main__":
    main()
