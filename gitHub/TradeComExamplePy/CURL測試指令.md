$uri = "https://trade.tradmarkpeng.store/close"
$body = @{
  secret   = "your-secret-key-12345"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri $uri -ContentType "application/json" -Body $body


$uri = "https://trade.tradmarkpeng.store/long"
$body = @{
  secret   = "your-secret-key-12345"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri $uri -ContentType "application/json" -Body $body


$uri = "https://trade.tradmarkpeng.store/short"
$body = @{
  secret   = "your-secret-key-12345"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri $uri -ContentType "application/json" -Body $body

setx TV_SECRET "your-secret-key-12345"

nssm set TradeBot AppEnvironmentExtra "TV_SECRET=your-secret-key-12345"


