"""
main.py — Test bot ishga tushirish.
"""
import logging
from telegram import BotCommand
from telegram.ext import (Application, CommandHandler, MessageHandler,
                          CallbackQueryHandler, PollAnswerHandler, filters)

import config
from bot.matnlar import t as _t
from bot.handlers import (start, newquiz_tugma_bosildi, yordam, newquiz, lang_komandasi,
                          til_tanlandi, testlarim, stop_komandasi, fayl_qabul, chek_qabul,
                          tolov_tasdiqlandi, tolov_radetildi, nechta_tanlandi, tartib_tanlandi,
                          soniya_tanlandi, tayyor_bosildi, davom_bosildi,
                          tugat_bosildi, poll_javob, natija)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

_BUYRUQLAR = {
    "uz": [
        ("start", "Botni boshlash"),
        ("newquiz", "Fayldan yangi test yaratish"),
        ("help", "Yordam"),
        ("testlarim", "Yaratgan testlaringiz"),
        ("stop", "Joriy testni to'xtatish"),
        ("natija", "Oxirgi natijangiz"),
        ("lang", "Tilni o'zgartirish"),
    ],
    "ru": [
        ("start", "Начать"),
        ("newquiz", "Создать тест из файла"),
        ("help", "Помощь"),
        ("testlarim", "Ваши тесты"),
        ("stop", "Остановить текущий тест"),
        ("natija", "Ваш последний результат"),
        ("lang", "Сменить язык"),
    ],
    "en": [
        ("start", "Start the bot"),
        ("newquiz", "Create a quiz from a file"),
        ("help", "Help"),
        ("testlarim", "Your tests"),
        ("stop", "Stop the current test"),
        ("natija", "Your last result"),
        ("lang", "Change language"),
    ],
}


async def _botni_sozlash(app: Application):
    """Har til uchun "/" buyruqlar menyusini VA botning START bosishdan
    OLDIN ko'rinadigan tavsifini o'rnatadi (@QuizBot'dagi "What can this
    bot do?" kartochkasi kabi) — Telegram mijoz tiliga qarab mosini ko'rsatadi."""
    for til, royxat in _BUYRUQLAR.items():
        buyruqlar = [BotCommand(nom, tavsif) for nom, tavsif in royxat]
        await app.bot.set_my_commands(buyruqlar, language_code=til)
        await app.bot.set_my_description(_t("bot_tavsifi", til), language_code=til)
        await app.bot.set_my_short_description(_t("bot_qisqa_tavsifi", til), language_code=til)
    await app.bot.set_my_commands([BotCommand(nom, tavsif) for nom, tavsif in _BUYRUQLAR["uz"]])
    await app.bot.set_my_description(_t("bot_tavsifi", "uz"))
    await app.bot.set_my_short_description(_t("bot_qisqa_tavsifi", "uz"))


def main():
    config.tekshir()
    if not config.TOLOV_YOQILGAN:
        print("ℹ️ To'lov sozlanmagan (ADMIN_CHAT_ID/TOLOV_KARTA bo'sh) — xizmat bepul ishlaydi.")
    # concurrent_updates=True SHART: aks holda PTB yangilanishlarni birma-bir
    # qayta ishlaydi — test davomida (poll vaqtini kutayotganda) botning
    # o'zi band bo'lib qoladi va foydalanuvchining javobi (poll_answer)
    # test tugagunicha ishlanmay navbatda turib qoladi (shuning uchun
    # "javob berdim, lekin keyingi savolga o'tmayapti" muammosi bo'lgan).
    app = (Application.builder().token(config.BOT_TOKEN)
           .concurrent_updates(True).post_init(_botni_sozlash).build())
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("newquiz", newquiz))
    app.add_handler(CallbackQueryHandler(newquiz_tugma_bosildi, pattern=r"^newquiz_tugma$"))
    app.add_handler(CommandHandler("help", yordam))
    app.add_handler(CommandHandler("lang", lang_komandasi))
    app.add_handler(CommandHandler("testlarim", testlarim))
    app.add_handler(CommandHandler("stop", stop_komandasi))
    app.add_handler(CommandHandler("natija", natija))
    app.add_handler(CallbackQueryHandler(til_tanlandi, pattern=r"^til:"))
    app.add_handler(CallbackQueryHandler(nechta_tanlandi, pattern=r"^nechta:"))
    app.add_handler(CallbackQueryHandler(tartib_tanlandi, pattern=r"^tartib:"))
    app.add_handler(CallbackQueryHandler(soniya_tanlandi, pattern=r"^soniya:"))
    app.add_handler(CallbackQueryHandler(tayyor_bosildi, pattern=r"^tayyor:"))
    app.add_handler(CallbackQueryHandler(davom_bosildi, pattern=r"^davom:"))
    app.add_handler(CallbackQueryHandler(tugat_bosildi, pattern=r"^tugat:"))
    app.add_handler(CallbackQueryHandler(tolov_tasdiqlandi, pattern=r"^tolovtasdiq:"))
    app.add_handler(CallbackQueryHandler(tolov_radetildi, pattern=r"^tolovrad:"))
    app.add_handler(MessageHandler(filters.Document.ALL, fayl_qabul))
    app.add_handler(MessageHandler(filters.PHOTO, chek_qabul))
    app.add_handler(PollAnswerHandler(poll_javob))
    print("✅ Test bot ishga tushdi. To'xtatish: Ctrl+C")
    app.run_polling()


if __name__ == "__main__":
    main()
