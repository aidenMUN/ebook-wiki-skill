#!/usr/bin/env python3
"""위키 무결성 점검 v2.

사용: python3 -I check_wiki.py [볼트 경로]
  볼트 경로를 생략하면 config.json의 vault_path → 환경변수 EBOOK_WIKI_VAULT → FALLBACK_VAULT 순으로 찾음
종료 코드: 오류가 있으면 1, 없으면 0 (주의·정보만 있으면 0)

검사 항목
  [오류] 깨진 링크 · frontmatter 필수값 누락 · 책 raw 링크 누락/대상 없음 ·
         종합 페이지 raw_p02 누락/대상 없음 · 같은 이름 위키 페이지
  [주의] 고립된 원본(10_raw에 들어오는 링크 없음) · 고아 페이지 · index 누락 ·
         같은 이름 원본 파일(이름만 쓴 링크가 엉뚱한 파일로 갈 수 있음) · iCloud 충돌 의심
  [정보] 관리 문서(99_admin)의 자리표시 링크 수
코드 블록(```)과 인라인 코드(`…`) 안의 [[…]]는 링크로 보지 않음 (Obsidian과 같음)
"""
import collections
import glob
import os
import re
import sys
import unicodedata

FALLBACK_VAULT = None  # 내 맥 전용 설치본에서는 볼트 경로를 넣어 둠

CONTENT = ("20_books", "30_concepts", "40_entities", "50_synthesis", "60_outputs")
REQUIRED = {
    "20_books": ["type", "title", "author", "category", "notebook", "raw", "status", "ingested"],
    "30_concepts": ["type", "sources", "updated"],
    "40_entities": ["type", "kind", "sources"],
    "50_synthesis": ["type", "sources", "created"],
}
ADMIN = ("99_admin/",)
SKIP = (".obsidian/", ".trash/")


def nfc(s):
    return unicodedata.normalize("NFC", s)


def default_vault():
    here = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(os.path.join(here, "_config.py")):
        sys.path.insert(0, here)
        try:
            from _config import load  # noqa: E402
            return load()["vault_path"]
        except SystemExit:
            pass
    return os.environ.get("EBOOK_WIKI_VAULT") or FALLBACK_VAULT


def strip_code(text):
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    return re.sub(r"`[^`\n]*`", "", text)


def frontmatter(text):
    m = re.match(r"---\n(.*?)\n---", text, re.S)
    return m.group(1) if m else ""


def links(text):
    return [l.split("|")[0].split("#")[0].strip() for l in re.findall(r"\[\[([^\[\]]+)\]\]", strip_code(text))]


