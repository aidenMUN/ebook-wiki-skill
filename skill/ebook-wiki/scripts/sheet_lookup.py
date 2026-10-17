#!/usr/bin/env python3
"""도서목록 시트(CSV 내보내기)에서 책을 찾아 행 번호와 상태를 보여준다.

입력: Drive 도구 download_file_content(exportMimeType=text/csv) 결과
      - 결과가 저장된 JSON 파일({"content": base64 또는 csv}) 또는 일반 CSV 파일 모두 가능
사용:
  python3 -I sheet_lookup.py <파일> "<검색어>" ["<검색어2>" ...]   # 도서명·저자·파일명 일부
  python3 -I sheet_lookup.py <파일> --status                        # H열 상태 집계
출력 행 번호는 시트의 실제 행 번호(헤더=1행)임.
"""
import base64
import csv
import io
import json
import re
import sys
import unicodedata
from collections import Counter


def load_rows(path):
    raw = open(path, encoding="utf-8", errors="replace").read()
    text = raw
    try:
        content = json.loads(raw)["content"]
        try:
            text = base64.b64decode(content).decode("utf-8")
        except Exception:
            text = content
    except Exception:
        pass
    return list(csv.reader(io.StringIO(text)))


def norm(s):
    # macOS 파일명은 한글이 NFD(자모 분리)로 저장되므로 NFC로 맞춘 뒤 비교
    s = unicodedata.normalize("NFC", s)
    s = s.replace("’", "'").replace("‘", "'")
    return re.sub(r"[\s.\-_·,()'\[\]=]", "", s).lower()


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    rows = load_rows(sys.argv[1])
    header = rows[0]
    if sys.argv[2] == "--status":
        c = Counter((r[7].strip() if len(r) > 7 else "") or "(빈칸)" for r in rows[1:])
        print(f"전체 {len(rows) - 1}행")
        for k, v in c.most_common():
            print(f"  {k}: {v}")
        return
    for q in sys.argv[2:]:
        nq = norm(q)
        hits = []
        for i, r in enumerate(rows[1:], start=2):
            title = r[3] if len(r) > 3 else ""
            author = r[4] if len(r) > 4 else ""
            if nq and (nq in norm(title + author) or norm(title) and norm(title) in nq):
                hits.append((i, r))
        print(f"## 검색: {q} → {len(hits)}건")
        for i, r in hits:
            r = r + [""] * (9 - len(r))
            print(f"- 행 {i} | 연번 {r[0]} | {r[1]} | {r[2]} | 도서명 {r[3]} | 저자 {r[4]} | H {r[7] or '(빈칸)'} | I {r[8] or '(빈칸)'}")
            print(f"  파일 {r[5]}")
    if header[7:9] != ["위키상태", "노트북"]:
        print("⚠️ 헤더 H·I열이 예상(위키상태, 노트북)과 다름:", header[7:9])


if __name__ == "__main__":
    main()
