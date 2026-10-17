#!/usr/bin/env python3
"""위키 무결성 점검: 깨진 링크, 이름 중복, 출처 없는 개념·인물, frontmatter 필수값, iCloud 충돌 파일.

사용: python3 -I check_wiki.py [볼트 경로 — 생략 시 config.json의 vault_path]
"""
import collections
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _config import load as load_config  # noqa: E402

REQUIRED = {
    "20_books": ["type", "title", "author", "category", "notebook", "status", "ingested"],
    "30_concepts": ["type", "sources", "updated"],
    "40_entities": ["type", "kind", "sources"],
    "50_synthesis": ["type", "sources", "created"],
}
SKIP_DIRS = ("99_admin/", ".obsidian/")


def frontmatter(text):
    m = re.match(r"---\n(.*?)\n---", text, re.S)
    return m.group(1) if m else ""


def main():
    vault = sys.argv[1] if len(sys.argv) > 1 else load_config()["vault_path"]
    os.chdir(vault)
    files = [p for p in glob.glob("**/*.md", recursive=True) if not p.startswith(SKIP_DIRS)]
    all_md = glob.glob("**/*.md", recursive=True) + glob.glob("**/*.base", recursive=True)
    names = {os.path.splitext(os.path.basename(p))[0] for p in all_md}
    names |= {os.path.basename(p) for p in all_md}
    paths = {os.path.splitext(p)[0] for p in all_md} | set(all_md)
    problems = collections.defaultdict(list)

    for p in files:
        text = open(p, encoding="utf-8").read()
        body = re.sub(r"`[^`\n]*`", "", text)  # 코드 표기 안의 예시는 제외
        for link in re.findall(r"\[\[([^\]|#]+)", body):
            link = link.strip()
            if link not in names and link not in paths:
                problems["깨진 링크"].append(f"{p} → [[{link}]]")
        top = p.split("/")[0]
        if top in REQUIRED:
            fm = frontmatter(text)
            for key in REQUIRED[top]:
                if not re.search(rf"^{key}:\s*(\S|\n\s+-)", fm, re.M):
                    problems["frontmatter 누락"].append(f"{p}: {key}")
        if re.search(r" \d+\.md$", p) or "(1).md" in p:
            problems["iCloud 충돌 의심"].append(p)

    dup = collections.Counter(os.path.splitext(os.path.basename(p))[0] for p in files)
    problems["이름 중복"] += [k for k, v in dup.items() if v > 1]

    linked = set()
    for p in files:
        linked |= set(l.strip() for l in re.findall(r"\[\[([^\]|#]+)", open(p, encoding="utf-8").read()))
    for p in glob.glob("30_concepts/*.md") + glob.glob("40_entities/*.md") + glob.glob("20_books/*.md"):
        n = os.path.splitext(os.path.basename(p))[0]
        if n not in linked:
            problems["고아 페이지(들어오는 링크 0)"].append(p)

    if not any(problems.values()):
        print("이상 없음")
    for k, v in problems.items():
        if v:
            print(f"## {k} ({len(v)})")
            for x in v:
                print(f"- {x}")


if __name__ == "__main__":
    main()
