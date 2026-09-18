"""
bot/handlers.py — Test bot oqimi:
  fayl (Word/PDF) -> matn -> testlarni ajratish -> "nechtadan?" ->
  "qanday tartibda?" -> "necha soniyadan?" -> "Tayyorman!" -> Telegram
  Quiz (poll, vaqt chegarasi bilan, QuizBot uslubida) -> yakuniy natija.

  Xususiyatlar:
  - "Nechtadan" tanlansa, fayldagi BARCHA savollar shu o'lchamdagi
    bo'laklarga bo'linib, HAR biri uchun ALOHIDA test (quiz_id, o'z
    havolasi, o'z reytingi) yaratiladi — masalan 101 ta savol, 10tadan
    tanlansa 11 ta mustaqil test hosil bo'ladi. HAMMASI uchun DARHOL
    o'z "tayyor bo'ling" kartochkasi yuboriladi (tayyorman/ulashish/
    guruhda tugmalari bilan) — xohlagan to'plamni to'g'ridan-to'g'ri
    boshlash mumkin, qo'shimcha "qaysi to'plam" menyusi yo'q. Har biri
    tugagach, qulaylik uchun yakuniy natija ekranida "Keyingi to'plam"
    tugmasi ham chiqadi.
  - Savol/javob tartibi: asl holat / savollar aralash / javoblar aralash /
    ikkalasi ham aralash — foydalanuvchi tanlaydi.
  - Shaxsiy chatda javob berilgach, to'g'ri/xato belgisi ko'rinishi uchun
    qisqa pauzadan keyin keyingi savolga o'tiladi (vaqt tugashini
    kutmaydi); guruhda esa har doim to'liq vaqt kutiladi.
  - Ketma-ket 3 ta savolga javob kelmasa, test avtomatik to'xtaydi.
  - Har savol "[N/jami]" prefiksi bilan ko'rsatiladi (progress).
  - Test tugagach: to'g'ri/xato/tashlab ketilgan soni, sarflangan vaqt,
    va shu testni yechganlar orasidagi o'rin (reyting) ko'rsatiladi.
  - Barcha matnlar 3 tilda (uz/ru/en) — /lang orqali tanlanadi.
  - Viktorinalar va reyting SQLite bazasida saqlanadi (bot qayta ishga
    tushirilsa ham yo'qolmaydi).
"""
import html
import os
import time
import uuid
import random
import asyncio
import logging
import tempfile

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import PollType

import click_pay
import config
import db
from fayl.oqi import matn_ol
from ai.parse import testlarni_ajrat, AIXato
from bot.matnlar import t, STANDART_TIL
from bot.keyboards import (nechta_klaviatura, tartib_klaviatura, soniya_klaviatura,
                           tayyor_klaviatura, davom_klaviatura, yakuniy_klaviatura,
                           til_klaviatura, testlarim_klaviatura, tolov_invoice_klaviatura,
                           asosiy_klaviatura)

log = logging.getLogger(__name__)
KETMA_KET_JAVOBSIZ_CHEGARA = 3   # shuncha savolga javob kelmasa test to'xtaydi
JAVOBDAN_KEYINGI_PAUZA = 2.0     # shaxsiy chatda: to'g'ri/xato belgisini ko'rish uchun pauza


def _esc(matn) -> str:
    """Foydalanuvchi kiritgan (ism, fayl nomi kabi) matnni HTML xabarlarga
    xavfsiz qo'shish uchun ekranlaydi (aks holda "<"/"&" kabi belgilar
    xabar formatini buzishi yoki noto'g'ri render bo'lishi mumkin edi)."""
    return html.escape(str(matn))


