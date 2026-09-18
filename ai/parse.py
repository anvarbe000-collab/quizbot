"""
ai/parse.py — matndan testlarni ajratadi, javobni aniqlaydi.
Har test: {savol, variantlar:[...], javob: to'g'ri indeks, taxmin: AI topdimi}.

Strategiya (AI so'rovlarini tejash uchun — bepul tarifda kunlik kvota bor):
  1) FAQAT KODGA ASOSLANGAN shablon (ai/shablon.py) bilan savol/variantlarni
     ajratishga harakat qilinadi — AI'siz. Ko'p hollarda javob ham fayldan
     aniq topiladi ([TO'G'RI] rang belgisi, * yulduzcha, "Javob: B" qatori).
  2) Shablon ishonchli natija bersa-yu, ba'zi savollarning javobi aniq
     bo'lmasa — FAQAT o'sha savol+variantlar AI'ga (bitta yengil so'rov,
     ko'p savolni birga) yuborilib, javob indeksini topish so'raladi.
  3) Shablon umuman mos kelmasa (format juda notekis) — eski usul: butun
     matn AI'ga bo'laklab yuborilib, to'liq ajratish so'raladi.
"""
import json
import logging
import re
import time
import openai
from openai import OpenAI

from config import AI_BASE_URL, AI_API_KEY, AI_MODEL
from ai import shablon

log = logging.getLogger(__name__)
# max_retries=0: openai kutubxonasining o'ZI ham qayta urinishga harakat qiladi
# (odatiy holatda), bu bizning qayta urinishimiz bilan qo'shilib ketib,
# kunlik so'rov kvotasini (bepul tarifda juda kichik) tezda tugatib qo'yadi.
# Qayta urinishni FAQAT o'zimiz boshqaramiz.
client = OpenAI(base_url=AI_BASE_URL, api_key=AI_API_KEY, max_retries=0)

_QAYTA_URINISH = 2  # AI vaqtincha band/xato bo'lsa (503/429) qayta urinish soni


class AIXato(Exception):
    """AI xizmatiga ulanishda/javob olishda xatolik (fayl bo'sh emas, lekin
    AI javob bera olmadi) — bu "faylda test yo'q" holatidan farqlanishi kerak."""


def testlarni_ajrat(matn: str) -> tuple:
    """Qaytaradi: (testlar, toliq).
    toliq=False — to'liq AI fallback ishlatilganda, ba'zi qismlar AI
    xatosi tufayli o'tkazib yuborilgan bo'lishi mumkin."""
    bloklar = shablon.ajrat(matn)
    if bloklar:
        return _shablon_natija(bloklar)
    log.info("shablon mos kelmadi — to'liq AI orqali ajratishga o'tildi")
    return _toliq_ai_ajrat(matn)


def _shablon_natija(bloklar):
    testlar = []
    kerakli = {}  # {ro'yxatdagi indeks: (savol, variantlar)} — javobi noaniq
    for i, b in enumerate(bloklar):
        aniq = b["javob_idx"] is not None
        testlar.append({
            "savol": b["savol"],
            "variantlar": b["variantlar"],
            "javob": b["javob_idx"] if aniq else 0,
            "taxmin": not aniq,
        })
        if not aniq:
            kerakli[i] = (b["savol"], b["variantlar"])

    if kerakli:
        try:
            topilgan = _javoblarni_ai_orqali_top(kerakli)
        except Exception:
            log.exception("javob topishda AI xatosi (taxmin sifatida qoldiriladi)")
            topilgan = {}
        for i, j in topilgan.items():
            testlar[i]["javob"] = j
            # taxmin=True qoladi — AI o'zi topdi, foydalanuvchi tekshirsin

    log.info("shablon orqali ajratildi: %d ta test, %d tasi javobi uchun AI ishlatildi",
              len(testlar), len(kerakli))
    return testlar, True


# ---------------------------------------------------------------------------
# 2-BOSQICH: faqat javobi noaniq savollar uchun yengil AI so'rovi
# ---------------------------------------------------------------------------

