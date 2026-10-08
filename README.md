# 양정우 포트폴리오 (정적 사이트)

PM 양정우의 반응형 웹 포트폴리오. Python(Jinja2 + PyYAML)으로 정적 HTML을 만들고 GitHub Pages로 배포합니다.
콘텐츠(YAML)와 템플릿을 분리해 두었기 때문에 수치·문구 수정은 `content/` 한 곳에서만 합니다.

## 구조

```
content/profile.yaml     소개·경력·제품·역할·프로필
content/projects.yaml    프로젝트 4개 (성과 수치, 케이스 슬라이드 목록)
templates/               base + partials (hero, profile, career, product, role, project, footer)
static/                  css, js, img(제품 이미지), slides(케이스 슬라이드), og.png
build.py                 content + templates + static -> dist/
tests/test_layout.py     Playwright 레이아웃 테스트
scripts/                 슬라이드 내보내기·변환, og.png 생성
.github/workflows/       deploy.yml
```

## 로컬 빌드와 미리보기

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\python build.py
.\.venv\Scripts\python -m http.server -d dist
```

브라우저에서 `http://localhost:8000` 을 엽니다. 내용을 고친 뒤에는 `build.py` 를 다시 실행하세요.

## 테스트

```powershell
.\.venv\Scripts\python -m playwright install chromium   # 최초 1회
.\.venv\Scripts\python -m pytest tests
```

390 / 768 / 1440px × 라이트 / 다크에서 가로 스크롤, 이미지 로드, 앵커 대상, JS 없이도 열람되는지를 검사하고
스크린샷을 `tests/screenshots/` 에 저장합니다(커밋 제외).

## 슬라이드·이미지 갱신

원본 PPT 는 커밋하지 않습니다(`.gitignore`). PPT 를 수정했다면 다시 내보냅니다.

1. `scripts/export_slides.ps1` — PowerPoint 로 슬라이드를 3200x1800 PNG 로 내보냄(Windows + PowerPoint 필요)
2. `scripts/convert_slides.py` — 2400px WebP(q90) 로 변환해 `static/slides/` 에 저장

**공개하기 전에 슬라이드 속 얼굴·식별 정보·전화번호가 없는지 직접 확인하세요.** 공개 리포에 한 번 올라가면 이력에서 지울 수 없습니다.
전화번호는 어떤 파일에도 넣지 않습니다(연락처는 이메일만). 테스트(`test_no_phone_number_or_education`)가 전화번호 형식 문자열이 없는지 검사합니다.

## GitHub Pages 배포 (최초 1회)

1. GitHub 에서 `sheepha88.github.io` 리포지토리를 만듭니다(Public).
2. 로컬에서 연결하고 올립니다.
   ```powershell
   git remote add origin https://github.com/sheepha88/sheepha88.github.io.git
   git push -u origin main
   ```
3. GitHub 의 Settings > Pages > Build and deployment > Source 를 **GitHub Actions** 로 지정합니다.
4. `main` 에 push 하면 `deploy.yml` 이 빌드 → 테스트 → 배포를 실행합니다. 테스트가 실패하면 배포되지 않습니다.
5. 주소: https://sheepha88.github.io

## 지원할 때마다 태그 운영

회사별로 어떤 버전을 보냈는지 남겨 두기 위해 지원 시점에 태그를 답니다.

```powershell
git tag v1.0-회사명
git push origin v1.0-회사명
```

특정 회사에 보낸 버전을 다시 보려면 `git checkout v1.0-회사명` 후 빌드하면 됩니다.
사이트는 `noindex` 이므로 검색엔진에는 노출되지 않고, 링크를 아는 사람만 열 수 있습니다.
