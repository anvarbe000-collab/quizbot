import os
from dotenv import load_dotenv
load_dotenv()
BOT_TOKEN = os.getenv("TEST_BOT_TOKEN", "")
AI_BASE_URL = os.getenv("AI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "gemini-flash-lite-latest")

# To'lov — endi Click orqali AVTOMATIK (admin qo'lda tasdiqlamaydi).
# Talaba tugmani bosadi -> Click sahifasida to'laydi -> Click bizning
# webhook'imizga xabar beradi -> xizmat avtomatik ochiladi.
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID") or 0)  # (ixtiyoriy) to'lov haqida bildirishnoma uchun
TOLOV_NARXI = int(os.getenv("TOLOV_NARXI") or 0)      # so'mda, butun son (Click UZS'ni tiyinsiz oladi)

CLICK_SERVICE_ID = os.getenv("CLICK_SERVICE_ID", "")
CLICK_SECRET_KEY = os.getenv("CLICK_SECRET_KEY", "")
CLICK_MERCHANT_ID = os.getenv("CLICK_MERCHANT_ID", "")
CLICK_MERCHANT_USER_ID = os.getenv("CLICK_MERCHANT_USER_ID", "")
CLICK_RETURN_URL = os.getenv("CLICK_RETURN_URL", "")
CLICK_WEBHOOK_HOST = os.getenv("CLICK_WEBHOOK_HOST", "0.0.0.0")
CLICK_WEBHOOK_PORT = int(os.getenv("CLICK_WEBHOOK_PORT") or 8080)

_CLICK_SOZLANGAN = bool(CLICK_SERVICE_ID and CLICK_SECRET_KEY and CLICK_MERCHANT_ID and TOLOV_NARXI)
# .env'da aniq TOLOV_YOQILGAN=true/false bo'lsa o'shani hurmat qilamiz,
# bo'lmasa Click ma'lumotlari to'liqligiga qarab o'zi aniqlaydi.
_tolov_yoqilgan_env = os.getenv("TOLOV_YOQILGAN")
if _tolov_yoqilgan_env is not None:
    TOLOV_YOQILGAN = _tolov_yoqilgan_env.strip().lower() in ("1", "true", "yes", "ha")
else:
    TOLOV_YOQILGAN = _CLICK_SOZLANGAN


def tekshir():
    if not BOT_TOKEN or BOT_TOKEN == "bu_yerga_token":
        raise RuntimeError("TEST_BOT_TOKEN topilmadi. .env faylini to'ldiring.")
    if TOLOV_YOQILGAN and not _CLICK_SOZLANGAN:
        raise RuntimeError(
            "TOLOV_YOQILGAN=true, lekin CLICK_SERVICE_ID/CLICK_SECRET_KEY/"
            "CLICK_MERCHANT_ID/TOLOV_NARXI to'liq emas. .env faylini tekshiring.")
