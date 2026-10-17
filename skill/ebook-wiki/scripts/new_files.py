#!/usr/bin/env python3
"""`신규 확인`용: 원본 서고 폴더(config library_path)의 PDF 중 도서목록 시트에 없는 파일을 찾는다.

사용: python3 -I new_files.py <시트 CSV/JSON 파일> [서고 경로 — 생략 시 config.json의 library_path]
- 파일명 규칙 "도서명-저자.pdf"로 도서명을 추정해 시트 D열과 비교 (공백·기호 무시)
- 출력: 미등록 파일 목록(대분류 / 세부 폴더 / 도서명 / 저자 추정)과 전체 PDF 수(library_total 갱신용)
"""
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheet_lookup import load_rows, norm  # noqa: E402
from _config import load as load_config  # noqa: E402



def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    rows = load_rows(sys.argv[1])
    root = sys.argv[2] if len(sys.argv) > 2 else load_config()["library_path"]
    titles = {norm(r[3]) for r in rows[1:] if len(r) > 3 and r[3].strip()}
    total, missing = 0, []
    for dirpath, _, files in os.walk(root):
        for f in files:
            if not f.lower().endswith(".pdf"):
                continue
            total += 1
            stem = unicodedata.normalize("NFC", f[:-4])
            sep = "-" if "-" in stem else ("_" if "_" in stem else "")
            title, _, author = stem.rpartition(sep) if sep else (stem, "", "")
            # 저자 끝 괄호(예: "홍석균(인도자용)")는 시트에서 도서명 쪽으로 옮겨 적으므로 함께 비교
            paren = re.search(r"\(([^)]*)\)\s*$", author)
            alt = norm(title + paren.group(1)) if paren else None
            if norm(title) in titles or norm(stem) in titles or (alt and alt in titles):
                continue
            if paren:
                title, author = f"{title.strip()}({paren.group(1)})", author[: paren.start()]
            rel = unicodedata.normalize("NFC", os.path.relpath(dirpath, root)).split(os.sep)
            big = rel[0] if rel and rel[0] != "." else ""
            sub = "/".join(rel[1:]) if len(rel) > 1 else "단행본"
            missing.append((big, sub, title.strip(), author.strip(), f))
    print(f"서고 PDF 전체: {total}권 (library_total)")
    print(f"시트 미등록: {len(missing)}권")
    for big, sub, title, author, f in sorted(missing):
        print(f"- {big} | {sub} | {title} | {author or '(저자 추정 불가)'} | {f}")


if __name__ == "__main__":
    main()
