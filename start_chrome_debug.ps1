# Chrome 디버그 모드 실행 스크립트
# HelloTalk 봇을 실행하기 전에 이 스크립트를 먼저 실행하세요

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Chrome 디버그 모드 시작" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Chrome 경로 찾기
$chromePaths = @(
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
)

$chromePath = $null
foreach ($path in $chromePaths) {
    if (Test-Path $path) {
        $chromePath = $path
        break
    }
}

if (-not $chromePath) {
    Write-Host "❌ Chrome을 찾을 수 없습니다" -ForegroundColor Red
    Write-Host ""
    Write-Host "Chrome을 설치하거나 경로를 수동으로 지정하세요:" -ForegroundColor Yellow
    Write-Host '  Start-Process "C:\Path\To\chrome.exe" -ArgumentList "--remote-debugging-port=9222","--user-data-dir=C:\temp\chrome-debug"' -ForegroundColor White
    Write-Host ""
    exit 1
}

Write-Host "✓ Chrome 경로: $chromePath" -ForegroundColor Green
Write-Host ""

# 디버그 데이터 디렉토리
$debugDir = "C:\temp\chrome-debug"

# 기존 Chrome 프로세스 확인
$existingChrome = Get-Process chrome -ErrorAction SilentlyContinue
if ($existingChrome) {
    Write-Host "⚠ Chrome이 이미 실행 중입니다" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "디버그 모드로 실행하려면 모든 Chrome 창을 닫아야 합니다." -ForegroundColor Yellow
    Write-Host ""
    $response = Read-Host "모든 Chrome 프로세스를 종료하시겠습니까? (y/n)"

    if ($response -eq 'y' -or $response -eq 'Y') {
        Write-Host "Chrome 종료 중..." -ForegroundColor Cyan
        Get-Process chrome -ErrorAction SilentlyContinue | Stop-Process -Force
        Start-Sleep -Seconds 2
        Write-Host "✓ Chrome 종료됨" -ForegroundColor Green
        Write-Host ""
    } else {
        Write-Host "취소됨" -ForegroundColor Yellow
        exit 0
    }
}

# Chrome 디버그 모드 시작
Write-Host "Chrome 디버그 모드를 시작합니다..." -ForegroundColor Cyan
Write-Host ""
Write-Host "설정:" -ForegroundColor Gray
Write-Host "  - 디버그 포트: 9222" -ForegroundColor Gray
Write-Host "  - 데이터 디렉토리: $debugDir" -ForegroundColor Gray
Write-Host ""

try {
    Start-Process -FilePath $chromePath -ArgumentList @(
        "--remote-debugging-port=9222",
        "--user-data-dir=$debugDir"
    )

    Start-Sleep -Seconds 3

    # 연결 확인
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:9222/json" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        Write-Host "✓ Chrome 디버그 모드 시작 성공!" -ForegroundColor Green
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host "다음 단계:" -ForegroundColor Yellow
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "1. Chrome에서 HelloTalk 웹 로그인:" -ForegroundColor White
        Write-Host "   https://web.hellotalk.com/" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "2. 로그인 후 새 PowerShell 창에서 봇 실행:" -ForegroundColor White
        Write-Host "   cd E:\hellotalk-automation" -ForegroundColor Gray
        Write-Host "   python multi_user_bot.py" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "⚠️  이 Chrome 창을 닫지 마세요!" -ForegroundColor Yellow
        Write-Host ""
    } catch {
        Write-Host "⚠ Chrome이 시작되었지만 디버그 포트 연결 확인 실패" -ForegroundColor Yellow
        Write-Host "   Chrome이 완전히 시작될 때까지 기다려주세요" -ForegroundColor Gray
        Write-Host ""
    }

} catch {
    Write-Host "❌ Chrome 시작 실패: $_" -ForegroundColor Red
    Write-Host ""
    exit 1
}
