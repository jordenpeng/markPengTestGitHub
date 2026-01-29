# TradingView Webhook API 測試指令集 (Windows PowerShell)
# ⚠️ 注意：這些指令會實際下單！請謹慎使用！

# 設定變數
$BASE_URL = "http://localhost:5000"
$SECRET = "your-secret-key-12345"

# 如果在 AWS EC2，請改成你的 IP
# $BASE_URL = "http://YOUR-EC2-IP:5000"

Write-Host "========================================================================"
Write-Host "TradingView Webhook API - PowerShell 測試指令"
Write-Host "========================================================================"
Write-Host ""
Write-Host "⚠️⚠️⚠️  警告：以下指令會實際下單！請謹慎使用！ ⚠️⚠️⚠️" -ForegroundColor Red
Write-Host ""
Write-Host "設定："
Write-Host "  BASE_URL: $BASE_URL"
Write-Host "  SECRET: $SECRET"
Write-Host ""
Write-Host "========================================================================"

# ============================================================
# 1. 健康檢查（安全，不會下單）
# ============================================================
Write-Host ""
Write-Host "【1. 健康檢查】（安全測試）" -ForegroundColor Green
Write-Host "指令："
Write-Host "Invoke-RestMethod -Uri '$BASE_URL/health' -Method GET"
Write-Host ""
Write-Host "執行結果："
try {
    $result = Invoke-RestMethod -Uri "$BASE_URL/health" -Method GET
    $result | ConvertTo-Json -Depth 10
} catch {
    Write-Host "錯誤: $_" -ForegroundColor Red
}
Write-Host ""

# ============================================================
# 2. 查詢倉位（安全，不會下單）
# ============================================================
Write-Host ""
Write-Host "【2. 查詢倉位】（安全測試）" -ForegroundColor Green
Write-Host "指令："
Write-Host "Invoke-RestMethod -Uri '$BASE_URL/position' -Method GET"
Write-Host ""
Write-Host "執行結果："
try {
    $result = Invoke-RestMethod -Uri "$BASE_URL/position" -Method GET
    $result | ConvertTo-Json -Depth 10
} catch {
    Write-Host "錯誤: $_" -ForegroundColor Red
}
Write-Host ""

# ============================================================
# 3. 做多/買入（⚠️ 會實際下單）
# ============================================================
Write-Host ""
Write-Host "========================================================================"
Write-Host "⚠️  以下指令會實際下單！" -ForegroundColor Yellow
Write-Host "========================================================================"
$confirm = Read-Host "是否要繼續執行做多測試？(yes/no)"

if ($confirm -eq "yes") {
    Write-Host ""
    Write-Host "【3. 做多/買入】⚠️ 實際下單" -ForegroundColor Yellow
    Write-Host "指令："
    Write-Host "Invoke-RestMethod -Uri '$BASE_URL/long' -Method POST -Body (ConvertTo-Json @{secret='$SECRET'; qty=1; price=23000.0}) -ContentType 'application/json'"
    Write-Host ""
    Write-Host "執行結果："
    try {
        $body = @{
            secret = $SECRET
            qty = 1
            price = 23000.0
        } | ConvertTo-Json
        
        $result = Invoke-RestMethod -Uri "$BASE_URL/long" -Method POST -Body $body -ContentType "application/json"
        $result | ConvertTo-Json -Depth 10
    } catch {
        Write-Host "錯誤: $_" -ForegroundColor Red
    }
    Write-Host ""
} else {
    Write-Host "已跳過做多測試"
}

# ============================================================
# 4. 做空/賣出（⚠️ 會實際下單）
# ============================================================
Write-Host ""
$confirm = Read-Host "是否要繼續執行做空測試？(yes/no)"

if ($confirm -eq "yes") {
    Write-Host ""
    Write-Host "【4. 做空/賣出】⚠️ 實際下單" -ForegroundColor Yellow
    Write-Host "指令："
    Write-Host "Invoke-RestMethod -Uri '$BASE_URL/short' -Method POST -Body (ConvertTo-Json @{secret='$SECRET'; qty=1; price=22500.0}) -ContentType 'application/json'"
    Write-Host ""
    Write-Host "執行結果："
    try {
        $body = @{
            secret = $SECRET
            qty = 1
            price = 22500.0
        } | ConvertTo-Json
        
        $result = Invoke-RestMethod -Uri "$BASE_URL/short" -Method POST -Body $body -ContentType "application/json"
        $result | ConvertTo-Json -Depth 10
    } catch {
        Write-Host "錯誤: $_" -ForegroundColor Red
    }
    Write-Host ""
} else {
    Write-Host "已跳過做空測試"
}

# ============================================================
# 5. 平倉（⚠️ 會實際下單）
# ============================================================
Write-Host ""
$confirm = Read-Host "是否要執行平倉？(yes/no)"

if ($confirm -eq "yes") {
    Write-Host ""
    Write-Host "【5. 平倉】⚠️ 實際下單" -ForegroundColor Yellow
    Write-Host "指令："
    Write-Host "Invoke-RestMethod -Uri '$BASE_URL/close' -Method POST -Body (ConvertTo-Json @{secret='$SECRET'}) -ContentType 'application/json'"
    Write-Host ""
    Write-Host "執行結果："
    try {
        $body = @{
            secret = $SECRET
        } | ConvertTo-Json
        
        $result = Invoke-RestMethod -Uri "$BASE_URL/close" -Method POST -Body $body -ContentType "application/json"
        $result | ConvertTo-Json -Depth 10
    } catch {
        Write-Host "錯誤: $_" -ForegroundColor Red
    }
    Write-Host ""
} else {
    Write-Host "已跳過平倉測試"
}

Write-Host ""
Write-Host "========================================================================"
Write-Host "測試完成"
Write-Host "========================================================================"
