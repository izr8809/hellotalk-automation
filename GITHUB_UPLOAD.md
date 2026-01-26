# GitHub 업로드 가이드

## 방법 1: GitHub 웹사이트에서 리포지토리 생성

### 1단계: GitHub에서 새 리포지토리 생성

1. https://github.com/new 접속
2. 리포지토리 이름 입력: `hellotalk-automation`
3. Description: "HelloTalk web automation bot for sequential messaging"
4. **Public** 또는 **Private** 선택
5. ❌ **"Initialize this repository with a README" 체크 해제** (이미 있으므로)
6. "Create repository" 클릭

### 2단계: 로컬 리포지토리와 연결

GitHub 페이지에 표시되는 명령어를 복사하거나, 아래 명령어 실행:

```bash
cd /Users/jaeseunglee/Downloads/hellotalk_automation

# GitHub 리포지토리와 연결 (YOUR_USERNAME을 본인 계정으로 변경)
git remote add origin https://github.com/YOUR_USERNAME/hellotalk-automation.git

# 브랜치 이름을 main으로 변경
git branch -M main

# GitHub에 푸시
git push -u origin main
```

### 3단계: 완료!

브라우저에서 `https://github.com/YOUR_USERNAME/hellotalk-automation` 확인

---

## 방법 2: GitHub CLI 사용 (설치 필요)

### 1단계: GitHub CLI 설치

```bash
brew install gh
```

### 2단계: 인증

```bash
gh auth login
```

### 3단계: 리포지토리 생성 및 푸시

```bash
cd /Users/jaeseunglee/Downloads/hellotalk_automation

# 리포지토리 생성 (public)
gh repo create hellotalk-automation --public --source=. --push

# 또는 private
gh repo create hellotalk-automation --private --source=. --push
```

---

## 이후 업데이트 방법

코드를 수정한 후:

```bash
cd /Users/jaeseunglee/Downloads/hellotalk_automation

# 변경 사항 확인
git status

# 변경 사항 스테이징
git add .

# 커밋
git commit -m "Update: 변경 내용 설명"

# GitHub에 푸시
git push
```

---

## 중요 파일이 .gitignore에 포함됨

다음 파일들은 GitHub에 업로드되지 **않습니다** (.gitignore에 포함):

- `bot_state.json` - 봇 진행 상태
- `exclude_users.txt` - 제외 유저 목록 (개인 정보)
- `messages.txt` - 전송할 메시지 (개인 정보)
- `page_structure.html` - 디버그 파일
- `hellotalk_screenshot.png` - 스크린샷
- `venv/` - 가상환경

대신 `.example` 파일들이 포함되어 있습니다:
- `messages.example.txt`
- `exclude_users.example.txt`
