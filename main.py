"""
main.py — Test bot ishga tushirish.
"""
import asyncio
import logging
import os
from telegram import BotCommand
from telegram.ext import (Application, CommandHandler, MessageHandler,
                          CallbackQueryHandler, PollAnswerHandler, filters)

import click_pay
import config
from bot.matnlar import t as _t
from bot.handlers import (start, newquiz_tugma_bosildi, yordam, newquiz, lang_komandasi,
                          til_tanlandi, testlarim, stop_komandasi, fayl_qabul,
                          click_tolov_muvaffaqiyatli, nechta_tanlandi, tartib_tanlandi,
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
        print("ℹ️ To'lov sozlanmagan (Click ma'lumotlari to'liq emas) — xizmat bepul ishlaydi.")
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
    app.add_handler(MessageHandler(filters.Document.ALL, fayl_qabul))
    app.add_handler(PollAnswerHandler(poll_javob))
    return app


async def _click_webhook_ishga_tushir(app: Application):
    """Click "Prepare"/"Complete" so'rovlarini qabul qiluvchi aiohttp
    serverini PTB bilan BIR XIL asyncio event loop'da, alohida portda
    ko'taradi. Click bu manzilga action=0 (Prepare) va action=1 (Complete)
    so'rovlarini form-encoded POST sifatida yuboradi."""
    from aiohttp import web

    async def _handler(request: web.Request):
        m = dict(await request.post())
        action = m.get("action")
        if action == "0":
            javob = await click_pay.prepare(m)
        elif action == "1":
            javob = await click_pay.complete(
                m, tolov_muvaffaqiyatli_callback=lambda tolov_id: click_tolov_muvaffaqiyatli(app, tolov_id))
        else:
            javob = {"error": -3, "error_note": "Action not found"}
        return web.json_response(javob)

    # Railway (va shunga o'xshash hosting'lar) konteynerga o'zining ochiq
    # portini $PORT muhit o'zgaruvchisi orqali beradi va ommaviy domenni
    # aynan o'sha portga yo'naltiradi — shuning uchun CLICK_WEBHOOK_PORT
    # o'rniga (agar mavjud bo'lsa) $PORT'ni ishlatishimiz SHART, aks holda
    # Click webhook tashqi domendan konteynerga umuman yetib bormaydi.
    port = int(os.getenv("PORT") or config.CLICK_WEBHOOK_PORT)
    aiohttp_app = web.Application()
    aiohttp_app.router.add_post("/click/webhook", _handler)
    runner = web.AppRunner(aiohttp_app)
    await runner.setup()
    site = web.TCPSite(runner, config.CLICK_WEBHOOK_HOST, port)
    await site.start()
    print(f"✅ Click webhook: http://{config.CLICK_WEBHOOK_HOST}:{port}/click/webhook")


async def _asosiy():
    app = main()
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    if config.TOLOV_YOQILGAN:
        await _click_webhook_ishga_tushir(app)
    print("✅ Test bot ishga tushdi. To'xtatish: Ctrl+C")
    try:
        await asyncio.Event().wait()
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(_asosiy())
