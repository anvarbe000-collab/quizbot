"""
db.py — SQLite orqali doimiy saqlash (bot qayta ishga tushirilsa ham
ma'lumotlar yo'qolmasligi uchun): foydalanuvchi tili, viktorinalar
(savol-javoblari bilan) va reyting (kim nechta to'g'ri va qancha vaqtda
yechgani). Barcha funksiyalar asyncio bilan mos — sqlite3ning bloklovchi
chaqiruvlari alohida oqimda (thread) bajariladi.
"""
import asyncio
import json
import os
import sqlite3

DB_YOLI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot.db")


def _ulanish():
    conn = sqlite3.connect(DB_YOLI)
    conn.row_factory = sqlite3.Row
    return conn


def _sozlash():
    conn = _ulanish()
    conn.execute("""CREATE TABLE IF NOT EXISTS foydalanuvchilar (
        id INTEGER PRIMARY KEY,
        til TEXT NOT NULL DEFAULT 'uz'
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS viktorinalar (
        id TEXT PRIMARY KEY,
        egasi_id INTEGER,
        nomi TEXT,
        testlar_json TEXT,
        soniya INTEGER,
        tartib TEXT,
        keyingi_quiz_id TEXT,
        yaratilgan_vaqt REAL
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS reyting (
        quiz_id TEXT,
        uid INTEGER,
        ism TEXT,
        tugri INTEGER,
        vaqt REAL,
        PRIMARY KEY (quiz_id, uid)
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS tolovlar (
        id TEXT PRIMARY KEY,
        uid INTEGER,
        ism TEXT,
        fayl_nomi TEXT,
        fayl_bayt BLOB,
        holat TEXT NOT NULL DEFAULT 'kutilmoqda',
        yaratilgan_vaqt REAL,
        narxi REAL,
        click_trans_id TEXT
    )""")
    # eski bazada (Click qo'shilishidan oldin yaratilgan) bu ustunlar
    # bo'lmasligi mumkin — mavjud bo'lmasa qo'shamiz (ma'lumot yo'qolmasin)
    mavjud_ustunlar = {r["name"] for r in conn.execute("PRAGMA table_info(tolovlar)")}
    for ustun, tur in (("narxi", "REAL"), ("click_trans_id", "TEXT")):
        if ustun not in mavjud_ustunlar:
            conn.execute(f"ALTER TABLE tolovlar ADD COLUMN {ustun} {tur}")
    conn.commit()
    conn.close()


_sozlash()


async def _ish(f, *args):
    return await asyncio.to_thread(f, *args)


def _til_olish_sync(uid):
    conn = _ulanish()
    row = conn.execute("SELECT til FROM foydalanuvchilar WHERE id=?", (uid,)).fetchone()
    conn.close()
    return row["til"] if row else None


async def til_olish(uid):
    """Foydalanuvchining saqlangan tilini qaytaradi (yo'q bo'lsa None)."""
    return await _ish(_til_olish_sync, uid)


def _til_saqlash_sync(uid, til):
    conn = _ulanish()
    conn.execute(
        "INSERT INTO foydalanuvchilar (id, til) VALUES (?, ?) "
        "ON CONFLICT(id) DO UPDATE SET til=excluded.til", (uid, til))
    conn.commit()
    conn.close()


async def til_saqlash(uid, til):
    await _ish(_til_saqlash_sync, uid, til)


def _viktorina_saqlash_sync(quiz_id, egasi_id, nomi, testlar, soniya, tartib,
                            keyingi_quiz_id, yaratilgan_vaqt):
    conn = _ulanish()
    conn.execute(
        """INSERT INTO viktorinalar
           (id, egasi_id, nomi, testlar_json, soniya, tartib, keyingi_quiz_id, yaratilgan_vaqt)
           VALUES (?,?,?,?,?,?,?,?)
           ON CONFLICT(id) DO UPDATE SET keyingi_quiz_id=excluded.keyingi_quiz_id""",
        (quiz_id, egasi_id, nomi, json.dumps(testlar, ensure_ascii=False),
         soniya, tartib, keyingi_quiz_id, yaratilgan_vaqt))
    conn.commit()
    conn.close()


async def viktorina_saqlash(quiz_id, egasi_id, nomi, testlar, soniya, tartib,
                            keyingi_quiz_id, yaratilgan_vaqt):
    await _ish(_viktorina_saqlash_sync, quiz_id, egasi_id, nomi, testlar, soniya,
               tartib, keyingi_quiz_id, yaratilgan_vaqt)


def _viktorina_olish_sync(quiz_id):
    conn = _ulanish()
    row = conn.execute("SELECT * FROM viktorinalar WHERE id=?", (quiz_id,)).fetchone()
    conn.close()
    if not row:
        return None
    return {
        "nomi": row["nomi"], "testlar": json.loads(row["testlar_json"]),
        "soniya": row["soniya"], "tartib": row["tartib"],
        "keyingi_quiz_id": row["keyingi_quiz_id"], "egasi_id": row["egasi_id"],
    }


async def viktorina_olish(quiz_id):
    """Quiz_id bo'yicha viktorinani bazadan o'qiydi (topilmasa None)."""
    return await _ish(_viktorina_olish_sync, quiz_id)