JAVOB_SYSTEM = """Senga tayyor test savollari va variantlari beriladi (JSON
massiv, har biri {"i": <butun son>, "savol": "...", "variantlar": [...]}),
lekin ularda TO'G'RI JAVOB BELGILANMAGAN. HAR bir savol uchun o'z
bilimingga asoslanib eng to'g'ri variantni top.

Faqat JSON massiv qaytar (izohsiz, boshqa matnsiz):
[{"i": 0, "javob": 2}, {"i": 1, "javob": 0}, ...]
"i" — sendagi ro'yxatdagi indeks (o'zgarmasdan qaytar), "javob" — to'g'ri
variantning ro'yxatdagi indeksi (0 dan boshlab)."""

_JAVOB_BOLAK_HAJMI = 50


def _javoblarni_ai_orqali_top(kerakli: dict) -> dict:
    """kerakli: {indeks: (savol, variantlar)}. Qaytaradi: {indeks: javob_idx}
    (faqat AI muvaffaqiyatli topa olgan javoblar uchun)."""
    natija = {}
    kalitlar = list(kerakli.keys())
    for boshi in range(0, len(kalitlar), _JAVOB_BOLAK_HAJMI):
        bolak_kalitlari = kalitlar[boshi:boshi + _JAVOB_BOLAK_HAJMI]
        payload = [{"i": k, "savol": kerakli[k][0], "variantlar": kerakli[k][1]}
                   for k in bolak_kalitlari]
        try:
            javob_matni = _ai_sorov(JAVOB_SYSTEM, json.dumps(payload, ensure_ascii=False))
        except Exception:
            log.exception("javob-topish bo'lagida AI xatosi")
            continue
        for item in _parse(javob_matni):
            i, j = item.get("i"), item.get("javob")
            if (isinstance(i, int) and i in kerakli and isinstance(j, int)
                    and 0 <= j < len(kerakli[i][1])):
                natija[i] = j
    return natija


# ---------------------------------------------------------------------------
# 3-BOSQICH (fallback): shablon mos kelmasa, butun matnni AI orqali ajratish
# ---------------------------------------------------------------------------

SYSTEM = """Sen test (savol-javob) tahlilchisisan. Berilgan matndan HAMMA
ko'p tanlovli testlarni ajratib ol. Matn turli formatda bo'lishi mumkin
(raqamli, jadvalli, a) b) c) d), yoki oddiy). Sen ularni tushunib, tuzatib ol.

MUHIM: savol oxirida "?" belgisi HAR DOIM ham bo'lavermaydi — ba'zi
o'qituvchilar savolni "?" siz, oddiy gap sifatida yozadi (masalan
"Android dasturlash tili - bu"). Savolni "?" borligiga qarab emas,
undan keyin 2 tadan ko'p qisqa variant qatorlari kelishiga qarab tan ol.
Berilgan matn bo'lagida nechta savolga o'xshash blok bo'lsa, HAMMASINI
qaytar — birortasini ham tashlab ketma (agar u to'liq bo'lsa).

HAR test uchun:
- "savol": savol matni (raqam/harfsiz, toza)
- "variantlar": javob variantlari ro'yxati (2-6 ta). "[TO'G'RI] " prefiksi
  variant matnining bir qismi EMAS — buni variantlar ro'yxatiga qo'shmasdan olib tashla.
- "javob": TO'G'RI variantning indeksi (0 dan boshlab). Aniqlash tartibi:
    1) Agar biror variant oldida "[TO'G'RI]" belgisi bo'lsa (bu — faylda
       o'sha variant qizil rangda yozilganini bildiradi, o'qituvchilar
       shunday belgilashadi) — o'shani ishlat.
    2) Agar matnda boshqa kalit/belgi bo'lsa (masalan * yoki "to'g'ri javob: b"
       yoki oxirida javoblar ro'yxati) — o'shani ishlat.
    3) Agar to'g'ri javob ODATDA BIRINCHI variant bo'lsa (test to'plamlari
       shunday), buni sez va 0 qo'y.
    4) Agar hech biri aniq bo'lmasa — O'ZING to'g'ri javobni top (bilimingga
       ko'ra) va "taxmin": true qo'y.
- "taxmin": true (agar javobni o'zing topgan bo'lsang) yoki false (matndan aniq,
  shu jumladan "[TO'G'RI]" belgisi orqali aniqlangan bo'lsa ham false).

Faqat to'g'ri JSON massiv qaytar (izohsiz):
[{"savol":"...","variantlar":["...","..."],"javob":0,"taxmin":false}, ...]
To'liq bo'lmagan (yarim) savollarni tashlab yubor."""


