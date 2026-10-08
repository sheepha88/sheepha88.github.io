# PowerPoint(COM)로 케이스 슬라이드를 3200x1800 PNG 로 내보낸다. (Windows + PowerPoint 필요)
# 사용: .\scripts\export_slides.ps1 -Pptx "이력서 및 포트폴리오\포트폴리오\PM_Portfolio_YangJeongwoo_v16.pptx" -Out "$env:TEMP\hq"
param(
  [Parameter(Mandatory)] [string] $Pptx,
  [Parameter(Mandatory)] [string] $Out
)
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force $Out | Out-Null
# 프로젝트별 슬라이드 번호(표지 + 본문). 프로필(2)·마무리(36)는 전화번호가 있어 제외한다.
$map = [ordered]@{
  p1 = @(26) + (28..35)   # 진단 일치도
  p2 = @(7)  + (9..16)    # 폼빌더
  p3 = @(17) + (19..25)   # 마스킹
}
$app = New-Object -ComObject PowerPoint.Application
try {
  $pres = $app.Presentations.Open((Resolve-Path $Pptx).Path, $true, $false, $false)
  foreach ($k in $map.Keys) {
    $n = 0
    foreach ($i in $map[$k]) {
      $pres.Slides.Item($i).Export("$Out\$k-$('{0:D2}' -f $n).png", 'PNG', 3200, 1800)
      $n++
    }
  }
  $pres.Close()
} finally { $app.Quit() }
