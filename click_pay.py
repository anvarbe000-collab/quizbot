"""
click_pay.py — Click (click.uz) to'lov integratsiyasi: Merchant Shop-API
(Prepare/Complete webhook) orqali avtomatik to'lovni qabul qiladi.

Oqim:
  1) invoice_url() — talabaga yuboriladigan "to'lovga o'tish" havolasi.
  2) Click foydalanuvchini o'z sahifasiga olib boradi, u yerda to'laydi.
  3) Click bizning webhook manzilimizga ketma-ket 2 ta so'rov yuboradi:
     - action=0 (Prepare) — tranzaksiya haqiqiyligini so'raydi
     - action=1 (Complete) — pul haqiqatan tushganini xabar qiladi
  4) Har ikkalasi ham MD5 imzo (sign_string) orqali tekshiriladi — soxta
     so'rovlarning oldini olish uchun MUHIM xavfsizlik qatlami.

Click rasmiy hujjatlashtirilgan xato kodlari ishlatiladi (error maydoni):
   0  = muvaffaqiyatli
  -1  = SIGN CHECK FAILED (imzo noto'g'ri)
  -2  = noto'g'ri summa
  -3  = action topilmadi
  -4  = allaqachon to'langan
  -5  = foydalanuvchi/tranzaksiya topilmadi (bizda: to'lov yozuvi yo'q)
  -6  = tranzaksiya topilmadi (Complete'da Prepare qilinmagan bo'lsa)
  -9  = tranzaksiya bekor qilingan
"""
import hashlib
import logging
from urllib.parse import urlencode

import config
import db

log = logging.getLogger(__name__)

CLICK_INVOICE_ASOSIY = "https://my.click.uz/services/pay"

XATO = {
    "MUVAFFAQIYATLI": 0,
    "IMZO_XATO": -1,
    "SUMMA_XATO": -2,
    "ACTION_XATO": -3,
    "ALLAQACHON_TOLANGAN": -4,
    "TOLOV_TOPILMADI": -5,
    "TRANZAKSIYA_TOPILMADI": -6,
    "BEKOR_QILINGAN": -9,
}


def invoice_url(tolov_id: str, summa) -> str:
    """Talabaga yuboriladigan Click to'lov havolasini quradi."""
    params = {
        "service_id": config.CLICK_SERVICE_ID,
        "merchant_id": config.CLICK_MERCHANT_ID,
        "amount": summa,
        "transaction_param": tolov_id,   # bizning tolov_id — Click buni merchant_trans_id sifatida qaytaradi
    }
    if config.CLICK_RETURN_URL:
        params["return_url"] = config.CLICK_RETURN_URL
    return f"{CLICK_INVOICE_ASOSIY}?{urlencode(params)}"


def _md5(matn: str) -> str:
    return hashlib.md5(matn.encode("utf-8")).hexdigest()


def _prepare_imzo(m: dict) -> str:
    xom = (f"{m['click_trans_id']}{m['service_id']}{config.CLICK_SECRET_KEY}"
           f"{m['merchant_trans_id']}{m['amount']}{m['action']}{m['sign_time']}")
    return _md5(xom)


def _complete_imzo(m: dict) -> str:
    xom = (f"{m['click_trans_id']}{m['service_id']}{config.CLICK_SECRET_KEY}"
           f"{m['merchant_trans_id']}{m.get('merchant_prepare_id', '')}"
           f"{m['amount']}{m['action']}{m['sign_time']}")
    return _md5(xom)


def _asosiy_javob(m: dict, error: int, error_note: str, qoshimcha: dict = None) -> dict:
    javob = {
        "click_trans_id": m.get("click_trans_id"),
        "merchant_trans_id": m.get("merchant_trans_id"),
        "error": error,
        "error_note": error_note,
    }
    if qoshimcha:
        javob.update(qoshimcha)
    return javob


async def prepare(m: dict) -> dict:
    """Click'ning 'Prepare' (action=0) so'rovini qayta ishlaydi."""
    if _prepare_imzo(m) != m.get("sign_string"):
        log.warning("Click Prepare: imzo mos kelmadi (tolov_id=%s)", m.get("merchant_trans_id"))
        return _asosiy_javob(m, XATO["IMZO_XATO"], "SIGN CHECK FAILED")

    tolov_id = m.get("merchant_trans_id")
    tolov = await db.tolov_olish(tolov_id)
    if not tolov:
        return _asosiy_javob(m, XATO["TOLOV_TOPILMADI"], "Order not found")

    try:
        summa_kelgan = float(m.get("amount", 0))
    except (TypeError, ValueError):
        return _asosiy_javob(m, XATO["SUMMA_XATO"], "Invalid amount")
    if abs(summa_kelgan - float(tolov["narxi"])) > 1:  # 1 so'mgacha yaxlitlash xatosiga tolerant
        return _asosiy_javob(m, XATO["SUMMA_XATO"], "Incorrect amount")

    if tolov["holat"] == "tasdiqlangan":
        return _asosiy_javob(m, XATO["ALLAQACHON_TOLANGAN"], "Already paid")

    await db.tolov_click_prepare_yozish(tolov_id, m["click_trans_id"])
    return _asosiy_javob(m, XATO["MUVAFFAQIYATLI"], "Success",
                         {"merchant_prepare_id": tolov_id})


async def complete(m: dict, tolov_muvaffaqiyatli_callback=None) -> dict:
    """Click'ning 'Complete' (action=1) so'rovini qayta ishlaydi. Pul
    haqiqatan tushganini shu bosqich tasdiqlaydi. Muvaffaqiyatli bo'lsa,
    berilgan callback (agar bo'lsa) chaqiriladi — botga xabar berish uchun."""
    if _complete_imzo(m) != m.get("sign_string"):
        log.warning("Click Complete: imzo mos kelmadi (tolov_id=%s)", m.get("merchant_trans_id"))
        return _asosiy_javob(m, XATO["IMZO_XATO"], "SIGN CHECK FAILED")

    tolov_id = m.get("merchant_trans_id")
    tolov = await db.tolov_olish(tolov_id)
    if not tolov:
        return _asosiy_javob(m, XATO["TOLOV_TOPILMADI"], "Order not found")
    if tolov.get("click_trans_id") != m.get("click_trans_id"):
        return _asosiy_javob(m, XATO["TRANZAKSIYA_TOPILMADI"], "Transaction not prepared")

    error = int(m.get("error", 0))
    if error < 0:
        await db.tolov_holatini_yangilash(tolov_id, "bekor_qilingan")
        return _asosiy_javob(m, XATO["BEKOR_QILINGAN"], "Transaction cancelled",
                             {"merchant_confirm_id": tolov_id})

    if tolov["holat"] == "tasdiqlangan":
        return _asosiy_javob(m, XATO["ALLAQACHON_TOLANGAN"], "Already paid",
                             {"merchant_confirm_id": tolov_id})

    await db.tolov_holatini_yangilash(tolov_id, "tasdiqlangan")
    log.info("Click to'lov tasdiqlandi: tolov_id=%s", tolov_id)
    if tolov_muvaffaqiyatli_callback:
        await tolov_muvaffaqiyatli_callback(tolov_id)

    return _asosiy_javob(m, XATO["MUVAFFAQIYATLI"], "Success",
                         {"merchant_confirm_id": tolov_id})
