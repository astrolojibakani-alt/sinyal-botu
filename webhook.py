# ═══════════════════════════════════════════════════════════
#  Sinyal Botu v3 — 5 Kanal
#  ⚡ ThunderBox  |  📊 ZAZ-JV  |  🧠 ZoneIQ
#  🎯 TargetTrend Pro  |  📐 EMABOX
# ═══════════════════════════════════════════════════════════

from flask import Flask, request
from datetime import datetime, timezone, timedelta
import requests, os, logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s")
app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHAT_ID   = os.environ.get("CHAT_ID",   "")

# ── Türkiye saati (UTC+3) — sunucu konumundan bağımsız ────
TZ_TR = timezone(timedelta(hours=3))

SEMBOLLER = {
    "XAUUSD":"Altın","XAGUSD":"Gümüş","BTCUSDT":"Bitcoin",
    "ETHUSDT":"Ethereum","SOLUSDT":"Solana","XRPUSDT":"XRP",
    "USOIL":"Ham Petrol","UKOIL":"Brent Petrol",
    "NAS100":"NASDAQ 100","SPX500":"S&P 500","US30":"Dow Jones",
}
DILIMLER = {
    "1":"1 Dakika","5":"5 Dakika","15":"15 Dakika","30":"30 Dakika",
    "60":"1 Saatlik","240":"4 Saatlik",
    "D":"Günlük","1D":"Günlük","W":"Haftalık","M":"Aylık",
}

def sad(s):  return SEMBOLLER.get(s, s)
def dad(d):  return DILIMLER.get(d, d + " dk")
def saat():  return datetime.now(TZ_TR).strftime("%H:%M")  # BUG #4 DÜZELTİLDİ

def fmt(x):
    try:
        x = float(x)
        if x == 0: return "—"
        return f"{x:,.5f}" if 0 < x < 10 else f"{x:,.2f}"
    except: return str(x)

def bant_genislik(ust, alt):
    try: return fmt(float(ust) - float(alt))
    except: return "—"

def telegram(mesaj: str):
    if not BOT_TOKEN or not CHAT_ID:
        logging.warning("BOT_TOKEN veya CHAT_ID eksik!")
        return
    try:                                                      # BUG #5 DÜZELTİLDİ
        resp = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "HTML"},
            timeout=10
        )
        logging.info(f"Telegram {'OK' if resp.status_code==200 else 'HATA'} → {mesaj[:50]}…")
    except requests.exceptions.RequestException as e:
        logging.error(f"Telegram bağlantı hatası: {e}")

# ═══════════════════════════════════════════════════════════
#  ⚡ THUNDERBOX
#  Format: THUNDERBOX|TIP|SEMBOL|DILIM|CLOSE|UST|ALT|ORTA[|SKOR]
#  TIP: OMEGA | CROSS | VT_BULL | VT_BEAR |
#       BZ_BULL | BZ_BEAR | BZ_ENTRY | BZ_CLOSE_ABOVE | BZ_CLOSE_BELOW
# ═══════════════════════════════════════════════════════════
def isle_thunderbox(p):
    if len(p) < 8: return
    tip, sem, dil = p[1], p[2], p[3]
    cl, ust, alt, orta = p[4], p[5], p[6], p[7]
    skor = p[8] if len(p) > 8 else None
    genislik = bant_genislik(ust, alt)

    TIPLER = {
        "OMEGA":             ("Ω  OMEGA kutusu aktif oldu",                        "Omega"),
        "CROSS":             ("⊗  CROSS kutusu aktif oldu",                        "Cross"),
        "VT_BULL":           ("📦 Voltran kutusu — Boğa",                           "Voltran"),
        "VT_BEAR":           ("📦 Voltran kutusu — Ayı",                            "Voltran"),
        "VT_BULL_STRONG":    ("💚 GÜÇLÜ Voltran — Boğa  (%80+)",                   "Voltran GÜÇLÜ"),
        "VT_BEAR_STRONG":    ("❤️ GÜÇLÜ Voltran — Ayı  (%80+)",                    "Voltran GÜÇLÜ"),
        "BZ_BULL":           ("⚡ Yıldırım — Boğa seviyesi oluştu",                "Yıldırım"),
        "BZ_BEAR":           ("⚡ Yıldırım — Ayı seviyesi oluştu",                 "Yıldırım"),
        "BZ_ENTRY":          ("🎯 Yıldırım bölgesine GİRİLDİ",                     "Yıldırım"),
        "BZ_CLOSE_ABOVE":    ("🟢 Mum yıldırım kutusunun ÜSTÜNDE kapandı — Boğa onayı",  "Yıldırım"),
        "BZ_CLOSE_BELOW":    ("🔴 Mum yıldırım kutusunun ALTINDA kapandı — Ayı kırılımı", "Yıldırım"),
    }
    sinyal_adi, alt_tip = TIPLER.get(tip, (tip, tip))

    mesaj = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ <b>THUNDERBOX</b>  ·  {alt_tip}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>{sinyal_adi}</b>\n"
        f"<i>{sad(sem)}  ·  {dad(dil)}  ·  {saat()}</i>\n"
        f"\n"
        f"📍 Mevcut fiyat  :  <b>{fmt(cl)}</b>\n"
        f"🔼 Üst bant       :  <code>{fmt(ust)}</code>\n"
        f"🔽 Alt bant        :  <code>{fmt(alt)}</code>\n"
        f"⚖️ Orta nokta    :  <code>{fmt(orta)}</code>\n"
        f"\n"
        f"📦 <b>Kutu aralığı</b>\n"
        f"   <code>{fmt(alt)}  —  {fmt(ust)}</code>\n"
        f"   ↕ Genişlik: <b>{genislik}</b>"
    )
    if skor:
        mesaj += f"\n\n🎯 Voltran skoru: <b>%{skor}</b>"
    telegram(mesaj)

