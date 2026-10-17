---
title: HOME
---

# eBook Wiki

> 보유 eBook을 활용한 지식 데이터베이스 · 운영 규칙은 [[CLAUDE]] · 전체 목록은 [[index]] · 작업 기록은 [[log]]
> 📘 처음이라면 → [[워크플로우설명서|워크플로우 설명서]]

## 데이터베이스
- [[00_dashboard/대시보드|📊 대시보드]] — 분야별 책 수 · 핵심 개념 · 분야 횡단 개념 · 진행률 (Dataview 플러그인 필요)
- [[00_dashboard/책DB.base|📚 책 DB]] — 전체 도서 / 분야별 / 검토 대기
- [[00_dashboard/개념DB.base|💡 개념 DB]] — 근거 책 많은 순 / 최근 갱신
- [[00_dashboard/인물DB.base|👤 인물·저자·전통 DB]] — 종류별
- [[00_dashboard/종합DB.base|🧩 종합 DB]] — 묶음 종합·질의응답

## 사용법 (Claude Code에 말하기)
| 명령 | 언제 |
|---|---|
| `위키화 <노트북명>` | NotebookLM 노트북에 책을 추가한 뒤 |
| `위키화 inbox` | 추출본을 `01_inbox`에 직접 붙여넣은 뒤 |
| `신규 확인` | 원본 서고 폴더에 새 책을 넣은 뒤 |
| `질문: …` | 언제든 |
| `검토완료 <노트북명>` | 위키화 결과를 확인한 뒤 |
| `점검` / `현황` | 월 1회 / 언제든 |

## 폴더
| 폴더 | 내용 | 작성자 |
|---|---|---|
| `00_dashboard` | DB 보기 화면 | 고정 |
| `01_inbox` | 수동 붙여넣기 추출본 | 나 |
| `10_raw` | NotebookLM 추출본 원형 (수정 금지) | Claude |
| `20_books` | 책 | Claude |
| `30_concepts` | 개념·주제 | Claude |
| `40_entities` | 인물·저자·전통·기관·도구 | Claude |
| `50_synthesis` | 묶음 종합·질의응답 | Claude |
| `60_outputs` | 산출물 초안 | Claude (요청 시) |
| `80_journal` | 내 메모·생각 (새 노트 기본 위치) | 나 |
| `90_assets` | 이미지·첨부 | — |
| `99_admin` | 프롬프트·템플릿·제안서 | 합의 후 수정 |

## 원본
- 서고: Google Drive 서고 폴더 (스킬 config.json의 library_path)
- 도서목록 시트: [도서목록 시트](https://docs.google.com/spreadsheets/d/<sheet_id>/edit)

## 스킬
- 운영 스킬 `ebook-wiki` (`~/.claude/skills/ebook-wiki`) — Claude 세션에서 `/ebook-wiki` 입력 또는 위 명령어를 말하면 실행
