from pathlib import Path

csv_multi = """Ticker,Date,Open,High,Low,Close,Volume
AAPL,2026-03-01,180.25,182.50,179.80,181.90,52000000
AAPL,2026-03-02,182.00,183.10,181.00,182.40,48000000
MSFT,2026-03-01,405.10,408.00,403.50,407.20,21000000
NVDA,2026-03-01,880.00,895.50,875.00,890.10,35000000
"""

csv_tsla = """Date,Open,High,Low,Close,Volume
2026-03-01,202.50,205.80,200.10,204.30,31000000
2026-03-02,204.80,208.00,203.50,206.90,29000000
"""

json_crypto = """[
  {
    "symbol": "BTC",
    "timestamp": "2026-03-01T12:00:00Z",
    "price": 64200.50,
    "volume_24h": 28000000000
  },
  {
    "symbol": "ETH",
    "timestamp": "2026-03-01T12:00:00Z",
    "price": 3450.25,
    "volume_24h": 14000000000
  }
]
"""

json_googl = """{
  "Date": "2026-03-01",
  "Open": 175.20,
  "High": 177.00,
  "Low": 174.50,
  "Close": 176.80,
  "Volume": 18500000
}
"""

Path("market_data_multi_assets.csv").write_text(csv_multi)
Path("TSLA.csv").write_text(csv_tsla)
Path("crypto_data.json").write_text(json_crypto)
Path("GOOGL.json").write_text(json_googl)

print("Files successfully generated!")