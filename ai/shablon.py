"""
ai/shablon.py — AI'siz, tayyor shablon/qoida asosida savol-variantlarni
ajratadi. Maqsad: AI'ni faqat "javob aniq bo'lmagan" holatlarda ishlatish
(kunlik so'rov kvotasini tejash uchun).

Qo'llab-quvvatlanadigan formatlar:
- Raqamli savollar: "1. Savol", "1) Savol", "1: Savol", "1-savol: Savol",
  "Savol 1: ..."
- Bo'sh qator bilan ajratilgan bloklar (raqamlanmagan hujjatlar uchun)
- Variant belgilari: "a) ", "A.", "(a)", "[a]", "1)" kabi prefikslar tozalanadi
- To'g'ri javob belgilari (variant ichida, HAR QANDAY tartibda — variant
  qatoridan oldin yoki keyin muhim emas): "[TO'G'RI]" (fayl/oqi.py qizil
  rangni shunday belgilaydi), *yulduzcha*, ✓/✔/✅ belgisi, yoki alohida
  "Javob: B" qatori (variantlardan oldin ham, keyin ham kelishi mumkin).
- Hujjat OXIRIDA barcha savollarga umumiy javob kaliti ("1-b 2-a 3-d..."
  yoki "Javoblar: ...") kelsa, shuni ham topib, mos savollarga bog'laydi
  (agar savolning o'zida alohida belgi bo'lmasa).

Ishonchli natija topilmasa (format juda notekis) — None qaytaradi,
chaqiruvchi to'liq AI orqali ajratishga o'tishi kerak.
"""
import re

_RAQAM_RE = re.compile(
    r"^\s*(?:(\d{1,3})[\.\):]\s*(.+)"
    r"|(\d{1,3})\s*-\s*savol\.?\s*:?\s*(.+)"
    r"|savol\s*(\d{1,3})[\.:]?\s*(.+))$",
    re.IGNORECASE)

_SAVOL_PREFIKS_RE = re.compile(
    r"^\s*(?:\d{1,3}[\.\):]\s*|\d{1,3}\s*-\s*savol\.?\s*:?\s*|savol\s*\d{1,3}[\.:]?\s*)",
    re.IGNORECASE)

# variant prefiksi: "a)", "A.", "(a)", "[a]" — ochiluvchi qavs ixtiyoriy
_VARIANT_HARF_RE = re.compile(r"^\s*[\(\[]?[a-hA-H][\.\)\]]\s*(.+)$")
_VARIANT_RAQAM_RE = re.compile(r"^\s*[\(\[]?\d{1,2}[\.\)\]]\s+(.+)$")

_JAVOB_QATOR_RE = re.compile(
    r"^\s*(?:to'g'ri\s+)?javob\s*[:\-]?\s*([a-hA-H]|\d{1,2})\s*\)?\.?\s*$",
    re.IGNORECASE)

# hujjat oxiridagi umumiy javob kaliti: "1-b", "2. a", "12:d" kabi juftlar
_JAVOB_KALITI_JUFT_RE = re.compile(r"(\d{1,3})\s*[\.\)\-:]\s*([A-Ha-h])(?![a-zA-Z])")
_JAVOB_KALITI_ENG_KAM_JUFT = 5
_JAVOB_KALITI_ENG_KAM_MOSLIK = 0.8
_JAVOB_KALITI_QATORLAR_SONI = 40  # faqat hujjat oxiridan shuncha qatorni tekshiramiz

_TIK_BELGILAR = ("✓", "✔", "✅", "☑")

_ENG_KOP_VARIANT = 6
_ENG_KAM_VARIANT = 2