# ═══════════════════════════════════════════════════════════
#  📊 ZAZ-JV
#  Format: ZAZJV|TIP|SEMBOL|DILIM|CLOSE|BTOP|BBOT|CONF2X|REJIM
# ═══════════════════════════════════════════════════════════
def isle_zazjv(p):
    if len(p) < 7: return
    tip, sem, dil = p[1], p[2], p[3]
    cl, btop, bbot = p[4], p[5], p[6]
    conf2x = p[7] if len(p) > 7 else "0"
    rejim  = p[8] if len(p) > 8 else "0"
    genislik = bant_genislik(btop, bbot)

    try: orta = fmt((float(btop) + float(bbot)) / 2)
    except: orta = "—"

    rej_txt = "🟢 Boğa Rejimi" if rejim=="1" else ("🔴 Ayı Rejimi" if rejim=="-1" else "⚪ Nötr")
    c2x_txt = "✅ 2X Onay" if conf2x=="1" else "⏳ Tek sinyal"

    MTF = {
        "MTF_G_GREEN":  ("Günlük yeşile döndü + H+A Yeşil",            "+7.4% ort  ·  %67 yukarı  [Tier-1]"),
        "MTF_H_GREEN":  ("Haftalık yeşile döndü + A Yeşil",             "+5.1% ort  ·  %78 yukarı  [Tier-1]"),
        "MTF_G_RED":    ("Günlük kırmızıya döndü + H+A Kırmızı",       "-2.0% ort  ·  %84 aşağı  [Güçlü]"),
        "MTF_4S_GREEN": ("4 Saatlik yeşile döndü + H+A Yeşil",          "+4.8% ort  ·  %62 yukarı  [Tier-2]"),
        "MTF_4S_RED":   ("4 Saatlik kırmızıya döndü + H+A Kırmızı",    "-0.5% ort  ·  %55 aşağı"),
        "MTF_4S_DIP":   ("4S kırmızı — Dip fırsatı (H+A Yeşil)",       "+4.2% ort  ·  %59 yukarı"),
        "DEMA_GREEN":   ("DEMA yeşile geçti — Boğa kutusu açıldı",     "Rejim onaylı giriş"),
        "DEMA_RED":     ("DEMA kırmızıya geçti — Ayı kutusu açıldı",   "Rejim onaylı çıkış"),
        "CONF2X_BULL":  ("2X Boğa Konfirmasyonu",                       "DEMA + STD aynı yönde yeşil"),
        "CONF2X_BEAR":  ("2X Ayı Konfirmasyonu",                        "DEMA + STD aynı yönde kırmızı"),
    }
    sinyal_adi, beklenti = MTF.get(tip, (tip, ""))
    alt_tip = "MTF" if tip.startswith("MTF") else ("2X Onay" if "CONF2X" in tip else "DEMA")

    mesaj = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>ZAZ — Je Veux</b>  ·  {alt_tip}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>{sinyal_adi}</b>\n"
        f"<i>{sad(sem)}  ·  {dad(dil)}  ·  {saat()}</i>\n"
    )
    if beklenti:
        mesaj += f"\n📈 Beklenti: <b>{beklenti}</b>\n"

    mesaj += (
        f"\n"
        f"📍 Mevcut fiyat  :  <b>{fmt(cl)}</b>\n"
        f"🔼 Kutu üstü      :  <code>{fmt(btop)}</code>\n"
        f"🔽 Kutu altı       :  <code>{fmt(bbot)}</code>\n"
        f"⚖️ Orta nokta    :  <code>{orta}</code>\n"
        f"\n"
        f"📦 <b>Kutu aralığı</b>\n"
        f"   <code>{fmt(bbot)}  —  {fmt(btop)}</code>\n"
        f"   ↕ Genişlik: <b>{genislik}</b>\n"
        f"\n"
        f"🔄 Rejim  :  {rej_txt}\n"
        f"✔️ Onay   :  {c2x_txt}"
    )
    telegram(mesaj)

