#!/bin/bash
# TradingView Webhook API 測試指令集
# ⚠️ 注意：這些指令會實際下單！請謹慎使用！

# 設定變數
BASE_URL="http://localhost:5000"
SECRET="your-secret-key-12345"

# 如果在 AWS EC2，請改成你的 IP
# BASE_URL="http://YOUR-EC2-IP:5000"

echo "========================================================================"
echo "TradingView Webhook API - cURL 測試指令"
echo "========================================================================"
echo ""
echo "⚠️⚠️⚠️  警告：以下指令會實際下單！請謹慎使用！ ⚠️⚠️⚠️"
echo ""
echo "設定："
echo "  BASE_URL: $BASE_URL"
echo "  SECRET: $SECRET"
echo ""
echo "========================================================================"

# ============================================================
# 1. 健康檢查（安全，不會下單）
# ============================================================
echo ""
echo "【1. 健康檢查】（安全測試）"
echo "指令："
echo "curl $BASE_URL/health"
echo ""
echo "執行結果："
curl $BASE_URL/health
echo -e "\n"

# ============================================================
# 2. 查詢倉位（安全，不會下單）
# ============================================================
echo ""
echo "【2. 查詢倉位】（安全測試）"
echo "指令："
echo "curl $BASE_URL/position"
echo ""
echo "執行結果："
curl $BASE_URL/position
echo -e "\n"

# ============================================================
# 3. 做多/買入（⚠️ 會實際下單）
# ============================================================
echo ""
echo "========================================================================"
echo "⚠️  以下指令會實際下單！"
echo "========================================================================"
read -p "是否要繼續執行做多測試？(yes/no): " confirm

if [ "$confirm" == "yes" ]; then
    echo ""
    echo "【3. 做多/買入】⚠️ 實際下單"
    echo "指令："
    echo "curl -X POST $BASE_URL/long \\"
    echo "  -H \"Content-Type: application/json\" \\"
    echo "  -d '{\"secret\": \"$SECRET\", \"qty\": 1, \"price\": 23000.0}'"
    echo ""
    echo "執行結果："
    curl -X POST $BASE_URL/long \
      -H "Content-Type: application/json" \
      -d "{\"secret\": \"$SECRET\", \"qty\": 1, \"price\": 23000.0}"
    echo -e "\n"
else
    echo "已跳過做多測試"
fi

# ============================================================
# 4. 做空/賣出（⚠️ 會實際下單）
# ============================================================
echo ""
read -p "是否要繼續執行做空測試？(yes/no): " confirm

if [ "$confirm" == "yes" ]; then
    echo ""
    echo "【4. 做空/賣出】⚠️ 實際下單"
    echo "指令："
    echo "curl -X POST $BASE_URL/short \\"
    echo "  -H \"Content-Type: application/json\" \\"
    echo "  -d '{\"secret\": \"$SECRET\", \"qty\": 1, \"price\": 22500.0}'"
    echo ""
    echo "執行結果："
    curl -X POST $BASE_URL/short \
      -H "Content-Type: application/json" \
      -d "{\"secret\": \"$SECRET\", \"qty\": 1, \"price\": 22500.0}"
    echo -e "\n"
else
    echo "已跳過做空測試"
fi

# ============================================================
# 5. 平倉（⚠️ 會實際下單）
# ============================================================
echo ""
read -p "是否要執行平倉？(yes/no): " confirm

if [ "$confirm" == "yes" ]; then
    echo ""
    echo "【5. 平倉】⚠️ 實際下單"
    echo "指令："
    echo "curl -X POST $BASE_URL/close \\"
    echo "  -H \"Content-Type: application/json\" \\"
    echo "  -d '{\"secret\": \"$SECRET\"}'"
    echo ""
    echo "執行結果："
    curl -X POST $BASE_URL/close \
      -H "Content-Type: application/json" \
      -d "{\"secret\": \"$SECRET\"}"
    echo -e "\n"
else
    echo "已跳過平倉測試"
fi

echo ""
echo "========================================================================"
echo "測試完成"
echo "========================================================================"