def main():
    vault = sys.argv[1] if len(sys.argv) > 1 else default_vault()
    if not vault or not os.path.isdir(vault):
        sys.exit("볼트 경로를 찾지 못함 — 인자로 넘기거나 config.json·EBOOK_WIKI_VAULT를 설정하세요")
    os.chdir(vault)
    md = [nfc(p) for p in glob.glob("**/*.md", recursive=True) if not p.startswith(SKIP)]
    other = [nfc(p) for p in glob.glob("**/*.base", recursive=True) if not p.startswith(SKIP)]
    allf = md + other
    texts = {p: nfc(open(p, encoding="utf-8").read()) for p in md}

    by_name = collections.defaultdict(list)
    for p in allf:
        by_name[os.path.basename(p)[:-3] if p.endswith(".md") else os.path.basename(p)].append(p)
    paths = {p[:-3] if p.endswith(".md") else p: p for p in allf}

    def resolve(l):
        if not l:
            return None
        if l in paths:
            return paths[l]
        if l.endswith(".md") and l[:-3] in paths:
            return paths[l[:-3]]
        cands = by_name.get(os.path.basename(l)) or by_name.get(os.path.basename(l)[:-3] if l.endswith(".md") else "")
        return cands[0] if cands else None

    err, warn, info = collections.defaultdict(list), collections.defaultdict(list), collections.defaultdict(list)
    inbound = collections.defaultdict(set)
    admin_ghost = collections.Counter()

    for p, t in texts.items():
        is_admin = p.startswith(ADMIN)
        for l in links(t):
            r = resolve(l)
            if r:
                if r != p:
                    inbound[r].add(p)
            elif is_admin:
                admin_ghost[l] += 1
            else:
                err["깨진 링크"].append(f"{p} → [[{l}]]")

        top = p.split("/")[0]
        fm = frontmatter(t)
        for key in REQUIRED.get(top, []):
            if not re.search(rf"^{key}:[ \t]*(\S|\n\s+-)", fm, re.M):
                err["frontmatter 필수값 누락"].append(f"{p}: {key}")
        if top == "20_books":
            m = re.search(r'^raw:\s*"?\[\[([^\]]+)\]\]', fm, re.M)
            if m and not resolve(m.group(1).split("|")[0]):
                err["책 raw 링크 대상 없음"].append(f"{p} → {m.group(1)}")
        if top == "50_synthesis":
            nb = re.search(r'^notebook:\s*"?(.+?)"?\s*$', fm, re.M)
            rp = re.search(r'^raw_p02:\s*"?\[\[([^\]]+)\]\]', fm, re.M)
            if rp and not resolve(rp.group(1).split("|")[0]):
                err["종합 raw_p02 대상 없음"].append(f"{p} → {rp.group(1)}")
            if nb and not rp:
                folder = nb.group(1).replace("[", "").replace("]", "")
                folder = re.sub(r"\s*/\s*", "_", folder).strip()
                if glob.glob(os.path.join("10_raw", glob.escape(folder), "*P02*.md")):
                    err["종합 raw_p02 누락 (P02 원본이 있는데 링크 없음)"].append(p)
        if re.search(r" \d+\.md$", p) or "(1).md" in p:
            warn["iCloud 충돌 의심"].append(p)

    content = [p for p in md if p.split("/")[0] in CONTENT]
    dup = collections.Counter(os.path.basename(p) for p in content)
    err["같은 이름 위키 페이지"] += [n for n, c in dup.items() if c > 1]

    raw = [p for p in md if p.startswith("10_raw/")]
    for p in raw:
        if not inbound[p]:
            warn["고립된 원본 (들어오는 링크 없음)"].append(p)
    rawdup = collections.Counter(os.path.basename(p) for p in raw)
    for n, c in rawdup.items():
        if c > 1:
            warn["같은 이름 원본 파일 (경로 링크 필요)"].append(f"{n} × {c}")

    idx = texts.get("index.md", "")
    idx_links = set(links(idx))
    for p in content:
        name = os.path.basename(p)[:-3]
        if not (inbound[p] - {"index.md", "log.md"}):
            warn["고아 페이지 (index·log 말고 들어오는 링크 없음)"].append(p)
        if p.split("/")[0] in ("20_books", "30_concepts", "40_entities", "50_synthesis") and name not in idx_links and p[:-3] not in idx_links:
            warn["index 누락"].append(p)

    if admin_ghost:
        info["관리 문서(99_admin) 자리표시 링크 — 정상, 그래프에서만 보임"].append(
            ", ".join(f"[[{k}]]×{v}" for k, v in admin_ghost.most_common()))

    print(f"점검 대상: 문서 {len(md)}개 (위키 본문 {len(content)} · 원본 {len(raw)})")
    for title, bucket in (("오류", err), ("주의", warn), ("정보", info)):
        items = {k: v for k, v in bucket.items() if v}
        if not items:
            print(f"[{title}] 없음")
            continue
        for k, v in items.items():
            print(f"[{title}] {k} ({len(v)})")
            for x in v:
                print(f"  - {x}")
    sys.exit(1 if any(err.values()) else 0)


if __name__ == "__main__":
    main()
