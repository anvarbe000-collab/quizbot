import os
from dotenv import load_dotenv
load_dotenv()
BOT_TOKEN = os.getenv("TEST_BOT_TOKEN", "")
AI_BASE_URL = os.getenv("AI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "gemini-flash-lite-latest")

# To'lov (qo'lda tasdiqlash) sozlamalari — fayldan test yasash xizmati uchun.
# ADMIN_CHAT_ID yoki TOLOV_KARTA bo'sh bo'lsa, to'lov talab qilinmaydi
# (xizmat bepul ishlaydi) — bu sozlanmagan holatda botni buzmasligi uchun.
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID") or 0)
TOLOV_KARTA = os.getenv("TOLOV_KARTA", "")          # faqat karta raqami, masalan "8600 1234 5678 9012"
TOLOV_KARTA_EGASI = os.getenv("TOLOV_KARTA_EGASI", "")  # ixtiyoriy, masalan "IBROHIMOV J."
TOLOV_NARXI = os.getenv("TOLOV_NARXI", "")
TOLOV_YOQILGAN = bool(ADMIN_CHAT_ID and TOLOV_KARTA)

def tekshir():
    if not BOT_TOKEN or BOT_TOKEN == "bu_yerga_token":
        raise RuntimeError("TEST_BOT_TOKEN topilmadi. .env faylini to'ldiring.")
