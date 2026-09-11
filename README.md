# Siqnal Botu — Quraşdırma Təlimatı

## ⚠️ Vacib xəbərdarlıq
Bu bot **zəmanətli qazanc vəd etmir**. RSI, EMA və MACD kimi klassik texniki
indikatorlara əsaslanan sadə bir analiz köməkçisidir. Xüsusilə **OTC
cütlüklər broker tərəfindən sintetik yaradılan qiymətlərdir** — real bazar
məntiqi onlara tam tətbiq olunmur. Binar opsion / qısa müddətli ticarət
yüksək riskli fəaliyyətdir. İtirməyə hazır olmadığın pulu risk etmə.

## 1. Telegram botu yaratmaq
1. Telegram-da **@BotFather**-ə yaz
2. `/newbot` göndər, adını təyin et
3. Sənə verilən **token**-i qeyd et (məs: `123456:ABC-DEF...`)

## 2. Kodu işə salmaq

```bash
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN="buraya_token"
python bot.py
```

Windows-da (PowerShell):
```powershell
pip install -r requirements.txt
$env:TELEGRAM_BOT_TOKEN="buraya_token"
python bot.py
```

## 3. İstifadə

- `/start` — botu tanıt, komandaları göstər
- `/signal BTCUSDT` — real kripto cütlüyü üçün avtomatik siqnal (Binance
  açıq API-dən 5 dəqiqəlik şamlar əsasında)
- `/otc 1.1023 1.1030 1.1015 1.1040 1.1052 1.1048 1.1060 1.1065` — OTC
  cütlük üçün son bir neçə qapanış qiymətini əl ilə daxil edib siqnal al
  (ən azı 8 qiymət, köhnədən yeniyə sıra ilə)

## 4. Necə işləyir (qısaca)

Bot 3 indikatoru birləşdirir və 2/3 "səs" prinsipi ilə qərar verir:
- **RSI(14)**: 30-dan aşağı → alış siqnalı, 70-dən yuxarı → satış siqnalı
- **EMA9 vs EMA21**: sürətli EMA yavaş EMA-nı üstələyirsə → alış, əksinə → satış
- **MACD vs Signal xətti**: MACD yuxarıdadırsa → alış, aşağıdadırsa → satış

## 5. Real bazar cütlükləri üçün simvol nümunələri
`BTCUSDT`, `ETHUSDT`, `BNBUSDT`, `SOLUSDT` və Binance-də olan istənilən cüt.

## 6. Genişləndirmək istəsən
- Fərqli timeframe (1m, 15m, 1h) üçün `fetch_binance_closes` funksiyasındakı
  `interval` parametrini dəyişə bilərsən
- Forex cütlükləri üçün Binance əvəzinə pulsuz bir forex API-si (məs.
  Twelve Data, Alpha Vantage) inteqrasiya edilə bilər — token tələb edir