def ajrat(matn: str):
    """Matndan (savol, variantlar, javob_idx|None) bloklarini topadi.
    Ishonchli bo'lmasa None qaytaradi. Agar hujjat oxirida umumiy javob
    kaliti topilsa, o'sha qatorlar SAVOL/VARIANT sifatida tahlil qilinishdan
    OLDIN olib tashlanadi (aks holda oxirgi savolga "yolg'on variant"
    bo'lib qo'shilib qolardi), so'ng topilgan javoblar mos savollarga
    (o'z ichida alohida belgisi bo'lmaganlariga) qo'llaniladi."""
    qatorlar = matn.split("\n")
    kalit, kalit_indekslari = _javob_kaliti_top(qatorlar)
    if kalit_indekslari:
        qatorlar = [("" if i in kalit_indekslari else q) for i, q in enumerate(qatorlar)]
    bloklar = _raqamli_bloklar(qatorlar)
    if bloklar is None:
        bloklar = _bosh_qator_bloklar(qatorlar)
    if bloklar and kalit:
        for i, b in enumerate(bloklar, start=1):
            if b["javob_idx"] is not None:
                continue
            harf_idx = kalit.get(i)
            if harf_idx is not None and 0 <= harf_idx < len(b["variantlar"]):
                b["javob_idx"] = harf_idx
    return bloklar


def _javob_kaliti_top(qatorlar):
    """Hujjat oxirida ko'pincha keladigan "Javoblar: 1-b 2-a 3-d..." kabi
    umumiy javob kaliti bo'limini topadi (bitta qatorda yoki har biri o'z
    qatorida bo'lishi ham mumkin). ({savol_raqami: harf_indeksi}, shu
    juftlarni bergan qatorlar indekslari to'plami) qaytaradi — ishonchli
    topilmasa (kamida _JAVOB_KALITI_ENG_KAM_JUFT ta, asosan ketma-ket
    ortib boruvchi juftlar bo'lmasa) ikkalasi ham bo'sh qaytadi."""
    boshlanish = max(0, len(qatorlar) - _JAVOB_KALITI_QATORLAR_SONI)
    nomzodlar = []  # (qator_indeksi, [(raqam, harf), ...])
    for i in range(boshlanish, len(qatorlar)):
        juftlar = _JAVOB_KALITI_JUFT_RE.findall(qatorlar[i])
        if juftlar:
            nomzodlar.append((i, juftlar))
    barcha_juftlar = [jp for _, juftlar in nomzodlar for jp in juftlar]
    if len(barcha_juftlar) < _JAVOB_KALITI_ENG_KAM_JUFT:
        return {}, set()
    raqamlar = [int(r) for r, _ in barcha_juftlar]
    mos = sum(1 for i in range(1, len(raqamlar)) if raqamlar[i] - raqamlar[i - 1] == 1)
    if mos / (len(raqamlar) - 1) < _JAVOB_KALITI_ENG_KAM_MOSLIK:
        return {}, set()
    kalit = {int(r): _harf_yoki_raqam_indeks(h) for r, h in barcha_juftlar}
    indekslar = {i for i, _ in nomzodlar}
    # bo'lim sarlavhasi ("Javoblar:", "Javob kaliti" kabi) alohida qatorda
    # kelgan bo'lsa — pastdagi juftliklar bilan aloqasi yo'q, lekin savol
    # matniga qo'shilib qolmasligi uchun uni ham olib tashlaymiz
    birinchi = min(indekslar)
    if birinchi - 1 >= 0:
        oldingi = qatorlar[birinchi - 1].strip().lower()
        if oldingi and len(oldingi) < 40 and any(
                soz in oldingi for soz in ("javob", "kalit", "answer", "key")):
            indekslar.add(birinchi - 1)
    return kalit, indekslar


def _raqam_va_matn(m):
    """_RAQAM_RE moslashuvidan (raqam, qolgan_matn) ni ajratib oladi —
    3 xil uslubdan (N. / N-savol / savol N) qaysi biri mos kelgan bo'lsa ham."""
    for raqam_g, matn_g in ((1, 2), (3, 4), (5, 6)):
        if m.group(raqam_g) is not None:
            return int(m.group(raqam_g)), m.group(matn_g)
    return None, None