async def _almashtir(xabar, matn, reply_markup=None, parse_mode=None):
    """Xabarni ('bosqich' xabarini) yangi matn/tugmalar bilan TAHRIRLAYDI —
    shunda eski bosqich yo'qolib, yangisi uning o'rnida chiqadi (chatda
    "o'lik" tugmali xabarlar to'planib qolmasligi uchun). Tahrirlash
    imkonsiz bo'lsa (masalan xabar juda eski), yangi xabar yuboradi."""
    try:
        await xabar.edit_text(matn, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception:
        await xabar.reply_text(matn, reply_markup=reply_markup, parse_mode=parse_mode)


async def _til(ctx: ContextTypes.DEFAULT_TYPE, uid: int) -> str:
    """Foydalanuvchi tilini oladi: avval xotiradan (tez), bo'lmasa bazadan."""
    til = ctx.user_data.get("til")
    if til is None:
        til = await db.til_olish(uid) or STANDART_TIL
        ctx.user_data["til"] = til
    return til


async def _viktorina_olish(ctx: ContextTypes.DEFAULT_TYPE, quiz_id: str):
    """Viktorinani avval xotiradan, topilmasa bazadan o'qiydi (bot qayta
    ishga tushirilgan bo'lsa ham ishlashi uchun)."""
    ma = ctx.bot_data.get("viktorinalar", {}).get(quiz_id)
    if ma:
        return ma
    ma = await db.viktorina_olish(quiz_id)
    if ma:
        ctx.bot_data.setdefault("viktorinalar", {})[quiz_id] = ma
    return ma


def _narx_qatori(kalit: str, til: str) -> str:
    """To'lov yoqilgan bo'lsa narx qatorini (belgilangan kalit bo'yicha),
    aks holda bo'sh qator qaytaradi — matnlar shablonidagi {narx_qatori}
    o'rniga qo'yiladi."""
    if not config.TOLOV_YOQILGAN:
        return ""
    return t(kalit, til, narx=_esc(config.TOLOV_NARXI))


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    til = await _til(ctx, uid)
    if ctx.args:
        payload = ctx.args[0]
        if payload.startswith("viktorina_"):
            await _tayyor_xabar(update.message, ctx, payload[len("viktorina_"):], til)
            return
    narx = config.TOLOV_NARXI if config.TOLOV_YOQILGAN else None
    matn = t("salom", til, narx_qatori=_narx_qatori("salom_narx_qatori", til))
    await update.message.reply_text(matn, reply_markup=asosiy_klaviatura(til, narx), parse_mode="HTML")


async def newquiz_tugma_bosildi(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/start xabaridagi asosiy "Fayldan test yaratish" tugmasi — /newquiz
    bilan bir xil, faqat tugma orqali bosiladi."""
    q = update.callback_query
    await q.answer()
    til = await _til(ctx, q.from_user.id)
    matn = t("newquiz_sorov", til, narx_qatori=_narx_qatori("newquiz_narx_qatori", til))
    await q.message.reply_text(matn, parse_mode="HTML")


async def yordam(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    til = await _til(ctx, update.effective_user.id)
    await update.message.reply_text(t("yordam", til), parse_mode="HTML")


async def newquiz(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/newquiz — @QuizBot'dagi kabi, fayl yuborishni so'raydigan asosiy buyruq."""
    til = await _til(ctx, update.effective_user.id)
    matn = t("newquiz_sorov", til, narx_qatori=_narx_qatori("newquiz_narx_qatori", til))
    await update.message.reply_text(matn, parse_mode="HTML")


async def lang_komandasi(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    til = await _til(ctx, update.effective_user.id)
    await update.message.reply_text(t("til_tanlang", til), reply_markup=til_klaviatura())


async def til_tanlandi(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    yangi_til = q.data.split(":", 1)[1]
    ctx.user_data["til"] = yangi_til
    await db.til_saqlash(q.from_user.id, yangi_til)
    await _almashtir(q.message, t("til_ozgardi", yangi_til))


async def testlarim(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    til = await _til(ctx, uid)
    royxat = await db.foydalanuvchi_viktorinalari(uid)
    if not royxat:
        await update.message.reply_text(t("testlarim_royxat_yoq", til))
        return
    await update.message.reply_text(t("testlarim_sarlavha", til), reply_markup=testlarim_klaviatura(royxat))


async def stop_komandasi(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Joriy testni BATAMOM to'xtatadi. MUHIM: shu vaqtda fonda ishlab
    turgan _savollarni_yubor sikli ham darhol to'xtashi kerak — shuning
    uchun lug'atdan olib tashlashning o'zi yetarli emas (sikl o'sha DICT
    OBYEKTIga hali ham ishora qilib turadi), "toxtatilgan" bayrog'ini ham
    o'sha obyektga qo'yamiz, sikl buni tekshirib chiqib ketadi — aks holda
    /stop natija chiqargandan KEYIN ham sikl davom etib, keyinroq yana
    savol yuborishi yoki "davom ettirish" so'rovi chiqarishi mumkin edi."""
    uid = update.effective_user.id
    til = await _til(ctx, uid)
    sessiyalar = ctx.bot_data.get("sessiyalar", {})
    sessiya_id = next((sid for sid, s in sessiyalar.items() if s["uid"] == uid), None)
    if not sessiya_id:
        await update.message.reply_text(t("stop_faol_yoq", til))
        return
    s = sessiyalar.pop(sessiya_id)
    s["toxtatilgan"] = True
    await update.message.reply_text(t("stop_toxtatildi", til))
    await _yakuniy_natija(ctx, update.effective_chat.id, s, s.get("til", til))


async def fayl_qabul(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Fayl qabul qilinganda: agar to'lov YOQILGAN bo'lsa va yuboruvchi
    admin bo'lmasa — faylni saqlab, Click orqali to'lov havolasini
    beramiz (haqiqiy ishlov Click "Complete" webhook orqali TASDIQLANGANDAN
    keyin AVTOMATIK boshlanadi — admin aralashuvi kerak emas). Aks holda
    darhol ishlanadi."""
    uid = update.effective_user.id
    til = await _til(ctx, uid)
    doc = update.message.document
    nom = (doc.file_name or "").lower()
    if not (nom.endswith(".docx") or nom.endswith(".pdf")):
        await update.message.reply_text(t("faqat_fayl", til))
        return

    f = await doc.get_file()
    fayl_baytlari = bytes(await f.download_as_bytearray())

    if not config.TOLOV_YOQILGAN or uid == config.ADMIN_CHAT_ID:
        await _faylni_qayta_ishlash(ctx, uid, update.effective_chat.id, doc.file_name, fayl_baytlari, til)
        return

    kutilayotgan_id = ctx.user_data.get("tolov_id")
    if kutilayotgan_id:
        kutilayotgan = await db.tolov_olish(kutilayotgan_id)
        if kutilayotgan and kutilayotgan["holat"] in ("kutilmoqda", "tayyorlangan"):
            await update.message.reply_text(t("tolov_kutilmoqda_ogohlantirish", til))
            return

    tolov_id = uuid.uuid4().hex[:10]
    await db.tolov_yaratish(tolov_id, uid, update.effective_user.full_name,
                            doc.file_name, fayl_baytlari, config.TOLOV_NARXI, time.time())
    ctx.user_data["tolov_id"] = tolov_id
    havola = click_pay.invoice_url(tolov_id, config.TOLOV_NARXI)
    await update.message.reply_text(
        t("tolov_sorov", til, narx=_esc(config.TOLOV_NARXI)),
        reply_markup=tolov_invoice_klaviatura(havola, til), parse_mode="HTML")


async def _faylni_qayta_ishlash(ctx: ContextTypes.DEFAULT_TYPE, uid: int, chat_id: int,
                                fayl_nomi: str, fayl_baytlari: bytes, til: str):
    """Fayl baytlarini diskka yozib, matn/testlarni ajratadi va "nechtadan?"
    so'rovini chiqaradi. To'lovsiz (yoki admin) yuklashda VA to'lov
    tasdiqlangandan keyin — ikkalasida ham shu funksiya ishlatiladi.
    Natija (testlar) shu FOYDALANUVCHI uchun keyingi qadamlar (nechta/
    tartib/soniya) o'qiy oladigan joyga (application.user_data[uid])
    yoziladi — bu admin tasdiqidan keyin ham to'g'ri ishlashi uchun kerak
    (o'sha payt handler ADMIN kontekstida ishlaydi, talaba emas)."""
    kutish = await ctx.bot.send_message(chat_id, t("fayl_oqilmoqda", til))
    yol = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4().hex}{os.path.splitext(fayl_nomi or '')[1]}")
    with open(yol, "wb") as fobj:
        fobj.write(fayl_baytlari)

    try:
        matn = matn_ol(yol)
    except Exception:
        log.exception("fayl o'qishda xato")
        await kutish.edit_text(t("fayl_xato", til))
        return
    finally:
        if os.path.exists(yol):
            os.remove(yol)

    try:
        testlar, toliq = testlarni_ajrat(matn)
    except AIXato:
        log.exception("AI xizmati javob bermadi")
        await kutish.edit_text(t("ai_xato", til))
        return

    if not testlar:
        await kutish.edit_text(t("test_topilmadi", til))
        return

    foydalanuvchi_malumoti = ctx.application.user_data[uid]
    foydalanuvchi_malumoti["testlar"] = testlar
    foydalanuvchi_malumoti["fayl_nomi"] = os.path.splitext(fayl_nomi or "Test")[0]
    taxmin = sum(1 for t_ in testlar if t_.get("taxmin"))
    xabar = t("topildi", til, n=len(testlar))
    if not toliq:
        xabar += t("toliq_emas_ogohlantirish", til)
    if taxmin:
        xabar += t("taxmin_ogohlantirish", til, n=taxmin)
    xabar += t("nechtadan_sorov", til)
    await kutish.edit_text(xabar, reply_markup=nechta_klaviatura(len(testlar), til))


class _KontekstSimulyatori:
    """Click webhook (aiohttp) kabi PTB Update oqimidan TASHQARIDA turgan
    kod uchun ctx-ga o'xshash minimal obyekt — _til()/_faylni_qayta_ishlash()
    kabi funksiyalarni O'ZGARTIRMASDAN qayta ishlatish imkonini beradi.
    user_data — aynan shu FOYDALANUVCHI (uid) uchun bo'lgan bo'lak, chunki
    webhook allaqachon "kim uchun" ekanini biladi (PTB Update'dan farqli)."""
    def __init__(self, application, uid: int):
        self.bot = application.bot
        self.bot_data = application.bot_data
        self.application = application
        self.user_data = application.user_data[uid]


async def click_tolov_muvaffaqiyatli(application, tolov_id: str):
    """Click "Complete" webhook to'lovni TASDIQLAGANDA chaqiriladi (aiohttp
    handler ichidan, click_pay.complete() orqali) — talabaga xabar beradi
    va faylni AVTOMATIK ishga tushiradi (admin aralashuvisiz)."""
    tolov = await db.tolov_olish(tolov_id)
    if not tolov:
        log.error("click_tolov_muvaffaqiyatli: to'lov topilmadi id=%s", tolov_id)
        return
    ctx = _KontekstSimulyatori(application, tolov["uid"])
    til = await _til(ctx, tolov["uid"])
    try:
        await application.bot.send_message(
            tolov["uid"], t("tolov_tasdiqlandi_xabari", til), parse_mode="HTML")
    except Exception:
        log.exception("talabaga to'lov xabarini yuborishda xato")

    await _faylni_qayta_ishlash(ctx, tolov["uid"], tolov["uid"], tolov["fayl_nomi"], tolov["fayl_bayt"], til)

    if config.ADMIN_CHAT_ID:
        try:
            await application.bot.send_message(
                config.ADMIN_CHAT_ID,
                f"💰 To'lov qabul qilindi: {_esc(tolov['ism'])} — {tolov['narxi']} so'm",
                parse_mode="HTML")
        except Exception:
            log.exception("adminga to'lov haqida xabar berishda xato")


async def nechta_tanlandi(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    til = await _til(ctx, q.from_user.id)
    testlar = ctx.user_data.get("testlar")
    if not testlar:
        await q.message.reply_text(t("avval_fayl", til))
        return
    ctx.user_data["nechta"] = int(q.data.split(":", 1)[1])
    await _almashtir(q.message, t("tartib_sorov", til), tartib_klaviatura(til))


async def tartib_tanlandi(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    til = await _til(ctx, q.from_user.id)
    testlar = ctx.user_data.get("testlar")
    if not testlar:
        await q.message.reply_text(t("avval_fayl", til))
        return
    ctx.user_data["tartib"] = q.data.split(":", 1)[1]  # asl | savol | javob | hammasi
    await _almashtir(q.message, t("soniya_sorov", til), soniya_klaviatura(til))


async def soniya_tanlandi(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Fayldagi BARCHA savollarni "nechta" o'lchamdagi bo'laklarga bo'lib,
    HAR biri uchun ALOHIDA test (quiz) yaratadi (masalan 101 ta savol, 10tadan
    tanlansa -> 1-10, 11-20, ..., 91-101 — 11 ta mustaqil test). Har biri o'z
    havolasi/reytingiga ega, va HAR biri uchun DARHOL o'z "tayyor bo'ling"
    kartochkasi (tayyorman/ulashish/guruhda tugmalari bilan) yuboriladi —
    alohida "qaysi to'plamni tanlaysiz" menyusi kerak emas, xohlagan
    to'plamni to'g'ridan-to'g'ri boshlash mumkin. Har bir to'plam bazaga
    ham yoziladi (bot qayta ishga tushirilsa ham yo'qolmasligi uchun)."""
    q = update.callback_query
    await q.answer()
    til = await _til(ctx, q.from_user.id)
    soniya = int(q.data.split(":", 1)[1])
    testlar = ctx.user_data.get("testlar")
    nechta = ctx.user_data.get("nechta")
    tartib = ctx.user_data.get("tartib", "asl")
    if not testlar or not nechta:
        await q.message.reply_text(t("avval_fayl_sozlama", til))
        return
    nomi = ctx.user_data.get("fayl_nomi", "Test")
    egasi_id = q.from_user.id

    boshlarichlar = list(range(0, len(testlar), nechta))
    quiz_idlar = []
    for bosh in boshlarichlar:
        oxir = min(bosh + nechta, len(testlar))
        bolak_nomi = nomi if len(boshlarichlar) == 1 else f"{nomi} ({bosh + 1}-{oxir})"
        quiz_id = uuid.uuid4().hex[:10]
        ctx.bot_data.setdefault("viktorinalar", {})[quiz_id] = {
            "nomi": bolak_nomi, "testlar": testlar[bosh:oxir], "soniya": soniya,
            "tartib": tartib, "keyingi_quiz_id": None, "egasi_id": egasi_id}
        quiz_idlar.append(quiz_id)

    for oldingi, keyingi in zip(quiz_idlar, quiz_idlar[1:]):
        ctx.bot_data["viktorinalar"][oldingi]["keyingi_quiz_id"] = keyingi

    yaratilgan_vaqt = time.time()
    for quiz_id in quiz_idlar:
        ma = ctx.bot_data["viktorinalar"][quiz_id]
        await db.viktorina_saqlash(quiz_id, egasi_id, ma["nomi"], ma["testlar"], ma["soniya"],
                                   ma["tartib"], ma["keyingi_quiz_id"], yaratilgan_vaqt)

    # "soniya" bosqichi tugadi — o'sha xabarni tugmasiz tasdiqqa aylantiramiz
    await _almashtir(q.message, t("sozlamalar_saqlandi", til))
    if len(quiz_idlar) > 1:
        await q.message.reply_text(t("bolaklarga_bolindi", til, n=len(quiz_idlar)))
    for quiz_id in quiz_idlar:
        await _tayyor_xabar(q.message, ctx, quiz_id, til)
        if len(quiz_idlar) > 1:
            await asyncio.sleep(0.3)  # flood'ga tushmaslik uchun


async def _tayyor_xabar(xabar_manbasi, ctx: ContextTypes.DEFAULT_TYPE, quiz_id: str, til: str):
    """QuizBot uslubidagi "tayyor bo'ling" xabarini chiqaradi (tugmalar bilan)."""
    ma = await _viktorina_olish(ctx, quiz_id)
    if not ma:
        await xabar_manbasi.reply_text(t("test_topilmadi_qayta", til))
        return
    username = (await ctx.bot.get_me()).username
    matn = t("tayyor_bolib_karta", til, nomi=_esc(ma["nomi"]), savollar=len(ma["testlar"]), soniya=ma["soniya"])
    await xabar_manbasi.reply_text(matn, reply_markup=tayyor_klaviatura(quiz_id, username, til), parse_mode="HTML")


async def tayyor_bosildi(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """"Men tayyorman!" (yoki "Qayta urinish") bosilganda — yangi sessiya
    yaratib viktorinani boshlaymiz."""
    q = update.callback_query
    await q.answer()
    til = await _til(ctx, q.from_user.id)
    quiz_id = q.data.split(":", 1)[1]
    ma = await _viktorina_olish(ctx, quiz_id)
    if not ma:
        await q.message.reply_text(t("test_topilmadi_qayta", til))
        return

    tartib = ma.get("tartib", "asl")
    savollar = list(ma["testlar"])
    if tartib in ("savol", "hammasi"):
        random.shuffle(savollar)
    variantlarni_aralashtir = tartib in ("javob", "hammasi")

    sessiya_id = uuid.uuid4().hex[:8]
    guruhmi = q.message.chat.type != "private"
    ctx.bot_data.setdefault("sessiyalar", {})[sessiya_id] = {
        "quiz_id": quiz_id, "savollar": savollar, "keyingi_indeks": 0,
        "ketma_ket_javobsiz": 0, "soniya": ma["soniya"],
        "variantlarni_aralashtir": variantlarni_aralashtir, "guruhmi": guruhmi,
        "ism": q.from_user.full_name, "uid": q.from_user.id, "til": til,
        "tugri": 0, "notogri": 0, "boshlangan_vaqt": time.monotonic(),
    }
    chat_id = q.message.chat_id
    # "tayyor bo'ling" kartochkasini (tugmalari bilan) "boshlandi" holatiga
    # o'zgartiramiz — endi eskirgan "Men tayyorman!" tugmasi qolmaydi
    await _almashtir(q.message, t("tayyor_boshlandi_karta", til, nomi=ma["nomi"], savollar=len(savollar), soniya=ma["soniya"]))
    await _sanoq(ctx, chat_id, til)
    await _savollarni_yubor(ctx, chat_id, sessiya_id)


async def _sanoq(ctx: ContextTypes.DEFAULT_TYPE, chat_id: int, til: str):
    """3, 2, 1, GO! sanog'ini ko'rsatadi (bitta xabarni tahrirlab) — testni
    boshlashdan oldingi professional kirish (@QuizBot uslubida)."""
    try:
        xabar = await ctx.bot.send_message(chat_id, "3️⃣")
        for matn in ("2️⃣", "1️⃣"):
            await asyncio.sleep(1)
            await xabar.edit_text(matn)
        await asyncio.sleep(1)
        await xabar.edit_text(t("sanoq_go", til))
        await asyncio.sleep(0.6)
    except Exception:
        log.exception("sanoq xatosi")


async def davom_bosildi(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    sessiya_id = q.data.split(":", 1)[1]
    s = ctx.bot_data.get("sessiyalar", {}).get(sessiya_id)
    til = await _til(ctx, q.from_user.id)
    if not s:
        await _almashtir(q.message, t("sessiya_topilmadi", til))
        return
    s["ketma_ket_javobsiz"] = 0
    await _almashtir(q.message, t("davom_etmoqda", s.get("til", til)))
    await _savollarni_yubor(ctx, q.message.chat_id, sessiya_id)


async def tugat_bosildi(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    sessiya_id = q.data.split(":", 1)[1]
    s = ctx.bot_data.get("sessiyalar", {}).pop(sessiya_id, None)
    til = await _til(ctx, q.from_user.id)
    if not s:
        await _almashtir(q.message, t("sessiya_topilmadi", til))
        return
    s["toxtatilgan"] = True
    natija_tili = s.get("til", til)
    await _almashtir(q.message, t("stop_toxtatildi_karta", natija_tili))
    await _yakuniy_natija(ctx, q.message.chat_id, s, natija_tili)


async def _savollarni_yubor(ctx: ContextTypes.DEFAULT_TYPE, chat_id: int, sessiya_id: str):
    """Sessiyaning keyingi_indeks'dan boshlab (shu to'plamdagi) savollarni
    ketma-ket yuboradi. Ketma-ket KETMA_KET_JAVOBSIZ_CHEGARA ta savolga
    javob kelmasa to'xtaydi va davom/tugatish tugmalarini chiqarib qaytadi."""
    s = ctx.bot_data.get("sessiyalar", {}).get(sessiya_id)
    if not s:
        return
    til = s.get("til", STANDART_TIL)
    savollar = s["savollar"]
    jami = len(savollar)
    darhol_otish = not s["guruhmi"]  # shaxsiy chatda javob bilan (pauzadan keyin) o'tiladi

    while s["keyingi_indeks"] < jami:
        if s.get("toxtatilgan"):
            return  # /stop orqali allaqachon tugatilgan — natija allaqachon chiqarilgan
        i = s["keyingi_indeks"]
        t_ = savollar[i]
        poll_id = await _poll_yubor(ctx, chat_id, t_, s["soniya"], i + 1, jami,
                                    s["variantlarni_aralashtir"], sessiya_id, til)
        s["keyingi_indeks"] += 1
        if not poll_id:
            continue
        javob_berildi = await _javobni_kut(ctx, poll_id, s["soniya"], darhol_otish)
        if s.get("toxtatilgan"):
            return  # /stop davomida kelgan bo'lishi mumkin
        if javob_berildi:
            s["ketma_ket_javobsiz"] = 0
        else:
            s["ketma_ket_javobsiz"] += 1
            if s["ketma_ket_javobsiz"] >= KETMA_KET_JAVOBSIZ_CHEGARA:
                await ctx.bot.send_message(
                    chat_id, t("javobsiz_toxtatildi", til, n=KETMA_KET_JAVOBSIZ_CHEGARA),
                    reply_markup=davom_klaviatura(sessiya_id, til))
                return

    ctx.bot_data.get("sessiyalar", {}).pop(sessiya_id, None)
    await _yakuniy_natija(ctx, chat_id, s, til)


async def _yakuniy_natija(ctx: ContextTypes.DEFAULT_TYPE, chat_id: int, s: dict, til: str):
    """Test tugagach (yoki to'xtatilgach) yakuniy natijani chiqaradi:
    to'g'ri/xato/tashlab ketilgan soni, sarflangan vaqt va reytingdagi o'rin
    (reyting bazada saqlanadi — bot qayta ishga tushirilsa ham saqlanib qoladi)."""
    jami = len(s["savollar"])
    tugri, notogri = s["tugri"], s["notogri"]
    otkazib = max(0, jami - tugri - notogri)
    vaqt = time.monotonic() - s["boshlangan_vaqt"]

    ma = await _viktorina_olish(ctx, s["quiz_id"])
    nomi = ma["nomi"] if ma else "Test"

    await db.reyting_yozish(s["quiz_id"], s["uid"], s["ism"], tugri, vaqt)
    orin, ishtirokchi = await db.reyting_orni(s["quiz_id"], s["uid"])

    matn = t("yakuniy_natija", til, nomi=_esc(nomi), ism=_esc(s["ism"]), jami=jami,
             javob_berilgan=tugri + notogri, tugri=tugri, notogri=notogri,
             otkazib=otkazib, vaqt=f"{vaqt:.1f}", orin=orin, ishtirokchi=ishtirokchi)

    username = (await ctx.bot.get_me()).username
    keyingi_quiz_id = ma.get("keyingi_quiz_id") if ma else None
    keyingi_nomi = None
    if keyingi_quiz_id:
        keyingi_ma = await _viktorina_olish(ctx, keyingi_quiz_id)
        keyingi_nomi = keyingi_ma["nomi"] if keyingi_ma else None
    await ctx.bot.send_message(
        chat_id, matn, parse_mode="HTML",
        reply_markup=yakuniy_klaviatura(s["quiz_id"], username, til, keyingi_quiz_id, keyingi_nomi))


async def _javobni_kut(ctx, poll_id, max_soniya, darhol_otish):
    """Shaxsiy chatda (darhol_otish=True): javob berilishi bilan — lekin
    to'g'ri/xato belgisini ko'rish uchun qisqa pauzadan keyin — qaytadi,
    aks holda vaqt tugashida. Guruhda (darhol_otish=False): har doim to'liq
    vaqtni kutadi (hamma ulgurishi uchun), keyin kimdir javob berganmi
    tekshiradi. Javob berilgan-berilmaganini (bool) qaytaradi."""
    hodisa = asyncio.Event()
    ctx.bot_data.setdefault("poll_kutish", {})[poll_id] = hodisa
    try:
        if darhol_otish:
            try:
                await asyncio.wait_for(hodisa.wait(), timeout=max_soniya)
                await asyncio.sleep(JAVOBDAN_KEYINGI_PAUZA)
                return True
            except asyncio.TimeoutError:
                return False
        else:
            await asyncio.sleep(max_soniya)
            return hodisa.is_set()
    finally:
        ctx.bot_data.get("poll_kutish", {}).pop(poll_id, None)


async def _poll_yubor(ctx, chat_id, t_, ochiq_soniya, orin, jami, variantlarni_aralashtir, sessiya_id, til):
    """Bitta testni Quiz poll qilib yuboradi ("[N/jami]" progress bilan).
    Muvaffaqiyatli bo'lsa poll_id, aks holda None qaytaradi."""
    savol = (t_.get("savol") or "").strip()
    variantlar = [str(v).strip() for v in t_.get("variantlar", []) if str(v).strip()]
    if len(variantlar) < 2:
        return None
    javob = t_.get("javob", 0)
    if not (0 <= javob < len(variantlar)):
        javob = 0

    idx = list(range(len(variantlar)))
    if variantlarni_aralashtir:
        random.shuffle(idx)
    yangi_var = [variantlar[j][:100] for j in idx][:10]      # poll: 10 tagacha, 100 belgi
    yangi_javob = idx.index(javob) if javob in idx else 0
    if yangi_javob >= len(yangi_var):
        yangi_javob = 0

    prefiks = f"[{orin}/{jami}] "
    # savol uzun bo'lsa (300+), alohida xabar qilamiz
    if len(prefiks) + len(savol) > 300:
        await ctx.bot.send_message(chat_id, f"❓ {prefiks}{savol}")
        poll_savol = t("yuqoridagi_savol", til)
    else:
        poll_savol = f"{prefiks}{savol}" if savol else prefiks.strip()

    izoh = t("ai_taxmin_izoh", til) if t_.get("taxmin") else None
    try:
        msg = await ctx.bot.send_poll(
            chat_id, question=poll_savol[:300], options=yangi_var,
            type=PollType.QUIZ, correct_option_id=yangi_javob,
            is_anonymous=False, explanation=izoh, open_period=ochiq_soniya)
        ctx.bot_data.setdefault("polls", {})[msg.poll.id] = yangi_javob
        ctx.bot_data.setdefault("poll_sessiya", {})[msg.poll.id] = sessiya_id
        return msg.poll.id
    except Exception:
        log.exception("poll xato")
        return None


async def poll_javob(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Foydalanuvchi javob berganda ballni (global va sessiya ichida)
    hisoblaymiz va navbatdagi savolni tezlashtirish uchun kutish
    hodisasini ishga tushiramiz."""
    ans = update.poll_answer
    tugri_idx = ctx.bot_data.get("polls", {}).get(ans.poll_id)
    if tugri_idx is not None and ans.option_ids:
        togri_javobmi = ans.option_ids[0] == tugri_idx

        uid = ans.user.id
        ballar = ctx.bot_data.setdefault("ballar", {})
        b = ballar.setdefault(uid, {"tugri": 0, "jami": 0})
        b["jami"] += 1
        if togri_javobmi:
            b["tugri"] += 1

        sessiya_id = ctx.bot_data.get("poll_sessiya", {}).get(ans.poll_id)
        s = ctx.bot_data.get("sessiyalar", {}).get(sessiya_id) if sessiya_id else None
        if s is not None:
            if togri_javobmi:
                s["tugri"] += 1
            else:
                s["notogri"] += 1

    hodisa = ctx.bot_data.get("poll_kutish", {}).get(ans.poll_id)
    if hodisa:
        hodisa.set()


async def natija(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    til = await _til(ctx, uid)
    b = ctx.bot_data.get("ballar", {}).get(uid)
    if not b or b["jami"] == 0:
        await update.message.reply_text(t("hali_yechmagan", til))
        return
    foiz = round(b["tugri"] / b["jami"] * 100)
    await update.message.reply_text(t("natija_matni", til, tugri=b["tugri"], jami=b["jami"], foiz=foiz))
