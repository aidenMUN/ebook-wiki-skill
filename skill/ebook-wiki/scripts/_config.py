"""스킬 설정(config.json) 읽기.

위치 우선순위: 환경변수 EBOOK_WIKI_CONFIG → 스킬 폴더의 config.json
config.example.json을 복사해 config.json을 만들고 값을 채워야 함.
"""
import json
import os
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQUIRED = ("vault_path", "library_path", "sheet_id")


def load():
    path = os.environ.get("EBOOK_WIKI_CONFIG") or os.path.join(SKILL_DIR, "config.json")
    if not os.path.exists(path):
        sys.exit(f"설정 파일 없음: {path}\n→ config.example.json을 config.json으로 복사해 값을 채우세요")
    cfg = json.load(open(path, encoding="utf-8"))
    missing = [k for k in REQUIRED if not cfg.get(k) or "PUT_YOUR" in str(cfg.get(k))]
    if missing:
        sys.exit(f"config.json에 값이 비어 있음: {', '.join(missing)}")
    for k in ("vault_path", "library_path"):
        cfg[k] = os.path.expanduser(cfg[k])
    cfg["sheet_url"] = f"https://docs.google.com/spreadsheets/d/{cfg['sheet_id']}/edit"
    return cfg


if __name__ == "__main__":
    for k, v in load().items():
        print(f"{k}: {v}")
