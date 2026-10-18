---
name: ebook-wiki
description: 보유 eBook(PDF)으로 카파시(Karpathy) 방식 LLM Wiki를 만들고 운영하는 스킬. Google Drive 서고의 책을 NotebookLM 노트북에서 정형 추출(Aside CLI 브라우저 자동화)해 Obsidian 볼트에 책·개념·인물·종합 페이지로 쌓고, 도서목록 Google Sheet의 위키 상태를 갱신한다. "위키화 <노트북명>", "위키화 inbox", "신규 확인", "검토완료 <노트북명>", "질문: …"(eBook 위키 대상), "점검", "현황", "ebook wiki", "북 위키", "책을 위키에 넣어줘" 같은 요청에 사용한다.
---

# eBook Wiki 운영 스킬

사람은 **책 고르기 · NotebookLM 노트북에 추가 · 명령 한 줄 · 검토**만 함. 나머지(추출·작성·연결·기록·시트 갱신)는 이 스킬이 처리함.

## 0. 시작 전 반드시 할 일
1. 설정 확인: `python3 -I $SK/scripts/_config.py` → `vault_path`, `library_path`, `sheet_id`, `sheet_url` 값을 이후 절차에 사용. 오류가 나면 README의 설치 절차를 사용자에게 안내하고 멈춤
2. 볼트 규칙 파일을 읽음: `<vault_path>/CLAUDE.md` — 페이지 작성·명명·표기·안전 규칙의 **기준 문서**. 이 스킬과 충돌하면 CLAUDE.md가 우선
3. `<vault_path>/index.md`와 `<vault_path>/log.md` 마지막 10개 기록을 읽어 현재 상태 파악
4. 브라우저 작업 전 `aside guide`로 Aside CLI 사용법 확인 (처음 한 번). Aside가 없으면 사용자에게 설치 여부를 묻고, 설치 전에는 `위키화 inbox`(수동 붙여넣기) 경로만 사용
5. 작업 목록(plan)을 세우고 진행 상황을 사용자에게 짧게 알림

## 1. 고정 자원

| 이름 | 값 |
|---|---|
| `$SK` | 이 스킬 폴더 (보통 `~/.claude/skills/ebook-wiki`) |
| 설정 | `$SK/config.json` (또는 환경변수 `EBOOK_WIKI_CONFIG`) |
| 도서목록 시트 열 | A 연번 · B 대분류 · C 세부/시리즈 · D 도서명 · E 저자 · F 파일 링크 · G 폴더 링크 · **H 위키상태** · **I 노트북** |
| 상태값(H열) | (빈칸) → `위키반영` → `검토완료` / `보류` |
| 프롬프트 | `<vault_path>/99_admin/prompts/P01_책별추출.md`, `P02_묶음비교.md` |
| 템플릿 | `<vault_path>/99_admin/templates/T_책·T_개념·T_엔티티·T_종합.md` |
| Aside 명령 문구 | [references/aside_commands.md](references/aside_commands.md) (`<sheet_url>` 자리에 설정값) |
| 임시 파일 | 세션 스크래치패드 디렉터리 |

스크립트는 모두 `python3 -I $SK/scripts/<이름>.py` 로 실행함.

| 스크립트 | 용도 |
|---|---|
| `_config.py` | 설정 읽기·검증 |
| `extract_marked.py <입력> <출력>` | Aside 출력에서 `<<<BEGIN>>>`~`<<<END>>>` 본문만 저장 (짧거나 없으면 종료코드 1) |
| `notebook_folder.py "<노트북명>"` | 노트북명 → `10_raw` 폴더명 |
| `sheet_lookup.py <CSV> "<검색어>"…` / `--status` | 시트 행 번호·상태 찾기 / 상태 집계 |
| `new_files.py <CSV> [서고경로]` | 시트에 없는 PDF 찾기 (한글 NFD/NFC 차이 처리) |
| `check_wiki.py [볼트경로]` | [오류] 깨진 링크·필수값 누락·책 `raw`/종합 `raw_p02` 누락·이름 중복 / [주의] 고립된 원본·고아 페이지·index 누락·같은 이름 원본 / [정보] 관리 문서 자리표시 링크. 오류가 있으면 종료코드 1 |

## 2. 명령별 절차

### `위키화 <노트북명>`
1. **소스 확인** — Aside A1 실행 → 소스 제목 목록 확보. 노트북을 못 찾으면 비슷한 이름을 보여주고 확인
2. **시트 대조** — Google Drive 도구로 시트를 CSV로 내려받음(`download_file_content`, exportMimeType `text/csv`) → 결과 파일 경로로
   `sheet_lookup.py <파일> "<도서명 또는 파일명>"` 실행 → 행 번호·H·I 확인
   - H가 `위키반영`/`검토완료`면 건너뜀 · 시트에 없으면 "신규 등록 필요"로 따로 보고
   - 불일치가 없으면 묻지 않고 진행
3. **책별 추출** (1권씩) — Aside A2 실행, 출력은 스크래치패드에 저장 →
   `extract_marked.py <출력> <스크래치>/p01_<약칭>.md` → 실패(종료코드 1)면 1회 재시도 → 또 실패면 수동 붙여넣기 요청