def _foydalanuvchi_viktorinalari_sync(uid, limit):
    conn = _ulanish()
    rows = conn.execute(
        "SELECT id, nomi, yaratilgan_vaqt FROM viktorinalar "
        "WHERE egasi_id=? ORDER BY yaratilgan_vaqt DESC LIMIT ?", (uid, limit)).fetchall()
    conn.close()
    return [(r["id"], r["nomi"]) for r in rows]


async def foydalanuvchi_viktorinalari(uid, limit=15):
    """Shu foydalanuvchi yaratgan so'nggi viktorinalar ro'yxati [(id, nomi), ...]."""
    return await _ish(_foydalanuvchi_viktorinalari_sync, uid, limit)


def _reyting_yozish_sync(quiz_id, uid, ism, tugri, vaqt):
    conn = _ulanish()
    bor = conn.execute("SELECT 1 FROM reyting WHERE quiz_id=? AND uid=?", (quiz_id, uid)).fetchone()
    if not bor:
        conn.execute("INSERT INTO reyting (quiz_id, uid, ism, tugri, vaqt) VALUES (?,?,?,?,?)",
                     (quiz_id, uid, ism, tugri, vaqt))
        conn.commit()
    conn.close()


async def reyting_yozish(quiz_id, uid, ism, tugri, vaqt):
    """Reytingga yozadi — FAQAT birinchi urinish (qayta urinish o'rinni
    o'zgartirmaydi, QuizBot kabi)."""
    await _ish(_reyting_yozish_sync, quiz_id, uid, ism, tugri, vaqt)


def _reyting_orni_sync(quiz_id, uid):
    conn = _ulanish()
    rows = conn.execute(
        "SELECT uid FROM reyting WHERE quiz_id=? ORDER BY tugri DESC, vaqt ASC", (quiz_id,)).fetchall()
    conn.close()
    jami = len(rows)
    for i, r in enumerate(rows):
        if r["uid"] == uid:
            return i + 1, jami
    return jami, jami


async def reyting_orni(quiz_id, uid):
    """(o'rin, jami_ishtirokchi) — shu quiz_id bo'yicha reytingdagi o'rin."""
    return await _ish(_reyting_orni_sync, quiz_id, uid)


def _tolov_yaratish_sync(tolov_id, uid, ism, fayl_nomi, fayl_bayt, narxi, yaratilgan_vaqt):
    conn = _ulanish()
    conn.execute(
        """INSERT INTO tolovlar (id, uid, ism, fayl_nomi, fayl_bayt, holat, narxi, yaratilgan_vaqt)
           VALUES (?,?,?,?,?, 'kutilmoqda', ?, ?)""",
        (tolov_id, uid, ism, fayl_nomi, fayl_bayt, narxi, yaratilgan_vaqt))
    conn.commit()
    conn.close()


async def tolov_yaratish(tolov_id, uid, ism, fayl_nomi, fayl_bayt, narxi, yaratilgan_vaqt):
    """Yangi kutilayotgan to'lov (va unga tegishli fayl) yozadi. narxi —
    shu aniq to'lov uchun belgilangan summa (keyinchalik Click Prepare
    bosqichida solishtirish uchun saqlanadi)."""
    await _ish(_tolov_yaratish_sync, tolov_id, uid, ism, fayl_nomi, fayl_bayt, narxi, yaratilgan_vaqt)


def _tolov_olish_sync(tolov_id):
    conn = _ulanish()
    row = conn.execute("SELECT * FROM tolovlar WHERE id=?", (tolov_id,)).fetchone()
    conn.close()
    if not row:
        return None
    return {
        "uid": row["uid"], "ism": row["ism"], "fayl_nomi": row["fayl_nomi"],
        "fayl_bayt": row["fayl_bayt"], "holat": row["holat"],
        "narxi": row["narxi"], "click_trans_id": row["click_trans_id"],
    }


async def tolov_olish(tolov_id):
    """To'lov yozuvini bazadan o'qiydi (topilmasa None)."""
    return await _ish(_tolov_olish_sync, tolov_id)


def _tolov_holatini_yangilash_sync(tolov_id, holat):
    conn = _ulanish()
    conn.execute("UPDATE tolovlar SET holat=? WHERE id=?", (holat, tolov_id))
    conn.commit()
    conn.close()


async def tolov_holatini_yangilash(tolov_id, holat):
    """holat: 'kutilmoqda' | 'tayyorlangan' | 'tasdiqlangan' | 'bekor_qilingan'."""
    await _ish(_tolov_holatini_yangilash_sync, tolov_id, holat)


def _tolov_click_prepare_yozish_sync(tolov_id, click_trans_id):
    conn = _ulanish()
    conn.execute("UPDATE tolovlar SET click_trans_id=?, holat='tayyorlangan' WHERE id=?",
                 (click_trans_id, tolov_id))
    conn.commit()
    conn.close()


async def tolov_click_prepare_yozish(tolov_id, click_trans_id):
    """Click 'Prepare' bosqichi muvaffaqiyatli o'tganda chaqiriladi —
    Click'ning tranzaksiya ID'sini saqlaydi (Complete bosqichida
    solishtirish uchun) va holatni 'tayyorlangan'ga o'zgartiradi."""
    await _ish(_tolov_click_prepare_yozish_sync, tolov_id, click_trans_id)
