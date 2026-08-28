# DealSite News Clipper

딜사이트플러스 기사를 수집하고, Claude로 분류해서 데일리 뉴스 클리핑
문서(DOCX + 병합 PDF)를 만들어 주는 로컬 웹 애플리케이션입니다.

---

## 실행 방법 1 — 실행 파일 (권장, 설치 불필요)

배포된 `DealSiteNewsClipper.exe` 를 원하는 폴더에 두고 더블클릭하면 됩니다.
Python 을 따로 설치할 필요가 없습니다.

1. **더블클릭** — 빈 포트를 자동으로 찾아 서버가 뜨고 브라우저가 열립니다.
2. **첫 화면에서 API 키 입력** — 처음 실행하면 설정 화면이 먼저 열립니다.
   Claude API 키를 붙여넣고 **연결 확인** 을 누르면 키가 실제로 동작하는지
   바로 알려줍니다. 저장하면 이후에는 다시 묻지 않습니다.
3. **끝** — 이후 실행부터는 곧바로 메인 화면으로 들어갑니다.

설정을 바꾸고 싶으면 우측 상단의 **⚙️ 설정** 을 누르세요. 저장하면 프로그램을
다시 켜지 않아도 즉시 반영됩니다.

생성된 결과물은 exe 와 같은 폴더의 `output/` 아래에 저장됩니다.

```
배포 폴더/
├─ DealSiteNewsClipper.exe
├─ .env            ← 첫 실행 시 자동 생성 (설정 화면에서 관리)
└─ output/         ← 결과 문서가 쌓이는 곳
```

종료하려면 콘솔 창을 닫거나 `Ctrl+C` 를 누르세요.

---

## 실행 방법 2 — 소스에서 직접 실행 (개발용)

```bash
pip install -r requirements.txt
python launcher.py          # 포트 자동 선택 + 브라우저 자동 실행
                            # 첫 실행이면 설정 화면에서 API 키를 입력
# 또는
python preflight.py         # 환경 점검 후 서버 시작
```

Windows 사용자는 `setup_and_run.bat` 을 더블클릭하면 Python 설치 확인부터
의존성 설치, 서버 실행까지 한 번에 처리됩니다.

---

## 실행 파일 빌드하기

빌드하려는 OS 에서 실행해야 합니다. Windows 용 exe 는 Windows 에서,
macOS 용 실행 파일은 macOS 에서 빌드됩니다 (크로스 컴파일 불가).

```bash
# Windows
build_exe.bat

# macOS / Linux
./build_exe.sh
```

결과물은 `dist/DealSiteNewsClipper(.exe)` 하나의 파일로 나옵니다.
`templates/`, `static/`, 로고, 타임존 DB(tzdata), python-docx 템플릿,
reportlab 폰트가 모두 이 파일 안에 포함되므로 단일 파일만 복사하면 됩니다.

빌드 설정을 바꾸려면 `dealsite.spec` 을 수정하세요.

### 아이콘 지정 (선택)

`app/static/img/dealsite-logo.ico` 파일을 두면 빌드 시 자동으로 exe 아이콘에
적용됩니다. 없으면 기본 아이콘이 쓰입니다.

---

## 환경 요구사항

| 항목 | 요구사항 |
| --- | --- |
| OS | Windows 10+ / macOS 12+ / Linux |
| 브라우저 | Microsoft Edge 또는 Chrome (크롤링에 사용, 드라이버는 자동 설치) |
| 네트워크 | 딜사이트플러스 및 Claude API 접속 필요 |
| Python | 소스 실행·빌드 시에만 필요 (3.11 이상 권장) |

---

## 설정 항목 (`.env`)

| 키 | 설명 |
| --- | --- |
| `ANTHROPIC_API_KEY` | **필수.** Claude API 키 |
| `DEALSITEPLUS_ID` / `_PW` | 선택. 비우면 브라우저에서 수동 로그인 |
| `CLAUDE_MODEL` | 분류에 쓸 모델 (기본 `claude-sonnet-5`) |
| `BROWSER_HEADLESS` | `false` 면 크롤링 과정을 눈으로 볼 수 있음 |
| `LOG_LEVEL` | `INFO` / `DEBUG` |
| `CLEANUP_HOURS` | 오래된 결과 폴더 자동 삭제 기준 시간 |

> 서비스가 종료된 모델 ID 가 `.env` 에 남아 있으면 시작할 때 현행 모델로
> 자동 교체되고 경고가 출력됩니다.

---

## 문제 해결

**포트 오류가 납니다**
자동으로 빈 포트를 찾으므로 보통 문제되지 않습니다. 8000–8099 가 모두 사용
중이면 다른 프로그램을 종료한 뒤 다시 실행하세요.

**분류 결과가 전부 "기타" 로 들어갑니다**
AI 분류가 실패했을 때의 동작입니다. 화면 상단에 실패 원인 배너가 표시되니
내용을 확인하세요. 대부분 API 키 오류이거나 모델 ID 문제입니다.

**크롤링이 0건입니다**
로그인 세션이 만료됐거나 사이트 구조가 바뀐 경우입니다.
`BROWSER_HEADLESS=false` 로 두고 실행하면 브라우저 동작을 직접 볼 수 있습니다.

---

## 숨은 기능

날짜에 따라 시작할 때 미니게임 화면이 뜹니다. 급할 때는 그 화면에서
**`shwoa`** 를 타이핑하면 바로 넘어갑니다. (입력창에 포커스가 있지 않아야
동작합니다.)