4. **원본 보관** — `notebook_folder.py "<노트북명>"`으로 폴더명 생성 →
   `<vault_path>/10_raw/<폴더>/<도서명>_P01.md` 에 frontmatter(source, notebook, prompt: P01, extracted: YYYY.MM.DD, method: aside) + 본문 그대로 저장. **이미 있으면 덮어쓰지 않음**
   - 0번 인식 품질이 `읽기 어려움` → 위키화 중단, 시트 H `보류`, 보고
5. **묶음 비교** — 이번 대상이 2권 이상이면 Aside A3(P02) → `10_raw/<폴더>/<폴더>_P02_YYYYMMDD.md`
6. **Ingest** (CLAUDE.md 4장 ⑥ 준수)
   - 책 페이지 `20_books/<도서명>-<저자>.md` (원본 파일명과 같은 규칙, T_책 필드 전부 채움: category=시트 B열, drive_url=시트 F열, notebook=노트북명 그대로, raw 링크, ocr_quality, status `위키반영`, tags `분야/…`·`유형/…`)
   - 개념(`30_concepts`)·인물/전통(`40_entities`) 페이지: **먼저 기존 페이지·aliases를 검색**해 있으면 표에 행 추가·`sources`에 책 추가·`updated` 갱신, 없을 때만 새로 생성
   - 다른 책과 다르면 `🔀 관점 차이`(해석 차이) / `⚠️ 사실 충돌`(사실 차이)에 양쪽 출처 병기. 분야 간 연결을 우선 기록
   - `kind`는 인물 / 저자 / 전통·학파 / 기관 / 도구 / 작품 중 하나
   - 책에 없는 배경 지식(생몰년 등)을 넣으면 "확인 필요" 표시
7. **종합** — 2권 이상이면 `50_synthesis/<노트북폴더>_묶음종합.md`. frontmatter에 `raw_p02: "[[10_raw/<폴더>/<폴더>_P02_YYYYMMDD]]"`로 P02 원본을 반드시 링크 (빠지면 원본이 고립됨)
8. **마무리**
   - `index.md` 갱신(현황 숫자, 분야별 현황, 노트북·책·개념·인물 목록)
   - Aside A4로 시트 H `위키반영`, I 노트북명 (행마다 연번·도서명 확인 조건 포함)
   - `log.md` 맨 아래에 `## [YYYY.MM.DD] 위키화 | <노트북명> | 책 n권, 생성 n · 갱신 n` + 변경 페이지 목록
   - `check_wiki.py` 실행 → [오류]는 반드시 고친 뒤 다시 실행, [주의]는 보고에 포함
   - 사용자 보고: 위키화한 책, 생성·갱신 페이지 수, 인식 품질, 관점 차이·사실 충돌, 보류 도서, 확인 필요 사항 → `검토완료 <노트북명>` 안내

### `위키화 inbox`
- `<vault_path>/01_inbox/<노트북명 또는 폴더>/*.md`를 추출본으로 보고 위 4번(method: 수동)부터 진행. 처리 후 inbox 파일은 그대로 두고 사용자에게 정리 여부를 물음

### `검토완료 <노트북명>`
- 해당 노트북 책들의 시트 행을 찾아 Aside A4(H가 `위키반영`일 때만 `검토완료`) → 책 페이지 `status: 검토완료` → log 기록

### `신규 확인`
1. 시트 CSV 내려받기 → `new_files.py <파일>` → 미등록 PDF 목록과 서고 전체 수
2. 이름이 비슷한 기존 행이 있으면 중복 후보로 표시. 목록을 표로 보여주고 **승인받은 뒤에만** Aside A5로 시트 행 추가 (F열 링크는 Drive 검색으로 파일 ID 조회, G열은 같은 폴더의 기존 행 값 사용)
3. 추가 후 시트를 다시 내려받아 기존 행 무변경·신규 행 일치를 확인
4. `00_dashboard/대시보드.md`의 `library_total`, `library_counted` 갱신 → log 기록

### `질문: <내용>`
- `index.md` → 관련 페이지 → `[[책]] (장, p.쪽)` 출처를 달아 답변
- `80_journal/`의 관련 메모가 있으면 "나의 이전 기록"으로 함께 제시(수정 금지)
- 위키에 근거가 없으면 "위키에 없음" + 시트에서 관련 미위키화 도서 추천(`sheet_lookup.py`로 키워드 검색)
- 다시 쓸 만한 답은 `50_synthesis/` 저장 여부를 물음

### `점검`
- `check_wiki.py` + 시트 `sheet_lookup.py <파일> --status`와 `20_books` status 대조 + 개념 간 충돌 검토
- 리포트를 먼저 보여주고 **승인받은 항목만 수정** → log 기록

### `현황`
- 시트 `--status` 집계 + index 현황 + log 최근 5건을 표로 보고

## 3. 지켜야 할 것
- 원본 PDF, `10_raw/`(저장 후), `80_journal/`은 수정·이동·삭제하지 않음
- NotebookLM에서는 읽기·질문만. 노트북·소스 삭제, 공유 설정 변경 금지
- 시트는 H·I열 상태 기입만 위키화 절차의 일부로 진행. 행 추가·다른 열 수정은 사전 승인
- 비밀번호 입력 금지. 로그인이 필요하면 사용자에게 요청
- 원문 인용은 짧게. 위키는 개인 학습용으로 두고, 원문을 길게 옮겨 공개하지 않음 (저작권)
- 규칙(CLAUDE.md)을 바꾸면 버전을 올리고, 사람용 설명서(`99_admin/guide/`)도 갱신, log에 `스키마` 기록