def _raqamli_bloklar(qatorlar):
    belgilar = []  # (qator_indeksi, raqam, savol_matni)
    for i, q in enumerate(qatorlar):
        m = _RAQAM_RE.match(q)
        if m:
            raqam, savol_matni = _raqam_va_matn(m)
            belgilar.append((i, raqam, savol_matni))
    if len(belgilar) < 3:
        return None
    # raqamlar asosan ketma-ket (+1) bo'lishi kerak — aks holda bu
    # tasodifiy "1." kabi variant matnlari bo'lishi mumkin, savol emas
    mos = sum(1 for k in range(1, len(belgilar))
              if belgilar[k][1] - belgilar[k - 1][1] == 1)
    if mos / (len(belgilar) - 1) < 0.7:
        return None
    bloklar = []
    for idx, (chiziq, _, savol_matni) in enumerate(belgilar):
        oxir = belgilar[idx + 1][0] if idx + 1 < len(belgilar) else len(qatorlar)
        bloklar.append(_blok_yasash(savol_matni, qatorlar[chiziq + 1:oxir]))
    return _bloklarni_filtrla(bloklar)


def _bosh_qator_bloklar(qatorlar):
    guruhlar, joriy = [], []
    for q in qatorlar:
        if q.strip() == "":
            if joriy:
                guruhlar.append(joriy)
                joriy = []
        else:
            joriy.append(q)
    if joriy:
        guruhlar.append(joriy)
    if len(guruhlar) < 3:
        return None
    bloklar = [_blok_yasash(g[0], g[1:]) for g in guruhlar if g]
    return _bloklarni_filtrla(bloklar)


def _blok_yasash(savol_qatori, variant_qatorlari):
    savol = _savol_tozala(savol_qatori.strip())
    variantlar = []
    togri_idx = None
    javob_qator_idx = None
    for qator in variant_qatorlari:
        if not qator.strip():
            continue
        mj = _JAVOB_QATOR_RE.match(qator)
        if mj:
            javob_qator_idx = _harf_yoki_raqam_indeks(mj.group(1))
            continue
        toza, belgilangan = _belgi_va_toza(qator)
        toza = _variant_prefiks_olib_tashla(toza)
        if not toza:
            continue
        variantlar.append(toza[:100])
        if belgilangan:
            togri_idx = len(variantlar) - 1
    if javob_qator_idx is not None and 0 <= javob_qator_idx < len(variantlar):
        togri_idx = javob_qator_idx
    return {"savol": savol, "variantlar": variantlar[:_ENG_KOP_VARIANT], "javob_idx": togri_idx}


def _belgi_va_toza(qator):
    """Variant qatoridan to'g'ri javob belgisini olib tashlaydi va shu
    variant belgilangan-belgilanmaganini qaytaradi. Qo'llab-quvvatlanadi:
    "[TO'G'RI]" (rang orqali, fayl/oqi.py belgilagan), *yulduzcha*
    (oldida yoki keyin), va ✓/✔/✅/☑ belgisi (oldida yoki keyin)."""
    q = qator.strip()
    belgi = False
    if q.startswith("[TO'G'RI]"):
        q = q[len("[TO'G'RI]"):].strip()
        belgi = True
    for tik in _TIK_BELGILAR:
        if q.startswith(tik):
            q = q[len(tik):].strip()
            belgi = True
        if q.endswith(tik):
            q = q[:-len(tik)].strip()
            belgi = True
    if len(q) > 2 and q.startswith("*"):
        q = q[1:].strip()
        belgi = True
    if len(q) > 2 and q.endswith("*"):
        q = q[:-1].strip()
        belgi = True
    return q, belgi


def _variant_prefiks_olib_tashla(matn):
    m = _VARIANT_HARF_RE.match(matn)
    if m:
        return m.group(1).strip()
    m = _VARIANT_RAQAM_RE.match(matn)
    if m:
        return m.group(1).strip()
    return matn.strip()


def _savol_tozala(matn):
    m = _SAVOL_PREFIKS_RE.match(matn)
    if m:
        return matn[m.end():].strip()
    return matn.strip()


def _harf_yoki_raqam_indeks(s):
    if s.isdigit():
        return int(s) - 1
    return ord(s.lower()) - ord("a")


def _bloklarni_filtrla(bloklar):
    if not bloklar:
        return None
    toliq = [b for b in bloklar
             if b["savol"] and _ENG_KAM_VARIANT <= len(b["variantlar"]) <= _ENG_KOP_VARIANT]
    if len(toliq) / len(bloklar) < 0.75:
        return None
    return toliq
