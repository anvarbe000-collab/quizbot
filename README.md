# Test Bot — fayldan avtomatik Telegram Quiz yasovchi

O'qituvchi bergan Word/PDF test faylini avtomatik Telegram testiga (Quiz)
aylantiradi, xohlagan o'lchamdagi mustaqil to'plamlarga bo'ladi va
@QuizBot uslubida o'ynatadi (sanoq bilan boshlash, vaqt chegarasi, reyting,
ulashish havolasi). Ixtiyoriy ravishda Click (click.uz) orqali AVTOMATIK
to'lov bilan — admin aralashuvisiz.

## Oqim
Fayl (.docx/.pdf) yuboriladi -> (to'lov yoqilgan bo'lsa: Click to'lov
havolasi beriladi, talaba to'laydi, Click webhook orqali AVTOMATIK
tasdiqlaydi) -> matn olinadi -> testlar
ajratiladi (avval AI'siz shablon orqali — raqamli, jadvalli, a/b/c/d,
bo'sh qator bilan ajratilgan formatlar, jadval katagi ichidagi savollar;
javob rangli belgi/`*`/✓/"Javob: B"/hujjat oxiridagi umumiy javob kaliti
orqali topiladi; faqat chindan noaniq holatlarda AI ishlatiladi) ->
"nechtadan bo'laklarga bo'lay?" -> har bo'lak uchun ALOHIDA test
yaratiladi -> savollar tartibi (asl/aralash) -> soniya -> har bo'lak
uchun "Tayyorman / Ulashish / Guruhda boshlash" kartochkasi -> 3,2,1,GO!
sanog'i -> Telegram Quiz poll -> yakuniy natija (to'g'ri/xato/tashlab
ketilgan, vaqt, reyting).

## Muhim (halol)
- Javob faylda bo'lmasa, AI o'zi javob beradi — ba'zan XATO bo'lishi mumkin.
  Bunday testlarga "⚠️ tekshiring" belgisi qo'yiladi.
- Telegram Quiz cheklovi: savol 300 belgi, variant 100 belgi, 10 tagacha variant.
  Uzun savol alohida xabar bilan yuboriladi.
- Shaxsiy chatda javob berilgach qisqa pauzadan keyin keyingi savolga
  o'tiladi (to'g'ri/xato belgisini ko'rish uchun); guruhda har doim
  to'liq vaqt kutiladi (hamma ulgurishi uchun).
- Ketma-ket 3 ta savolga javob kelmasa test avtomatik to'xtaydi.

## To'lov (ixtiyoriy, Click orqali AVTOMATIK)
`.env`da `CLICK_SERVICE_ID`, `CLICK_SECRET_KEY`, `CLICK_MERCHANT_ID` va
`TOLOV_NARXI` to'liq bo'lsa yoqiladi (bo'lmasa xizmat bepul ishlayveradi).
Yoqilganda: talaba fayl yuborsa, bot Click to'lov sahifasiga o'tuvchi
tugma beradi; talaba shu yerda to'laydi; Click to'lov haqiqiyligini
tasdiqlash uchun bizning webhook manzilimizga (`CLICK_WEBHOOK_HOST:
CLICK_WEBHOOK_PORT/click/webhook`) 2 ta so'rov yuboradi (Prepare, so'ng
Complete) — bular MD5 imzo bilan tekshiriladi. Complete muvaffaqiyatli
bo'lishi bilan fayl AVTOMATIK ishlanadi va talabaga xabar boradi — admin
hech qanday tugma bosishi shart emas. Admin (ADMIN_CHAT_ID) o'zi fayl
yuborganda to'lov so'ralmaydi; ADMIN_CHAT_ID berilsa, har muvaffaqiyatli
to'lov haqida adminga ham xabar boradi (ixtiyoriy, faqat bildirishnoma
uchun). ADMIN_CHAT_ID'ni olish uchun: @userinfobot ga /start yuboring.

**MUHIM — tarmoq talabi:** Click serverlari `CLICK_WEBHOOK_HOST:
CLICK_WEBHOOK_PORT` manziliga INTERNET orqali ulana olishi kerak. Bu
kompyuter (Windows PC) uchun bu portni tashqariga chiqarish (router'da
port forwarding, statik/oq IP, yoki test uchun ngrok kabi tunnel vositasi)
zarur — aks holda Click to'lovni "Prepare/Complete" qilib bo'lmaydi va
xizmat avtomatik ochilmaydi. Ishlab chiqarishda buni doimiy ishlaydigan
serverga (VPS) joylashtirish tavsiya etiladi.

## Botning START oldidan ko'rinishi
Bot birinchi ishga tushganda (`post_init`) o'zining tavsifini (START
bosishdan oldin ko'rinadigan katta matn — @QuizBot'dagi "What can this
bot do?" kartochkasi kabi) va qisqa tavsifini (profilda ko'rinadigan)
avtomatik o'rnatadi — buni BotFather orqali qo'lda sozlash shart emas.
Matnlar `bot/matnlar.py`dagi `bot_tavsifi`/`bot_qisqa_tavsifi` kalitlarida,
3 tilda. `/start` bosilganda esa asosiy "📎 Fayldan test yaratish" tugmasi
chiqadi (to'lov yoqilgan bo'lsa — narxi bilan birga).

## Tuzilma
- `fayl/oqi.py` — Word/PDF -> matn (jadval, rang-belgi, bo'sh qator ichida)
- `ai/shablon.py` — AI'siz, kod asosida savol/javob ajratish
- `ai/parse.py` — shablon + (kerak bo'lsagina) AI orqali ajratish
- `db.py` — SQLite: viktorinalar, reyting, foydalanuvchi tili, to'lovlar
  (bot qayta ishga tushirilsa ham saqlanib qoladi — `bot.db` fayli)
- `click_pay.py` — Click (click.uz) Merchant Shop-API: invoice havolasi +
  Prepare/Complete webhook'larini MD5 imzo bilan tekshirish
- `bot/matnlar.py` — barcha matnlar 3 tilda (uz/ru/en)
- `bot/` — fayl qabul, to'lov, to'plam/tartib/vaqt tanlash, poll yuborish, natija
- `main.py` — ishga tushirish: PTB polling + Click webhook uchun aiohttp
  serveri BIR XIL event loop'da birga ishga tushadi

## O'rnatish
1) python -m venv venv && (venv faollashtiring)
2) pip install -r requirements.txt
3) .env: TEST_BOT_TOKEN (BotFather), AI_API_KEY (Gemini)
4) (ixtiyoriy) .env: CLICK_SERVICE_ID, CLICK_SECRET_KEY, CLICK_MERCHANT_ID,
   TOLOV_NARXI, ADMIN_CHAT_ID, CLICK_WEBHOOK_HOST/PORT — to'lovni yoqish uchun
5) python main.py

Birinchi ishga tushirishda loyiha papkasida `bot.db` (SQLite) avtomatik
yaratiladi — bu faylni o'chirmang, aks holda barcha testlar/reyting/
to'lovlar tarixi yo'qoladi.

## Buyruqlar
/start — boshlash | /newquiz — fayldan yangi test yaratish | /help — yordam |
/testlarim — yaratgan testlaringiz | /stop — joriy testni to'xtatish |
/natija — oxirgi natijangiz | /lang — tilni o'zgartirish (o'zbek/rus/ingliz)