def _toliq_ai_ajrat(matn: str) -> tuple:
    testlar = []
    korilgan = set()
    bolaklar = list(_bolaklar(matn, hajm=2500, ustma_qator=6))
    muvaffaqiyatli = 0
    xato_boldi = False
    oxirgi_xato = None
    for i, bolak in enumerate(bolaklar):
        try:
            natija = _parse(_ai_sorov(SYSTEM, bolak))
            muvaffaqiyatli += 1
        except Exception as e:
            log.exception("bo'lak %d/%d ni tahlil qilishda xato", i + 1, len(bolaklar))
            oxirgi_xato = e
            xato_boldi = True
            if _kunlik_kvota_tugagan(e):
                log.error("AI kunlik so'rov kvotasi tugadi — qolgan bo'laklar o'tkazib yuborildi")
                break
            continue
        yangi = 0
        for t in natija:
            kalit = _norm(t.get("savol", ""))
            if kalit and kalit not in korilgan and t.get("variantlar"):
                if len(t["variantlar"]) >= 2:
                    korilgan.add(kalit)
                    t.setdefault("javob", 0)
                    t.setdefault("taxmin", False)
                    testlar.append(t)
                    yangi += 1
        log.info("bo'lak %d/%d: %d ta test topildi (jami: %d)",
                  i + 1, len(bolaklar), yangi, len(testlar))
    if muvaffaqiyatli == 0 and oxirgi_xato is not None:
        raise AIXato(str(oxirgi_xato)) from oxirgi_xato
    return testlar, not xato_boldi


# ---------------------------------------------------------------------------
# Umumiy AI so'rov yordamchisi
# ---------------------------------------------------------------------------

def _kunlik_kvota_tugagan(xato) -> bool:
    """429 xato KUNLIK kvota tugaganidan (qayta urinish foydasiz, ertaga
    tiklanadi) yoki daqiqalik cheklovdan (tez tiklanadi) ekanini ajratadi."""
    return isinstance(xato, openai.RateLimitError) and "perday" in str(xato).lower().replace(" ", "")


def _ai_sorov(system_matn, foydalanuvchi_matn):
    xato = None
    for urinish in range(_QAYTA_URINISH):
        try:
            resp = client.chat.completions.create(
                model=AI_MODEL, temperature=0.2, max_tokens=8000,
                messages=[{"role": "system", "content": system_matn},
                          {"role": "user", "content": foydalanuvchi_matn}])
            return resp.choices[0].message.content
        except (openai.InternalServerError, openai.RateLimitError,
                openai.APIConnectionError, openai.APITimeoutError) as e:
            xato = e
            if _kunlik_kvota_tugagan(e):
                break  # kunlik kvota tugagan bo'lsa qayta urinish foydasiz
            if urinish < _QAYTA_URINISH - 1:
                time.sleep(2 * (urinish + 1))
    raise xato


def _parse(matn):
    matn = matn.strip()
    if matn.startswith("```"):
        matn = matn.strip("`")
        if matn.lower().startswith("json"):
            matn = matn[4:]
    b, e = matn.find("["), matn.rfind("]")
    if b != -1 and e != -1:
        matn = matn[b:e + 1]
    data = json.loads(matn)
    return data if isinstance(data, list) else []


def _bolaklar(matn, hajm, ustma_qator):
    """Matnni ~hajm belgili bo'laklarga bo'ladi, FAQAT qator chegarasida
    kesadi (hech qachon savol/qator o'rtasida emas — aks holda AI uni
    "to'liq emas" deb tashlab yuboradi). Qatorlar bo'laklar orasida
    bir necha qator ustma-ust tushadi (chegaradagi savol yo'qolmasin)."""
    qatorlar = matn.split("\n")
    if not qatorlar:
        return
    i = 0
    n = len(qatorlar)
    while i < n:
        bolak, hajmi, j = [], 0, i
        while j < n and (hajmi <= hajm or j == i):
            bolak.append(qatorlar[j])
            hajmi += len(qatorlar[j]) + 1
            j += 1
        yield "\n".join(bolak)
        if j >= n:
            break
        i = max(i + 1, j - ustma_qator)


def _norm(s):
    return re.sub(r"\s+", " ", (s or "").lower()).strip()[:120]