# ═══════════════════════════════════════════════════════════
#  🧠 ZoneIQ
#  Format: ZONEIQ|TIP|SEMBOL|DILIM|CLOSE|ST_UST|ST_ALT|
#          QUALITY|SKOR|GAP|STR|T1|T2|T3|T4|STARS
# ═══════════════════════════════════════════════════════════
def isle_zoneiq(p):
    if len(p) < 8: return
    tip, sem, dil = p[1], p[2], p[3]
    cl    = p[4]
    st_u  = p[5]
    st_a  = p[6]
    ql       = p[7]  if len(p) > 7  else "—"
    skor     = p[8]  if len(p) > 8  else "—"
    gap      = p[9]  if len(p) > 9  else "—"
    strength = p[10] if len(p) > 10 else "—"
    t1       = p[11] if len(p) > 11 else "0"
    t2       = p[12] if len(p) > 12 else "0"
    t3       = p[13] if len(p) > 13 else "0"
    t4       = p[14] if len(p) > 14 else "0"
    stars    = p[15] if len(p) > 15 else ""
    genislik = bant_genislik(st_u, st_a)

    TIPLER = {
        "FLIP_UP":   ("🟢 Trend Dönüşü — Yukarı",  "SuperTrend yön değiştirdi"),
        "FLIP_DOWN": ("🔴 Trend Dönüşü — Aşağı",   "SuperTrend yön değiştirdi"),
        "PREMIUM":   ("⭐ Premium Sinyal",            "GÜÇLÜ + skor ≥ 12"),
        "PB_LONG":   ("🔵 Pullback Long",            "Fiyat aktif desteğe döndü"),
        "PB_SHORT":  ("🟠 Pullback Short",           "Fiyat aktif dirence döndü"),
        "MAG_PB":    ("⚡ Manyetik Pullback",         "Trend dönüşünde ref alanı üstünde"),
        "T1_HIT":    ("🎯 T1 Hedefine Ulaşıldı",    f"Sonraki hedef T2: {fmt(t2)}"),
        "T2_HIT":    ("🎯 T2 Hedefine Ulaşıldı",    f"Sonraki hedef T3: {fmt(t3)}"),
        "T3_HIT":    ("🎯 T3 Hedefine Ulaşıldı",    f"Sonraki hedef T4: {fmt(t4)}"),
    }
    sinyal_adi, aciklama = TIPLER.get(tip, (tip, ""))
    alt_tip = "Hedef" if "HIT" in tip else ("Pullback" if "PB" in tip else "Trend")

    kalite = {"GÜÇLÜ":"🟢 GÜÇLÜ","İYİ":"🟡 İYİ","DİKKAT":"🟠 DİKKAT","TEHLİKE":"🔴 TEHLİKE"}.get(ql, ql)

    # BUG #6 DÜZELTİLDİ — güvenli float dönüşüm
    def safe_positive(val):
        try: return float(val) > 0
        except: return False

    hedef_blok = ""
    if "HIT" not in tip and any(safe_positive(x) for x in [t1, t2, t3, t4]):
        hedef_blok = (
            f"\n"
            f"🎯 <b>Hedefler</b>\n"
            f"   T1 (~%59)  :  <code>{fmt(t1)}</code>\n"
            f"   T2 (~%43)  :  <code>{fmt(t2)}</code>\n"
            f"   T3 (~%33)  :  <code>{fmt(t3)}</code>\n"
            f"   T4 (~%22)  :  <code>{fmt(t4)}</code>"
        )

    mesaj = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🧠 <b>ZoneIQ</b>  ·  {alt_tip}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>{sinyal_adi}</b>\n"
        f"<i>{aciklama}</i>\n"
        f"<i>{sad(sem)}  ·  {dad(dil)}  ·  {saat()}</i>\n"
        f"\n"
        f"📍 Mevcut fiyat  :  <b>{fmt(cl)}</b>\n"
        f"🔼 Kutu üst bant :  <code>{fmt(st_u)}</code>\n"
        f"🔽 Kutu alt bant  :  <code>{fmt(st_a)}</code>\n"
        f"\n"
        f"📦 <b>Kutu aralığı</b>\n"
        f"   <code>{fmt(st_a)}  —  {fmt(st_u)}</code>\n"
        f"   ↕ Genişlik: <b>{genislik}</b>\n"
        f"\n"
        f"🏆 Kalite    :  {kalite}\n"
        f"📊 Skor      :  <b>{skor}/16</b>  {stars}\n"
        f"↔️ Gap       :  <b>{gap}%</b>\n"
        f"💪 Strength  :  <b>{strength}× ATR</b>"
        f"{hedef_blok}"
    )
    telegram(mesaj)

