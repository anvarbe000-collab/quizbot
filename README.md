# Test Bot — fayldan avtomatik Telegram Quiz yasovchi

O'qituvchi bergan Word/PDF test faylini avtomatik Telegram testiga (Quiz)
aylantiradi, xohlagan o'lchamdagi mustaqil to'plamlarga bo'ladi va
@QuizBot uslubida o'ynatadi (sanoq bilan boshlash, vaqt chegarasi, reyting,
ulashish havolasi). Ixtiyoriy ravishda qo'lda tasdiqlanadigan to'lov bilan.

## Oqim
Fayl (.docx/.pdf) yuboriladi -> (to'lov yoqilgan bo'lsa: karta ko'rsatiladi,
chek/skrinshot kutiladi, admin tasdiqlaydi) -> matn olinadi -> testlar
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

## To'lov (ixtiyoriy, qo'lda tasdiqlash)
`.env`da `ADMIN_CHAT_ID` va `TOLOV_KARTA` ikkalasi ham to'ldirilsa yoqiladi
(bo'lmasa xizmat bepul ishlayveradi). `TOLOV_KARTA_EGASI` ixtiyoriy (karta
egasining F.I.Sh.) — to'ldirilsa, to'lov xabarida karta raqami ostida
alohida ko'rsatiladi. Yoqilganda: talaba fayl yuborsa, bot karta raqami
(bosib nusxa olinadigan) va narxni professional ko'rinishda ko'rsatib
chek/skrinshot so'raydi; talaba yuborgan skrinshot ADMIN_CHAT_ID'ga
(rasm + "✅ Tasdiqlash"/"❌ Rad etish" tugmalari bilan) boradi; admin
tasdiqlasa — fayl avtomatik ishlanadi va talabaga xabar boradi; rad etsa —
talaba qayta tekshirishga yo'naltiriladi. Admin (ADMIN_CHAT_ID) o'zi fayl
yuborganda to'lov so'ralmaydi. ADMIN_CHAT_ID'ni olish uchun: @userinfobot
ga /start yuboring.

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
- `bot/matnlar.py` — barcha matnlar 3 tilda (uz/ru/en)
- `bot/` — fayl qabul, to'lov, to'plam/tartib/vaqt tanlash, poll yuborish, natija
- `main.py` — ishga tushirish, "/" buyruqlar menyusi

## O'rnatish
1) python -m venv venv && (venv faollashtiring)
2) pip install -r requirements.txt
3) .env: TEST_BOT_TOKEN (BotFather), AI_API_KEY (Gemini)
4) (ixtiyoriy) .env: ADMIN_CHAT_ID, TOLOV_KARTA, TOLOV_KARTA_EGASI, TOLOV_NARXI — to'lovni yoqish uchun
5) python main.py

Birinchi ishga tushirishda loyiha papkasida `bot.db` (SQLite) avtomatik
yaratiladi — bu faylni o'chirmang, aks holda barcha testlar/reyting/
to'lovlar tarixi yo'qoladi.

## Buyruqlar
/start — boshlash | /newquiz — fayldan yangi test yaratish | /help — yordam |
/testlarim — yaratgan testlaringiz | /stop — joriy testni to'xtatish |
/natija — oxirgi natijangiz | /lang — tilni o'zgartirish (o'zbek/rus/ingliz)
