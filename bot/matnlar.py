"""
bot/matnlar.py — botning barcha matnlari, 3 tilda (o'zbek/rus/ingliz).
Ishlatish: t("kalit", til, param1=..., param2=...)
"""

TILLAR = {"uz": "🇺🇿 O'zbekcha", "ru": "🇷🇺 Русский", "en": "🇬🇧 English"}
STANDART_TIL = "uz"

_M = {
    "salom": {
        "uz": "👋 <b>Xush kelibsiz!</b>\n\n"
              "📚 Word yoki PDF test faylingizni bir necha soniyada professional "
              "Telegram Quiz'ga aylantiraman.\n\n"
              "✨ <b>Nega aynan shu bot:</b>\n"
              "• Savol va javoblarni aniq, avtomatik ajratadi\n"
              "• Fayl xohlagan o'lchamdagi mustaqil bo'laklarga bo'linadi\n"
              "• Vaqt chegarasi, aralashtirish, reyting va ulashish havolasi\n"
              "• Yakka yoki guruhda o'ynash mumkin\n"
              "• O'zbek, rus, ingliz — 3 tilda ishlaydi\n"
              "{narx_qatori}\n"
              "💡 Tayyor testni yechish uchun kelgan bo'lsangiz — sizga yuborilgan "
              "havolani bosing.\n"
              "🆕 Yangi test yaratmoqchi bo'lsangiz — pastdagi tugmani bosing yoki "
              "faylni to'g'ridan-to'g'ri yuboring 👇",
        "ru": "👋 <b>Добро пожаловать!</b>\n\n"
              "📚 Превращу ваш файл теста Word или PDF в профессиональный "
              "Telegram Quiz за несколько секунд.\n\n"
              "✨ <b>Почему именно этот бот:</b>\n"
              "• Точно и автоматически извлекает вопросы и ответы\n"
              "• Файл делится на независимые части любого размера\n"
              "• Таймер, перемешивание, рейтинг и ссылка для отправки\n"
              "• Можно проходить в одиночку или в группе\n"
              "• Работает на узбекском, русском и английском\n"
              "{narx_qatori}\n"
              "💡 Если вы пришли пройти готовый тест — нажмите присланную вам ссылку.\n"
              "🆕 Хотите создать новый тест — нажмите кнопку ниже или сразу "
              "отправьте файл 👇",
        "en": "👋 <b>Welcome!</b>\n\n"
              "📚 I'll turn your Word or PDF test file into a professional "
              "Telegram Quiz in seconds.\n\n"
              "✨ <b>Why this bot:</b>\n"
              "• Accurately auto-extracts questions and answers\n"
              "• Splits the file into independent parts of any size\n"
              "• Timer, shuffling, leaderboard, and a shareable link\n"
              "• Play solo or in a group\n"
              "• Works in Uzbek, Russian and English\n"
              "{narx_qatori}\n"
              "💡 If you came to take a ready-made quiz — tap the link that was sent to you.\n"
              "🆕 Want to create a new quiz — press the button below or just "
              "send the file directly 👇",
    },
    "salom_narx_qatori": {
        "uz": "\n💳 <b>Narxi:</b> {narx} (bitta fayl uchun)\n",
        "ru": "\n💳 <b>Цена:</b> {narx} (за один файл)\n",
        "en": "\n💳 <b>Price:</b> {narx} (per file)\n",
    },
    # --- Bot tavsifi (START bosishdan OLDIN ko'rinadi — setMyDescription) ---
    "bot_tavsifi": {
        "uz": "📚 Bu bot o'qituvchi tayyorlagan Word yoki PDF test faylini "
              "avtomatik ravishda professional Telegram testiga (Quiz) aylantiradi.\n\n"
              "✨ Nima qila oladi:\n"
              "• Fayldan savol va javoblarni avtomatik, aniq ajratadi\n"
              "• Testni istalgan o'lchamdagi mustaqil bo'laklarga bo'ladi\n"
              "• Vaqt chegarasi, savol/javob aralashtirish, reyting — hammasi bor\n"
              "• Yakka yoki guruhda o'ynash mumkin\n"
              "• O'zbek, rus va ingliz tillarida ishlaydi\n\n"
              "Agar sizga test havolasi yuborilgan bo'lsa — pastdagi START tugmasini bosing.",
        "ru": "📚 Этот бот автоматически превращает файл теста (Word или PDF) "
              "от преподавателя в профессиональный Telegram-тест (Quiz).\n\n"
              "✨ Что умеет:\n"
              "• Точно и автоматически извлекает вопросы и ответы из файла\n"
              "• Делит тест на независимые части любого размера\n"
              "• Таймер, перемешивание вопросов/ответов, рейтинг — всё есть\n"
              "• Можно проходить в одиночку или в группе\n"
              "• Работает на узбекском, русском и английском\n\n"
              "Если вам прислали ссылку на тест — нажмите кнопку START внизу.",
        "en": "📚 This bot automatically turns a teacher's Word or PDF test "
              "file into a professional Telegram Quiz.\n\n"
              "✨ What it can do:\n"
              "• Accurately auto-extracts questions and answers from the file\n"
              "• Splits the test into independent parts of any size\n"
              "• Timer, question/answer shuffling, leaderboard — all included\n"
              "• Play solo or in a group\n"
              "• Works in Uzbek, Russian and English\n\n"
              "If someone sent you a quiz link, tap START below to begin.",
    },
    "bot_qisqa_tavsifi": {
        "uz": "📚 Word/PDF test faylini professional Telegram Quiz'ga aylantiruvchi bot",
        "ru": "📚 Бот, превращающий файл теста Word/PDF в профессиональный Telegram Quiz",
        "en": "📚 Bot that turns your Word/PDF test file into a professional Telegram Quiz",
    },
    "yordam": {
        "uz": ("📖 <b>Bot qanday ishlaydi</b>\n\n"
               "1. /newquiz — yangi test yaratish (yoki to'g'ridan-to'g'ri fayl yuboring)\n"
               "2. Word (.docx) yoki PDF test faylini yuboring\n"
               "3. Nechtadan bo'laklarga bo'lishni tanlang\n"
               "4. Savollar tartibini tanlang\n"
               "5. Har savolga necha soniya berilishini tanlang\n"
               "6. Har bo'lak uchun chiqqan \"Tayyorman!\" tugmasini bosing\n\n"
               "<b>Buyruqlar:</b>\n"
               "/start — botni boshlash\n"
               "/newquiz — fayldan yangi test yaratish\n"
               "/help — shu yordam\n"
               "/testlarim — yaratgan testlaringiz ro'yxati\n"
               "/stop — joriy testni to'xtatish\n"
               "/natija — oxirgi natijangiz\n"
               "/lang — tilni o'zgartirish"),
        "ru": ("📖 <b>Как работает бот</b>\n\n"
               "1. /newquiz — создать новый тест (или сразу отправьте файл)\n"
               "2. Отправьте файл теста Word (.docx) или PDF\n"
               "3. Выберите, на сколько частей разбить\n"
               "4. Выберите порядок вопросов\n"
               "5. Выберите, сколько секунд на вопрос\n"
               "6. Нажмите \"Готов!\" под нужной частью\n\n"
               "<b>Команды:</b>\n"
               "/start — начать\n"
               "/newquiz — создать тест из файла\n"
               "/help — эта справка\n"
               "/testlarim — список ваших тестов\n"
               "/stop — остановить текущий тест\n"
               "/natija — ваш последний результат\n"
               "/lang — сменить язык"),
        "en": ("📖 <b>How the bot works</b>\n\n"
               "1. /newquiz — create a new quiz (or just send a file directly)\n"
               "2. Send a Word (.docx) or PDF test file\n"
               "3. Choose how many questions per part\n"
               "4. Choose the question order\n"
               "5. Choose seconds per question\n"
               "6. Press \"Ready!\" under the part you want\n\n"
               "<b>Commands:</b>\n"
               "/start — start the bot\n"
               "/newquiz — create a quiz from a file\n"
               "/help — this help\n"
               "/testlarim — your created tests\n"
               "/stop — stop the current test\n"
               "/natija — your last result\n"
               "/lang — change language"),
    },
    "newquiz_sorov": {
        "uz": "📎 Test faylini (Word .docx yoki PDF) yuboring — men uni Quiz'ga aylantiraman.{narx_qatori}",
        "ru": "📎 Отправьте файл теста (Word .docx или PDF) — я превращу его в Quiz.{narx_qatori}",
        "en": "📎 Send your test file (Word .docx or PDF) — I'll turn it into a Quiz.{narx_qatori}",
    },
    "newquiz_narx_qatori": {
        "uz": "\n\n💳 Xizmat narxi: <b>{narx}</b> (bitta fayl uchun)",
        "ru": "\n\n💳 Цена услуги: <b>{narx}</b> (за один файл)",
        "en": "\n\n💳 Service price: <b>{narx}</b> (per file)",
    },
    "faqat_fayl": {
        "uz": "Faqat .docx yoki .pdf fayl yuboring.",
        "ru": "Отправьте только файл .docx или .pdf.",
        "en": "Please send only a .docx or .pdf file.",
    },
    "fayl_oqilmoqda": {
        "uz": "⏳ Fayl o'qilmoqda va testlar ajratilmoqda...\n(biroz kuting)",
        "ru": "⏳ Читаю файл и извлекаю тесты...\n(подождите немного)",
        "en": "⏳ Reading the file and extracting questions...\n(please wait)",
    },
    "fayl_xato": {
        "uz": "Kechirasiz, faylni o'qishda xatolik. Boshqa fayl bilan urinib ko'ring.",
        "ru": "Извините, ошибка при чтении файла. Попробуйте другой файл.",
        "en": "Sorry, there was an error reading the file. Try another file.",
    },
    "ai_xato": {
        "uz": "Kechirasiz, hozir AI xizmatiga ulanib bo'lmadi. Birozdan so'ng "
              "qayta urinib ko'ring yoki botni sozlagan shaxsga xabar bering.",
        "ru": "Извините, сейчас не удалось подключиться к AI-сервису. "
              "Попробуйте позже или сообщите администратору бота.",
        "en": "Sorry, couldn't reach the AI service right now. Try again "
              "later or contact whoever set up the bot.",
    },
    "test_topilmadi": {
        "uz": "Faylda test topilmadi. Fayl formatini tekshiring.",
        "ru": "В файле не найдено тестов. Проверьте формат файла.",
        "en": "No questions found in the file. Check the file format.",
    },
    "topildi": {
        "uz": "✅ {n} ta test topildi.",
        "ru": "✅ Найдено {n} тестов.",
        "en": "✅ Found {n} questions.",
    },
    "toliq_emas_ogohlantirish": {
        "uz": "\n⚠️ AI xizmatida vaqtinchalik xatolik bo'lgani uchun ba'zi "
              "qismlar o'tkazib yuborilgan bo'lishi mumkin — fayldagi haqiqiy "
              "son bundan ko'p bo'lsa, birozdan so'ng qayta yuborib ko'ring.",
        "ru": "\n⚠️ Из-за временной ошибки AI-сервиса некоторые части могли "
              "быть пропущены — если в файле их больше, попробуйте отправить "
              "снова чуть позже.",
        "en": "\n⚠️ Because of a temporary AI service error, some parts may "
              "have been skipped — if the file actually has more, try "
              "resending it in a bit.",
    },
    "taxmin_ogohlantirish": {
        "uz": "\n⚠️ Shundan {n} tasining javobini AI o'zi topdi (faylda javob "
              "yo'q edi) — bularni tekshirib oling.",
        "ru": "\n⚠️ Для {n} из них ответ определил сам AI (в файле ответа не "
              "было) — пожалуйста, проверьте их.",
        "en": "\n⚠️ For {n} of them, the AI guessed the answer itself (the "
              "file had none) — please double-check those.",
    },
    "nechtadan_sorov": {
        "uz": "\n\nNechtadan qilib bo'laklarga bo'lay? (har biri alohida test bo'ladi) 👇",
        "ru": "\n\nНа сколько частей разбить? (каждая — отдельный тест) 👇",
        "en": "\n\nHow many questions per part? (each part is its own test) 👇",
    },
    "avval_fayl": {
        "uz": "Avval fayl yuboring.",
        "ru": "Сначала отправьте файл.",
        "en": "Please send a file first.",
    },
    "tartib_sorov": {
        "uz": "Savollar qanday tartibda kelsin? 🔀",
        "ru": "В каком порядке должны идти вопросы? 🔀",
        "en": "In what order should the questions appear? 🔀",
    },
    "soniya_sorov": {
        "uz": "Har savolga necha soniya beray? ⏱",
        "ru": "Сколько секунд давать на каждый вопрос? ⏱",
        "en": "How many seconds per question? ⏱",
    },
    "avval_fayl_sozlama": {
        "uz": "Avval fayl yuboring va sozlamalarni tanlang.",
        "ru": "Сначала отправьте файл и выберите настройки.",
        "en": "Please send a file and choose the settings first.",
    },
    "bolaklarga_bolindi": {
        "uz": "✅ Fayl {n} ta to'plamga bo'lindi. Har birini alohida boshlashingiz mumkin 👇",
        "ru": "✅ Файл разбит на {n} частей. Каждую можно начать отдельно 👇",
        "en": "✅ The file was split into {n} parts. You can start each one separately 👇",
    },
    "test_topilmadi_qayta": {
        "uz": "Bu test topilmadi — ehtimol bot qayta ishga tushirilgan. "
              "Test yuborgan odamdan havolani qayta so'rang.",
        "ru": "Этот тест не найден — возможно, бот был перезапущен. "
              "Попросите у отправителя ссылку заново.",
        "en": "This test wasn't found — the bot may have restarted. "
              "Ask whoever sent it for the link again.",
    },
    "tayyor_bolib_karta": {
        "uz": "🎯 <b>{nomi}</b> testiga tayyor bo'ling!\n\n"
              "📝 {savollar} ta savol\n"
              "⏱ Har savolga {soniya} soniya\n"
              "👤 Guruhda javoblar hammaga ko'rinadi\n\n"
              "Tayyor bo'lsangiz, tugmani bosing 👇",
        "ru": "🎯 Приготовьтесь к тесту «<b>{nomi}</b>»!\n\n"
              "📝 {savollar} вопросов\n"
              "⏱ {soniya} секунд на вопрос\n"
              "👤 В группе ответы видны всем\n\n"
              "Когда будете готовы, нажмите кнопку 👇",
        "en": "🎯 Get ready for the quiz <b>{nomi}</b>!\n\n"
              "📝 {savollar} questions\n"
              "⏱ {soniya} seconds per question\n"
              "👤 In groups, answers are visible to everyone\n\n"
              "Press the button when you're ready 👇",
    },
    "sessiya_topilmadi": {
        "uz": "Bu test sessiyasi topilmadi.",
        "ru": "Эта сессия теста не найдена.",
        "en": "This test session wasn't found.",
    },
    "davom_etmoqda": {
        "uz": "▶️ Test davom etmoqda...",
        "ru": "▶️ Тест продолжается...",
        "en": "▶️ The test is continuing...",
    },
    "javobsiz_toxtatildi": {
        "uz": "⏸ Oxirgi {n} ta savolga javob berilmadi. Test to'xtatildi.",
        "ru": "⏸ На последние {n} вопросов не было ответа. Тест остановлен.",
        "en": "⏸ No answer for the last {n} questions. The test was stopped.",
    },
    "yakuniy_natija": {
        "uz": "🏁 <b>{nomi}</b> testi yakunlandi!\n\n"
              "👤 {ism}\n"
              "Siz {jami} ta savoldan {javob_berilgan} tasiga javob berdingiz:\n\n"
              "✅ To'g'ri — <b>{tugri}</b>\n"
              "❌ Xato — {notogri}\n"
              "⏰ Tashlab ketilgan — {otkazib}\n"
              "⏱ {vaqt} soniya\n\n"
              "🏆 <b>{orin}-o'rin</b>, {ishtirokchi} ishtirokchidan.\n\n"
              "<i>Testni qayta yechishingiz mumkin, lekin bu reytingdagi o'rningizni o'zgartirmaydi.</i>",
        "ru": "🏁 Тест «<b>{nomi}</b>» завершён!\n\n"
              "👤 {ism}\n"
              "Вы ответили на {javob_berilgan} из {jami} вопросов:\n\n"
              "✅ Верно — <b>{tugri}</b>\n"
              "❌ Неверно — {notogri}\n"
              "⏰ Пропущено — {otkazib}\n"
              "⏱ {vaqt} сек.\n\n"
              "🏆 <b>{orin} место</b> из {ishtirokchi} участников.\n\n"
              "<i>Вы можете пройти тест снова, но это не изменит ваше место в рейтинге.</i>",
        "en": "🏁 The quiz <b>{nomi}</b> has finished!\n\n"
              "👤 {ism}\n"
              "You answered {javob_berilgan} of {jami} questions:\n\n"
              "✅ Correct — <b>{tugri}</b>\n"
              "❌ Wrong — {notogri}\n"
              "⏰ Missed — {otkazib}\n"
              "⏱ {vaqt} sec\n\n"
              "🏆 <b>{orin} place</b> out of {ishtirokchi}.\n\n"
              "<i>You can take the quiz again, but it won't change your leaderboard place.</i>",
    },
    "yuqoridagi_savol": {
        "uz": "Yuqoridagi savol — javobni tanlang:",
        "ru": "Вопрос выше — выберите ответ:",
        "en": "Question above — choose your answer:",
    },
    "ai_taxmin_izoh": {
        "uz": "⚠️ Javob AI tomonidan topilgan — tekshiring.",
        "ru": "⚠️ Ответ определён AI — проверьте.",
        "en": "⚠️ The answer was guessed by AI — please verify.",
    },
    "hali_yechmagan": {
        "uz": "Hali test yechmadingiz.",
        "ru": "Вы ещё не проходили тест.",
        "en": "You haven't taken a test yet.",
    },
    "natija_matni": {
        "uz": "📊 Natija: {tugri} / {jami} to'g'ri ({foiz}%)",
        "ru": "📊 Результат: {tugri} / {jami} правильно ({foiz}%)",
        "en": "📊 Score: {tugri} / {jami} correct ({foiz}%)",
    },
    "stop_faol_yoq": {
        "uz": "Hozir faol testingiz yo'q.",
        "ru": "У вас сейчас нет активного теста.",
        "en": "You don't have an active test right now.",
    },
    "stop_toxtatildi": {
        "uz": "⏹ Test to'xtatildi.",
        "ru": "⏹ Тест остановлен.",
        "en": "⏹ The test was stopped.",
    },
    "testlarim_royxat_yoq": {
        "uz": "Siz hali test yaratmagansiz. Fayl yuboring 📎",
        "ru": "Вы ещё не создали ни одного теста. Отправьте файл 📎",
        "en": "You haven't created any tests yet. Send a file 📎",
    },
    "testlarim_sarlavha": {
        "uz": "📋 Sizning testlaringiz:",
        "ru": "📋 Ваши тесты:",
        "en": "📋 Your tests:",
    },
    "til_tanlang": {
        "uz": "Tilni tanlang / Choose language / Выберите язык 👇",
        "ru": "Tilni tanlang / Choose language / Выберите язык 👇",
        "en": "Tilni tanlang / Choose language / Выберите язык 👇",
    },
    "til_ozgardi": {
        "uz": "✅ Til o'zbekchaga o'zgartirildi.",
        "ru": "✅ Язык изменён на русский.",
        "en": "✅ Language changed to English.",
    },
    "sozlamalar_saqlandi": {
        "uz": "⚙️ Sozlamalar saqlandi!",
        "ru": "⚙️ Настройки сохранены!",
        "en": "⚙️ Settings saved!",
    },
    "tayyor_boshlandi_karta": {
        "uz": "🚀 '{nomi}' boshlandi!\n\n📝 {savollar} ta savol · ⏱ {soniya} soniya/savol",
        "ru": "🚀 '{nomi}' начался!\n\n📝 {savollar} вопросов · ⏱ {soniya} сек./вопрос",
        "en": "🚀 '{nomi}' has started!\n\n📝 {savollar} questions · ⏱ {soniya} sec/question",
    },
    "stop_toxtatildi_karta": {
        "uz": "⏹ To'xtatildi.",
        "ru": "⏹ Остановлено.",
        "en": "⏹ Stopped.",
    },
    "sanoq_go": {
        "uz": "🚀 START!",
        "ru": "🚀 СТАРТ!",
        "en": "🚀 GO!",
    },
    # --- To'lov (Click orqali avtomatik) ---
    "tolov_sorov": {
        "uz": "💳 <b>To'lov talab qilinadi</b>\n\n"
              "Fayldan test yaratish xizmati narxi: <b>{narx}</b>\n\n"
              "━━━━━━━━━━━━━━━━━━━\n"
              "👇 Pastdagi tugmani bosib, Click orqali to'lang.\n"
              "✅ To'lov o'tishi bilan faylingiz AVTOMATIK qayta ishlanadi — kutish shart emas.",
        "ru": "💳 <b>Требуется оплата</b>\n\n"
              "Стоимость услуги: <b>{narx}</b>\n\n"
              "━━━━━━━━━━━━━━━━━━━\n"
              "👇 Нажмите кнопку ниже, чтобы оплатить через Click.\n"
              "✅ Как только оплата пройдёт, файл обработается АВТОМАТИЧЕСКИ — ждать подтверждения не нужно.",
        "en": "💳 <b>Payment required</b>\n\n"
              "Price for creating a quiz from a file: <b>{narx}</b>\n\n"
              "━━━━━━━━━━━━━━━━━━━\n"
              "👇 Press the button below to pay via Click.\n"
              "✅ As soon as payment goes through, your file is processed AUTOMATICALLY — no waiting needed.",
    },
    "tolov_kutilmoqda_ogohlantirish": {
        "uz": "⏳ Avvalgi faylingiz uchun to'lov hali tasdiqlanmagan. Iltimos, avval to'lovni yakunlang yoki tasdiqlanishini kuting.",
        "ru": "⏳ Оплата за предыдущий файл ещё не подтверждена. Сначала завершите оплату или дождитесь подтверждения.",
        "en": "⏳ Payment for your previous file hasn't been confirmed yet. Please finish that payment first or wait for confirmation.",
    },
    "tolov_tasdiqlandi_xabari": {
        "uz": "✅ <b>To'lov tasdiqlandi!</b>\n\nFaylingiz qayta ishlanmoqda... 🔄",
        "ru": "✅ <b>Оплата подтверждена!</b>\n\nВаш файл обрабатывается... 🔄",
        "en": "✅ <b>Payment confirmed!</b>\n\nYour file is being processed... 🔄",
    },
    "tugma_tolovga_otish": {"uz": "💳 To'lovga o'tish", "ru": "💳 Перейти к оплате", "en": "💳 Go to payment"},
    "tugma_fayldan_test_pullik": {
        "uz": "📎 Fayldan test yaratish — {narx}",
        "ru": "📎 Создать тест из файла — {narx}",
        "en": "📎 Create a quiz from file — {narx}",
    },
    "tugma_fayldan_test_bepul": {
        "uz": "📎 Fayldan test yaratish",
        "ru": "📎 Создать тест из файла",
        "en": "📎 Create a quiz from file",
    },
    # --- Tugmalar ---
    "tugma_hammasi_bitta": {"uz": "📦 Hammasi bitta", "ru": "📦 Всё одним тестом", "en": "📦 Everything as one"},
    "tugma_asl": {"uz": "📄 Hammasi o'z holida (fayldagidek)", "ru": "📄 Как в файле (без перемешивания)", "en": "📄 As in the file (no shuffle)"},
    "tugma_savol_aralash": {"uz": "❓🔀 Savollar aralash", "ru": "❓🔀 Перемешать вопросы", "en": "❓🔀 Shuffle questions"},
    "tugma_javob_aralash": {"uz": "🔤🔀 Javoblar aralash", "ru": "🔤🔀 Перемешать ответы", "en": "🔤🔀 Shuffle answers"},
    "tugma_hammasi_aralash": {"uz": "🎲 Savol va javoblar aralash", "ru": "🎲 Перемешать всё", "en": "🎲 Shuffle both"},
    "tugma_soniya": {"uz": "⏱ {n} soniya", "ru": "⏱ {n} сек.", "en": "⏱ {n} sec"},
    "tugma_tayyorman": {"uz": "🚀 Men tayyorman!", "ru": "🚀 Я готов!", "en": "🚀 I am ready!"},
    "tugma_ulashish": {"uz": "🔗 Testni ulashish", "ru": "🔗 Поделиться тестом", "en": "🔗 Share quiz"},
    "tugma_guruhda": {"uz": "👥 Guruhda boshlash", "ru": "👥 Начать в группе", "en": "👥 Start in group"},
    "tugma_davom": {"uz": "▶️ Davom ettirish", "ru": "▶️ Продолжить", "en": "▶️ Continue"},
    "tugma_tugatish": {"uz": "⏹ Tugatish", "ru": "⏹ Завершить", "en": "⏹ Finish"},
    "tugma_keyingi_toplam": {"uz": "➡️ Keyingi to'plam", "ru": "➡️ Следующая часть", "en": "➡️ Next part"},
    "tugma_qayta_urinish": {"uz": "🔄 Qayta urinish", "ru": "🔄 Попробовать снова", "en": "🔄 Try again"},
}


def t(kalit: str, til: str = STANDART_TIL, **kwargs) -> str:
    """Kalit bo'yicha matnni tanlangan tilda qaytaradi (parametrlar bilan
    formatlab). Kalit yoki til topilmasa, o'zbekcha (yoki xom kalit) qaytadi."""
    variantlar = _M.get(kalit)
    if not variantlar:
        return kalit
    matn = variantlar.get(til) or variantlar.get(STANDART_TIL) or next(iter(variantlar.values()))
    return matn.format(**kwargs) if kwargs else matn