# ═══════════════════════════════════════════════════════════
#  🎯 TARGET TREND PRO
#  Format: TARGETTREND|TIP|SEMBOL|DILIM|CLOSE|ENTRY|T1A|T1B|T2|T3|YON
#  TIP: SIG_UP | SIG_DOWN | T1A_HIT | T1B_HIT | T2_HIT | T3_HIT
# ═══════════════════════════════════════════════════════════
def isle_targettrend(p):
    if len(p) < 9: return
    tip, sem, dil = p[1], p[2], p[3]
    cl    = p[4]
    entry = p[5]
    t1a   = p[6]
    t1b   = p[7]
    t2    = p[8]
    t3    = p[9]  if len(p) > 9  else "—"
    yon   = p[10] if len(p) > 10 else "—"

    TIPLER = {
        "SIG_UP":   ("🟢 Yeni UP Sinyali",       "Trend yukarı döndü"),
        "SIG_DOWN": ("🔴 Yeni DOWN Sinyali",      "Trend aşağı döndü"),
        "T1A_HIT":  ("🎯 T1a Hedefine Ulaşıldı", "Sonraki hedef T1b"),
        "T1B_HIT":  ("🎯 T1b Hedefine Ulaşıldı", "Sonraki hedef T2"),
        "T2_HIT":   ("🎯 T2 Hedefine Ulaşıldı",  "Sonraki hedef T3"),
        "T3_HIT":   ("🎯 T3 Hedefine Ulaşıldı",  "Döngü tamamlandı"),
    }
    sinyal_adi, aciklama = TIPLER.get(tip, (tip, ""))
    alt_tip = "Hedef" if "HIT" in tip else "Sinyal"
    yon_txt = "▲ UP" if yon == "1" else "▼ DOWN"

    hedef_blok = ""
    if "HIT" not in tip:
        hedef_blok = (
            f"\n"
            f"🎯 <b>Hedefler</b>\n"
            f"   T1a  :  <code>{fmt(t1a)}</code>\n"
            f"   T1b  :  <code>{fmt(t1b)}</code>\n"
            f"   T2   :  <code>{fmt(t2)}</code>\n"
            f"   T3   :  <code>{fmt(t3)}</code>"
        )

    mesaj = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 <b>Target Trend Pro</b>  ·  {alt_tip}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>{sinyal_adi}</b>\n"
        f"<i>{aciklama}</i>\n"
        f"<i>{sad(sem)}  ·  {dad(dil)}  ·  {saat()}</i>\n"
        f"\n"
        f"📍 Mevcut fiyat  :  <b>{fmt(cl)}</b>\n"
        f"🔖 Giriş seviyesi :  <code>{fmt(entry)}</code>\n"
        f"↕️ Yön           :  <b>{yon_txt}</b>"
        f"{hedef_blok}"
    )
    telegram(mesaj)

