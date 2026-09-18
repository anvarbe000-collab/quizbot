"""bot/keyboards.py — fayl yuklangandan keyin ko'rsatiladigan tugmalar."""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.matnlar import t, TILLAR

NECHTA_VARIANTLARI = [10, 20, 30, 40, 50]
SONIYA_VARIANTLARI = [5, 10, 15, 20, 30, 40]


_RAQAM_EMOJI = {"0": "0️⃣", "1": "1️⃣", "2": "2️⃣", "3": "3️⃣", "4": "4️⃣",
                "5": "5️⃣", "6": "6️⃣", "7": "7️⃣", "8": "8️⃣", "9": "9️⃣"}


def _raqam_belgisi(n: int) -> str:
    """Sonni keycap-emoji ko'rinishiga o'giradi (masalan 20 -> "2️⃣0️⃣"),
    tugmalar ko'zga yaqqolroq tashlanishi uchun."""
    return "".join(_RAQAM_EMOJI[raqam] for raqam in str(n))


def nechta_klaviatura(jami, til):
    """Har to'plamda nechtadan savol bo'lishini tanlash tugmalari: doimiy
    10/20/30/40/50 + "Hammasi bitta" (bo'lmasdan, bitta test). Kattaroq
    ko'rinishi uchun har qatorda faqat 2 tadan tugma."""
    variantlar = [v for v in NECHTA_VARIANTLARI if v < jami]
    qatorlar, qator = [], []
    for v in variantlar:
        qator.append(InlineKeyboardButton(_raqam_belgisi(v), callback_data=f"nechta:{v}"))
        if len(qator) == 2:
            qatorlar.append(qator); qator = []
    if qator:
        qatorlar.append(qator)
    qatorlar.append([InlineKeyboardButton(t("tugma_hammasi_bitta", til), callback_data=f"nechta:{jami}")])
    return InlineKeyboardMarkup(qatorlar)


def tartib_klaviatura(til):
    """Savol/javob tartibini tanlash: asl holat, savollar aralash,
    javoblar aralash, yoki ikkalasi ham aralash."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("tugma_asl", til), callback_data="tartib:asl")],
        [InlineKeyboardButton(t("tugma_savol_aralash", til), callback_data="tartib:savol")],
        [InlineKeyboardButton(t("tugma_javob_aralash", til), callback_data="tartib:javob")],
        [InlineKeyboardButton(t("tugma_hammasi_aralash", til), callback_data="tartib:hammasi")],
    ])


def soniya_klaviatura(til):
    """Har savolga necha soniya berilishini tanlash tugmalari. Kattaroq
    ko'rinishi uchun har qatorda faqat 2 tadan tugma."""
    qatorlar, qator = [], []
    for v in SONIYA_VARIANTLARI:
        qator.append(InlineKeyboardButton(t("tugma_soniya", til, n=v), callback_data=f"soniya:{v}"))
        if len(qator) == 2:
            qatorlar.append(qator); qator = []
    if qator:
        qatorlar.append(qator)
    return InlineKeyboardMarkup(qatorlar)


def tayyor_klaviatura(quiz_id, bot_username, til):
    """QuizBot uslubidagi: tayyorman / ulashish / guruhda boshlash tugmalari."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("tugma_tayyorman", til), callback_data=f"tayyor:{quiz_id}")],
        [InlineKeyboardButton(t("tugma_ulashish", til),
                               url=f"https://t.me/{bot_username}?start=viktorina_{quiz_id}")],
        [InlineKeyboardButton(t("tugma_guruhda", til),
                               url=f"https://t.me/{bot_username}?startgroup=viktorina_{quiz_id}")],
    ])


def davom_klaviatura(sessiya_id, til):
    """3 ta savolga javob kelmagach to'xtaganda: davom ettirish / tugatish
    (kattaroq ko'rinishi uchun har biri o'z qatorida)."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("tugma_davom", til), callback_data=f"davom:{sessiya_id}")],
        [InlineKeyboardButton(t("tugma_tugatish", til), callback_data=f"tugat:{sessiya_id}")],
    ])


def yakuniy_klaviatura(quiz_id, bot_username, til, keyingi_quiz_id=None, keyingi_nomi=None):
    """Test yakunlangandagi tugmalar: (agar bo'lsa) keyingi to'plam / qayta
    urinish / guruhda boshlash / ulashish."""
    qatorlar = []
    if keyingi_quiz_id:
        matn = t("tugma_keyingi_toplam", til)
        if keyingi_nomi:
            matn = f"{matn} ({keyingi_nomi})"
        qatorlar.append([InlineKeyboardButton(matn[:64], callback_data=f"tayyor:{keyingi_quiz_id}")])
    qatorlar.append([InlineKeyboardButton(t("tugma_qayta_urinish", til), callback_data=f"tayyor:{quiz_id}")])
    qatorlar.append([InlineKeyboardButton(t("tugma_guruhda", til),
                                          url=f"https://t.me/{bot_username}?startgroup=viktorina_{quiz_id}")])
    qatorlar.append([InlineKeyboardButton(t("tugma_ulashish", til),
                                          url=f"https://t.me/{bot_username}?start=viktorina_{quiz_id}")])
    return InlineKeyboardMarkup(qatorlar)


def til_klaviatura():
    """Tilni tanlash tugmalari (/lang)."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(nomi, callback_data=f"til:{kod}")] for kod, nomi in TILLAR.items()
    ])


def testlarim_klaviatura(royxat):
    """/testlarim — foydalanuvchi yaratgan viktorinalar ro'yxati, har biri
    bosilsa to'g'ridan-to'g'ri o'sha testni boshlaydi."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(nomi[:64], callback_data=f"tayyor:{quiz_id}")] for quiz_id, nomi in royxat
    ])


def tolov_klaviatura(tolov_id, til):
    """Admin chatiga yuboriladigan chek xabaridagi: tasdiqlash / rad etish."""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(t("tugma_tolov_tasdiqlash", til), callback_data=f"tolovtasdiq:{tolov_id}"),
        InlineKeyboardButton(t("tugma_tolov_rad", til), callback_data=f"tolovrad:{tolov_id}"),
    ]])


def asosiy_klaviatura(til, narx=None):
    """/start xabaridagi asosiy tugma — "Fayldan test yaratish". Agar
    to'lov yoqilgan bo'lsa (narx berilsa), narxi ochiq ko'rsatiladi."""
    matn = t("tugma_fayldan_test_pullik", til, narx=narx) if narx else t("tugma_fayldan_test_bepul", til)
    return InlineKeyboardMarkup([[InlineKeyboardButton(matn, callback_data="newquiz_tugma")]])
