"""
Olymp-tərzi Siqnal Botu (Telegram)
----------------------------------
DİQQƏT: Bu bot HEÇ BİR ZƏMANƏTLİ QAZANC vəd etmir. Texniki indikatorlara
əsaslanan analiz köməkçisidir, maliyyə məsləhəti deyil. Binar opsion və
qısa müddətli ticarət yüksək riskli fəaliyyətdir, itirdiyin məbləği
qarşılaya biləcəyindən çox risk etmə.

İKİ REJİM:
1) /signal <pair>  -> Real bazar (kripto, Binance-dən pulsuz açıq data)
   üçün avtomatik RSI + EMA + MACD əsaslı siqnal.
   Məsələn: /signal BTCUSDT

2) /otc             -> OTC (Olymp Trade sintetik) cütlüklər üçün, real
   API mövcud olmadığından, son bir neçə şamın qapanış qiymətini ƏL İLƏ
   daxil edərək eyni indikatorlarla siqnal hesablanır.
   Məsələn: /otc 1.1023 1.1030 1.1015 1.1040 1.1052 1.1048 1.1060

Qurulum:
  pip install -r requirements.txt
  export TELEGRAM_BOT_TOKEN="sənin_tokenin"
  python bot.py
"""

import os
import logging
import requests
import numpy as np
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DISCLAIMER = (
    "\n\n⚠️ Bu, zəmanətli qazanc vəd etmir. Sadəcə texniki analizdir. "
    "Riskini özün qiymətləndir."
)

# ---------------------------------------------------------------------
# İNDİKATOR HESABLAMALARI
# ---------------------------------------------------------------------

def compute_rsi(closes: np.ndarray, period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0
    deltas = np.diff(closes)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def compute_ema(closes: np.ndarray, period: int) -> float:
    if len(closes) < period:
        period = len(closes)
    weights = np.exp(np.linspace(-1.0, 0.0, period))
    weights /= weights.sum()
    return float(np.convolve(closes, weights, mode="valid")[-1])


def compute_macd(closes: np.ndarray):
    if len(closes) < 26:
        return 0.0, 0.0
    ema12 = compute_ema(closes, 12)
    ema26 = compute_ema(closes, 26)
    macd_line = ema12 - ema26
    signal_line = macd_line * 0.9  # sadələşdirilmiş approximasiya
    return macd_line, signal_line


def build_signal(closes: np.ndarray) -> str:
    closes = np.array(closes, dtype=float)
    rsi = compute_rsi(closes)
    ema_fast = compute_ema(closes, min(9, len(closes)))
    ema_slow = compute_ema(closes, min(21, len(closes)))
    macd_line, signal_line = compute_macd(closes)

    votes = []
    # RSI qaydası
    if rsi < 30:
        votes.append("AL")
    elif rsi > 70:
        votes.append("SAT")
    else:
        votes.append("NEYTRAL")

    # EMA cross qaydası
    if ema_fast > ema_slow:
        votes.append("AL")
    elif ema_fast < ema_slow:
        votes.append("SAT")
    else:
        votes.append("NEYTRAL")

    # MACD qaydası
    if macd_line > signal_line:
        votes.append("AL")
    elif macd_line < signal_line:
        votes.append("SAT")
    else:
        votes.append("NEYTRAL")

    al_count = votes.count("AL")
    sat_count = votes.count("SAT")

    if al_count >= 2:
        final = "🟢 AL (YUXARI) siqnalı"
    elif sat_count >= 2:
        final = "🔴 SAT (AŞAĞI) siqnalı"
    else:
        final = "🟡 NEYTRAL — aydın siqnal yoxdur"

    detail = (
        f"RSI(14): {rsi:.2f}\n"
        f"EMA9: {ema_fast:.5f} | EMA21: {ema_slow:.5f}\n"
        f"MACD: {macd_line:.5f} | Signal: {signal_line:.5f}\n\n"
        f"Nəticə: {final}"
    )
    return detail


# ---------------------------------------------------------------------
# REAL BAZAR DATASI (Binance — pulsuz, açıq, key tələb etmir)
# ---------------------------------------------------------------------

def fetch_binance_closes(symbol: str, interval: str = "5m", limit: int = 100):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    closes = [float(candle[4]) for candle in data]
    return closes


# ---------------------------------------------------------------------
# TELEGRAM HANDLER-LƏRİ
# ---------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Salam! Mən texniki analiz siqnal botuyam.\n\n"
        "/signal BTCUSDT — real kripto/forex cütlüyü üçün avtomatik siqnal\n"
        "/otc qiymət1 qiymət2 ... — OTC cütlük üçün əl ilə data daxil et\n\n"
        "Nümunə: /signal BTCUSDT\n"
        "Nümunə: /otc 1.1023 1.1030 1.1015 1.1040 1.1052 1.1048 1.1060"
        + DISCLAIMER
    )


async def signal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("İstifadə: /signal BTCUSDT")
        return
    symbol = context.args[0]
    try:
        closes = fetch_binance_closes(symbol)
        result = build_signal(np.array(closes))
        await update.message.reply_text(f"📊 {symbol.upper()}\n\n{result}{DISCLAIMER}")
    except Exception as e:
        logger.exception("signal_cmd error")
        await update.message.reply_text(
            f"Xəta baş verdi: {e}\nCütlük simvolunu yoxla (məs. BTCUSDT, ETHUSDT)."
        )


async def otc_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 8:
        await update.message.reply_text(
            "Ən azı 8 qapanış qiyməti daxil et (son şamlardan ən köhnədən ən yeniyə sırala).\n"
            "Nümunə: /otc 1.1023 1.1030 1.1015 1.1040 1.1052 1.1048 1.1060 1.1065"
        )
        return
    try:
        closes = [float(x) for x in context.args]
        result = build_signal(np.array(closes))
        await update.message.reply_text(
            f"📊 OTC (əl ilə daxil edilmiş data)\n\n{result}{DISCLAIMER}\n\n"
            "Qeyd: OTC qiymətləri broker tərəfindən sintetik yaradıldığı üçün "
            "bu nəticə real bazar cütlüklərindəki qədər etibarlı deyil."
        )
    except ValueError:
        await update.message.reply_text("Bütün dəyərlər rəqəm olmalıdır.")


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit(
            "TELEGRAM_BOT_TOKEN environment dəyişəni tapılmadı. "
            "Əvvəlcə: export TELEGRAM_BOT_TOKEN='sənin_tokenin'"
        )
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("signal", signal_cmd))
    app.add_handler(CommandHandler("otc", otc_cmd))
    logger.info("Bot işə düşdü...")
    app.run_polling()


if __name__ == "__main__":
    main()