# ═══════════════════════════════════════════════════════════
#  📐 EMABOX
#  Format: EMABOX|CİFT|SEMBOL|DILIM|CLOSE|UST|ALT|SKOR|KATEGORİ
#  ÇİFT: 111x200 | 111x786 | 111x1618 | 200x786 | 200x1618 |
#        786x1618 | 111x4236 | 200x4236 | 786x4236 | 1618x4236
#  KATEGORİ: Tetikleyici | Trend | Mega | Ultra-Mega
# ═══════════════════════════════════════════════════════════
def isle_emabox(p):
    if len(p) < 7: return
    cift, sem, dil = p[1], p[2], p[3]
    cl, ust, alt   = p[4], p[5], p[6]
    skor     = p[7] if len(p) > 7 else "—"
    kategori = p[8] if len(p) > 8 else "—"
    genislik = bant_genislik(ust, alt)

    # Yıldız hesapla
    try:
        s = float(skor)
        if   s >= 58: yildiz = "★★★★★"
        elif s >= 52: yildiz = "★★★★"
        elif s >= 45: yildiz = "★★★"
        elif s >= 38: yildiz = "★★"
        else:         yildiz = "★"
    except:
        yildiz = "★"

    KAT = {
        "Tetikleyici": ("●", "Tetikleyici", "🔵"),
        "Trend":       ("●", "Trend",       "🟠"),
        "Mega":        ("⬤", "Mega",        "🔴"),
        "Ultra-Mega":  ("◉", "Ultra-Mega",  "🟣"),
    }
    dot, kat_adi, kat_emoji = KAT.get(kategori, ("●", kategori, "⚪"))

    mesaj = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📐 <b>EMABOX</b>  ·  {kat_emoji} {kat_adi}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>{dot} EMA {cift.replace('x','×')} — Kesişim</b>\n"
        f"<i>{sad(sem)}  ·  {dad(dil)}  ·  {saat()}</i>\n"
        f"\n"
        f"📍 Mevcut fiyat  :  <b>{fmt(cl)}</b>\n"
        f"🔼 Kutu üstü     :  <code>{fmt(ust)}</code>\n"
        f"🔽 Kutu altı      :  <code>{fmt(alt)}</code>\n"
        f"\n"
        f"📦 <b>Kutu aralığı</b>\n"
        f"   <code>{fmt(alt)}  —  {fmt(ust)}</code>\n"
        f"   ↕ Genişlik: <b>{genislik}</b>\n"
        f"\n"
        f"🏆 Skor  :  <b>{skor} puan</b>  {yildiz}"
    )
    telegram(mesaj)

# ═══════════════════════════════════════════════════════════
#  〰️ ELLIOTT WAVE
#  Format: ELLIOTT|TIP|SEMBOL|DILIM|CLOSE
#  TIP: YENI_DESEN
# ═══════════════════════════════════════════════════════════
def isle_elliott(p):
    if len(p) < 5: return
    tip = p[1]
    sem = p[2]
    dil = p[3]
    cl  = p[4]

    mesaj = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"〰️ <b>Elliott Wave</b>  ·  Yeni Desen\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>🔄 Dalga sayımı değişti</b>\n"
        f"<i>Yeni bir Elliott Wave deseni oluştu</i>\n"
        f"<i>{sad(sem)}  ·  {dad(dil)}  ·  {saat()}</i>\n"
        f"\n"
        f"📍 Mevcut fiyat  :  <b>{fmt(cl)}</b>\n"
        f"\n"
        f"📊 Grafiği kontrol et, dalga yapısı güncellendi."
    )
    telegram(mesaj)

# ═══════════════════════════════════════════════════════════
#  WEBHOOK ENDPOINT
# ═══════════════════════════════════════════════════════════
@app.route("/webhook", methods=["POST"])
def webhook():
    veri = request.get_data(as_text=True).strip()
    logging.info(f"Gelen: {veri[:120]}")
    p = veri.split("|")
    if len(p) < 2: return "invalid", 400
    kaynak = p[0].upper()
    if   kaynak == "THUNDERBOX":  isle_thunderbox(p)
    elif kaynak == "ZAZJV":       isle_zazjv(p)
    elif kaynak == "ZONEIQ":      isle_zoneiq(p)
    elif kaynak == "TARGETTREND": isle_targettrend(p)
    elif kaynak == "EMABOX":      isle_emabox(p)
    elif kaynak == "ELLIOTT":     isle_elliott(p)
    else: logging.warning(f"Bilinmeyen kaynak: {kaynak}")
    return "ok", 200

@app.route("/health", methods=["GET"])
def health():
    import json
    return json.dumps({"durum":"aktif","saat":saat()}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
