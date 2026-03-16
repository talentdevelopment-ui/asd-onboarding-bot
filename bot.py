"""
ASD Team Onboarding Bot — Ігор
Mattermost + Google Gemini API
- Сам пише новачкам першим у DM
- Відповідає на питання про ASD Team
- Надсилає нагадування перший тиждень

Змінні середовища:
  GEMINI_API_KEY      — ключ з aistudio.google.com
  MATTERMOST_BOT_TOKEN — токен Bot Account (Ігор)
  MATTERMOST_URL      — https://your-mattermost.com
  MATTERMOST_TOKEN    — токен Outgoing Webhook (для перевірки)
  PORT                — порт (Render ставить автоматично)
"""

import os, json, urllib.request, threading, time
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

# ─────────────────────────────────────────────
GEMINI_API_KEY       = os.environ.get("GEMINI_API_KEY", "")
MATTERMOST_BOT_TOKEN = os.environ.get("MATTERMOST_BOT_TOKEN", "")
MATTERMOST_URL       = os.environ.get("MATTERMOST_URL", "").rstrip("/")
MATTERMOST_TOKEN     = os.environ.get("MATTERMOST_TOKEN", "")
PORT = int(os.environ.get("PORT", 10000))

BOT_NAME = "Ігор"

# ─────────────────────────────────────────────
# СИСТЕМНИЙ ПРОМПТ
# ─────────────────────────────────────────────
SYSTEM_PROMPT = f"""Ти — {BOT_NAME}, офіційний AI-помічник для онбордингу нових співробітників компанії ASD Team (Advanced Software Development), Чернівці, Україна. Ти дружній, уважний і завжди готовий допомогти новачку освоїтись.

ЗАГАЛЬНА ІНФОРМАЦІЯ:
- ASD — українська аутсорсингова IT-компанія, заснована у 2007 році Павлом Бойком. Понад 18 років на ринку.
- Офіс: м. Чернівці, вул. Рівненська 5А. Сайт: https://asd.team/ Email: hrasdteam@gmail.com
- Цінності: Cooperation, Decency, Customer Orientation, Responsibility for the Result
- CEO: Бойко Павло. COO: Соловйова Ольга. Head of HR: Джобулда Юлія. HRA: Богдана Басараба.

ROADMAP ОНБОРДИНГУ:
- День 1: Welcome meeting з HR, зустріч з PM/ментором, заповнити чеклист
- Тиждень 1: Заповнити анкету в Notion, налаштувати всі інструменти
- 1 місяць: Зустріч з HR перед проміжним фідбеком
- 1.5 місяці: Проміжний feedback (PM, TL, HR)
- 2.5 місяці: Зустріч з HR перед закінченням випробувального терміну
- 3 місяці: Закінчення випробувального терміну (PM, TL, HR)

CHECKLIST (надсилати Богдані в Mattermost):
1. Фото на аватар Mattermost + фото для Employee Directory
2. NDA договір — підписати та надіслати HR
3. Копії паспорту та ідентифікаційного коду + CV компанії
4. Розмір футболки (S/M/L...) + реквізити Нової Пошти

КОРИСНІ ПОСИЛАННЯ NOTION:
- ASD Home: https://www.notion.so/ASD-Home-710107f8bc2a42daaf7f7635c2591bf7
- Техніка та ПЗ: https://www.notion.so/Software-f2e839672460432188164879005ec08f
- Feedbacks: https://www.notion.so/Feedbacks-c6b54977a19f44d5b2eca7632035d072
- Offboarding: https://www.notion.so/offboarding-78d836122d7a4f6db52251b0ac8f4fc2
- Відрядження: https://www.notion.so/3a1aeac68ad74231af72c9040d997a85
- Ladders: https://www.notion.so/Ladders-d6022381305e479cb0a5a3a71dc17f93
- Assessment flow: https://www.notion.so/Assessment-level-up-flow-4cc50edc9bb4402993487adac5c16f77
- Delivery Flow: https://www.notion.so/Delivery-Flow-165adb762c6f41e098c51e771ad05a45
- AI Policy: https://www.notion.so/AI-policy-2639415244c280ffb6b7e36f85e6b25b

MATTERMOST КАНАЛИ:
- Town Square — оголошення HR
- Off-Topic — неформальне спілкування, меми
- Our_team — привітання з днями народження
- Company Important Info — важливі новини від CEO
- Volunteering — волонтерство
- ASD Well-being — well-being програма
- Talent development — корпоративне навчання

ASD REPORTER — ТИПИ ПОДІЙ:
- Time off: відгул (зазначати години + коментар + як зв'язатись)
- Vacation: відпустка (повідомити PM)
- Sick day: лікарняний (довідка НЕ потрібна; похід до стоматолога = відгул!)
- Overtime: понаднормові / відпрацювання
- Business trip: відрядження
- Extended leave: відпустка за власний рахунок (до 10 р.д.)
ВАЖЛИВО: до кінця місяця time off не більше overtime. Коментарі в Reporter — англійською.

BENEFITS:
- 15 р.д. оплачуваної відпустки (21 кал. день). +1 день з 3-го року. Макс 23 р.д.
- Безлімітний оплачуваний лікарняний. Корпоративний лікар: Трефаненко Ірина
- Гнучкий графік. Відпустку можна взяти відразу після випробувального терміну
- Щорічний перегляд зарплати. Бонуси (новорічні, при підвищенні, на ДН)
- Well-being: психолог Оксана, лікар Ірина, заняття з англійської (Ірина Сапожник)
- Реферальна програма. Допомога при релокейті (перший тиждень оренди)
- Навчання за рахунок компанії: конференції, курси, сертифікація

ПРАВИЛА ВІДПОВІДЕЙ:
- Звати себе {BOT_NAME}
- Відповідай ВИКЛЮЧНО українською мовою
- Будь дружнім і теплим, як справжній колега
- Давай конкретні відповіді з посиланнями на Notion
- Відповідай стисло (3-4 абзаци максимум)
- Якщо не знаєш — направ до hrasdteam@gmail.com або Богдани в Mattermost
- Форматування Mattermost: **жирний**, *курсив*, - списки"""

# ─────────────────────────────────────────────
# ПРИВІТАЛЬНЕ ПОВІДОМЛЕННЯ
# ─────────────────────────────────────────────
def welcome_message(user_name):
    return f"""👋 Привіт, @{user_name}! Мене звати **{BOT_NAME}** — я твій особистий помічник з онбордингу в #ASDTeam 🤖

Я тут щоб допомогти тобі швидко освоїтись: відповім на будь-яке питання про компанію, процеси, інструменти та правила — і все це приватно, тільки між нами!

**Ось з чого почати:**
- `/checklist` — що зробити в перший день
- `/roadmap` — твій план на 3 місяці
- `/contacts` — до кого звертатись
- `/links` — всі посилання на Notion

Або просто напиши своє питання — я завжди тут! 😊"""

# ─────────────────────────────────────────────
# НАГАДУВАННЯ НА ПЕРШИЙ ТИЖДЕНЬ
# ─────────────────────────────────────────────
WEEKLY_REMINDERS = {
    1: f"""👋 **День 1 — Welcome day!**

Привіт! Це {BOT_NAME} 🤖 Нагадую твій план на сьогодні:
- ✅ Welcome meeting з HR (Юлія / Богдана)
- ✅ Зустріч з PM / ментором
- ✅ Поставити аватар у Mattermost
- ✅ Надіслати фото Богдані (для Employee Directory)
- ✅ [Onboarding book в Notion](https://www.notion.so/ASD-Home-710107f8bc2a42daaf7f7635c2591bf7)

Питання? Пиши мені! 🤖""",

    2: """📋 **День 2 — Документи**

- ✅ Підписати NDA та надіслати HR
- ✅ Копії паспорту та ідентифікаційного коду
- ✅ Заповнити CV компанії
- ✅ Розмір футболки + реквізити Нової Пошти
- ℹ️ Все надсилай **Богдані** в особисті повідомлення в Mattermost""",

    3: """⏱ **День 3 — ASD Reporter**

- ✅ Увійти в ASD Reporter
- ✅ Внести перший Worklog (щодня обов'язково!)
- ✅ Відкрити Google Calendar для колег
- ✅ Підтверджувати запрошення на мітинги
- ℹ️ Коментарі в Reporter — **англійською**""",

    4: """📚 **День 4 — Notion ASD Home**

- ✅ [ASD Home](https://www.notion.so/ASD-Home-710107f8bc2a42daaf7f7635c2591bf7) — всі розділи
- ✅ Employee Directory — знайди себе та колег
- ✅ Mission, Vision, Values
- ✅ [AI Policy](https://www.notion.so/AI-policy-2639415244c280ffb6b7e36f85e6b25b)
- ✅ Well-being program — там багато корисного!""",

    5: f"""🚀 **День 5 — Фінал першого тижня!**

- ✅ [Ladders](https://www.notion.so/Ladders-d6022381305e479cb0a5a3a71dc17f93) — матриці компетенцій
- ✅ [Assessment flow](https://www.notion.so/Assessment-level-up-flow-4cc50edc9bb4402993487adac5c16f77) — як проходять оцінки
- ✅ [Delivery Flow](https://www.notion.so/Delivery-Flow-165adb762c6f41e098c51e771ad05a45) — цикл проєкту
- ✅ Заповнити анкету в Notion

🎉 Вітаємо з першим тижнем в #ASDTeam! Я — {BOT_NAME} — завжди тут якщо щось потрібно!"""
}

# ─────────────────────────────────────────────
# MATTERMOST API
# ─────────────────────────────────────────────
def mm_request(method, path, data=None):
    """Виконати запит до Mattermost API."""
    url = f"{MATTERMOST_URL}/api/v4{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(
        url, data=body, method=method,
        headers={
            "Authorization": f"Bearer {MATTERMOST_BOT_TOKEN}",
            "Content-Type": "application/json"
        }
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())

def get_or_create_dm(user_id):
    """Отримати або створити DM канал з користувачем."""
    bot_info = mm_request("GET", "/users/me")
    bot_id = bot_info["id"]
    channel = mm_request("POST", "/channels/direct", [bot_id, user_id])
    return channel["id"]

def send_dm(user_id, text):
    """Надіслати особисте повідомлення користувачу."""
    channel_id = get_or_create_dm(user_id)
    mm_request("POST", "/posts", {"channel_id": channel_id, "message": text})
    return channel_id

def get_user_info(user_id):
    """Отримати інформацію про користувача."""
    return mm_request("GET", f"/users/{user_id}")

# ─────────────────────────────────────────────
# GEMINI AI
# ─────────────────────────────────────────────
conversation_history = {}

def get_gemini_response(user_id, user_message):
    if user_id not in conversation_history:
        conversation_history[user_id] = []

    conversation_history[user_id].append({
        "role": "user", "parts": [{"text": user_message}]
    })

    if len(conversation_history[user_id]) > 10:
        conversation_history[user_id] = conversation_history[user_id][-10:]

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    )
    payload = json.dumps({
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": conversation_history[user_id],
        "generationConfig": {"maxOutputTokens": 800, "temperature": 0.7}
    }).encode()

    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())

    reply = data["candidates"][0]["content"]["parts"][0]["text"]
    conversation_history[user_id].append({
        "role": "model", "parts": [{"text": reply}]
    })
    return reply

# ─────────────────────────────────────────────
# НАГАДУВАННЯ — ПЛАНУВАЛЬНИК
# ─────────────────────────────────────────────
new_employees = {}  # user_id -> {"start_date", "sent_days": set()}

def register_new_employee(user_id):
    """Зареєструвати новачка для нагадувань."""
    if user_id not in new_employees:
        new_employees[user_id] = {
            "start_date": datetime.now().date(),
            "sent_days": set()
        }
        print(f"[REMIND] Registered {user_id}")

def _reminder_loop():
    """Фоновий планувальник — перевіряє кожні 30 хвилин."""
    while True:
        now = datetime.now()
        # Надсилати нагадування о 9:00 ранку
        if now.hour == 9 and now.minute < 30:
            today = now.date()
            for user_id, info in list(new_employees.items()):
                day = (today - info["start_date"]).days + 1
                if 1 <= day <= 5 and day not in info["sent_days"]:
                    try:
                        send_dm(user_id, WEEKLY_REMINDERS[day])
                        info["sent_days"].add(day)
                        print(f"[REMIND] Day {day} → {user_id}")
                    except Exception as e:
                        print(f"[REMIND] Error: {e}")
                if day > 5:
                    del new_employees[user_id]
        time.sleep(1800)  # перевіряти кожні 30 хвилин

# ─────────────────────────────────────────────
# WEBHOOK — обробник повідомлень
# ─────────────────────────────────────────────
class MattermostHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        """Health check для Render."""
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(f"{BOT_NAME} (ASD Onboarding Bot) is running! 🚀".encode())

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        try:
            data = json.loads(body.decode("utf-8"))
        except Exception:
            self._r(400, "{}"); return

        # Перевірка токена webhook
        if MATTERMOST_TOKEN and data.get("token") != MATTERMOST_TOKEN:
            self._r(403, "{}"); return

        # Ігнорувати повідомлення від самого бота
        if data.get("bot_id") or data.get("user_name") in ["onboarding-bot", "igor-bot"]:
            self._r(200, "{}"); return

        user_id   = data.get("user_id", "unknown")
        user_name = data.get("user_name", "colleague")
        text      = data.get("text", "").strip()

        # Прибрати згадку бота
        for mention in ["@onboarding-bot", "@igor", f"@{BOT_NAME.lower()}"]:
            text = text.replace(mention, "").strip()

        # Обробити подію "новий користувач" якщо є
        event = data.get("event", "")
        if event == "user_added" or data.get("trigger_word") == "new_member":
            self._handle_new_member(user_id, user_name)
            self._r(200, "{}"); return

        if not text:
            self._r(200, "{}"); return

        reply = self._handle_message(user_id, user_name, text)
        self._r(200, json.dumps({"text": reply, "response_type": "in_channel"}))

    def _handle_new_member(self, user_id, user_name):
        """Привітати нового співробітника в DM."""
        try:
            send_dm(user_id, welcome_message(user_name))
            register_new_employee(user_id)
            print(f"[BOT] Welcomed new member: {user_name}")
        except Exception as e:
            print(f"[BOT] Error welcoming {user_name}: {e}")

    def _handle_message(self, user_id, user_name, text):
        lower = text.lower().strip()

        if lower in ["привіт", "hello", "/start", "/help", "/допомога", "старт"]:
            return welcome_message(user_name)

        if lower in ["/checklist", "/чеклист"]:
            return (
                "📋 **Чеклист нового працівника**\n"
                "*(надсилати Богдані в особисті в Mattermost)*\n\n"
                "**1. Фото та профіль**\n"
                "- Аватар у Mattermost\n"
                "- Фото для Employee Directory\n\n"
                "**2. Документи**\n"
                "- [NDA договір](https://www.notion.so/ASD-Home-710107f8bc2a42daaf7f7635c2591bf7) → підписати та надіслати HR\n"
                "- Копії паспорту та ідентифікаційного коду\n"
                "- CV компанії\n\n"
                "**3. Інше**\n"
                "- Розмір футболки (S/M/L...)\n"
                "- Реквізити Нової Пошти\n\n"
                "**4. Тиждень 1**\n"
                "- [Анкета в Notion](https://www.notion.so/ASD-Home-710107f8bc2a42daaf7f7635c2591bf7)"
            )

        if lower in ["/roadmap", "/роадмап"]:
            return (
                "🗺 **Roadmap онбордингу**\n\n"
                "**День 1:** Welcome meeting з HR + зустріч з PM + чеклист\n"
                "**Тиждень 1:** Анкета в Notion + налаштування інструментів\n"
                "**1 місяць:** Зустріч з HR перед проміжним фідбеком\n"
                "**1.5 місяці:** Проміжний feedback (PM, TL, HR)\n"
                "**2.5 місяці:** Зустріч з HR перед кінцем випробувального терміну\n"
                "**3 місяці:** Закінчення випробувального терміну ✅"
            )

        if lower in ["/contacts", "/контакти"]:
            return (
                "👥 **Контакти ASD Team**\n\n"
                "- **Бойко Павло** — CEO\n"
                "- **Соловйова Ольга** — COO\n"
                "- **Джобулда Юлія** — Head of HR\n"
                "- **Богдана Басараба** — HRA *(перша точка контакту!)*\n"
                "- **Трефаненко Дмитро** — Офіс-менеджер\n"
                "- **Трефаненко Ірина** — Корпоративний лікар\n"
                "- **Оксана Пендерецька** — Психолог\n"
                "- **Ірина Сапожник** — Викладач англійської\n"
                "- **Юлія Одинак** — Фінансист\n\n"
                "📧 hrasdteam@gmail.com | 🌐 https://asd.team/"
            )

        if lower in ["/links", "/посилання"]:
            return (
                "🔗 **Корисні посилання Notion**\n\n"
                "- [🏠 ASD Home](https://www.notion.so/ASD-Home-710107f8bc2a42daaf7f7635c2591bf7)\n"
                "- [💻 Техніка та ПЗ](https://www.notion.so/Software-f2e839672460432188164879005ec08f)\n"
                "- [💬 Feedbacks](https://www.notion.so/Feedbacks-c6b54977a19f44d5b2eca7632035d072)\n"
                "- [✈️ Відрядження](https://www.notion.so/3a1aeac68ad74231af72c9040d997a85)\n"
                "- [📊 Ladders](https://www.notion.so/Ladders-d6022381305e479cb0a5a3a71dc17f93)\n"
                "- [🎯 Assessment flow](https://www.notion.so/Assessment-level-up-flow-4cc50edc9bb4402993487adac5c16f77)\n"
                "- [🔄 Delivery Flow](https://www.notion.so/Delivery-Flow-165adb762c6f41e098c51e771ad05a45)\n"
                "- [🤖 AI Policy](https://www.notion.so/AI-policy-2639415244c280ffb6b7e36f85e6b25b)\n"
                "- [🚪 Offboarding](https://www.notion.so/offboarding-78d836122d7a4f6db52251b0ac8f4fc2)"
            )

        try:
            return get_gemini_response(user_id, text)
        except Exception as e:
            print(f"[ERROR] Gemini: {e}")
            return f"⚠️ Вибач, не вдалось відповісти. Спробуй ще раз або звернись до HR: hrasdteam@gmail.com"

    def _r(self, code, body):
        b = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(b))
        self.end_headers()
        self.wfile.write(b)

    def log_message(self, fmt, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {fmt % args}")

# ─────────────────────────────────────────────
# ЗАПУСК
# ─────────────────────────────────────────────
if __name__ == "__main__":
    missing = []
    if not GEMINI_API_KEY:       missing.append("GEMINI_API_KEY")
    if not MATTERMOST_BOT_TOKEN: missing.append("MATTERMOST_BOT_TOKEN")
    if not MATTERMOST_URL:       missing.append("MATTERMOST_URL")
    if missing:
        print(f"❌ Відсутні змінні: {', '.join(missing)}")
        exit(1)

    threading.Thread(target=_reminder_loop, daemon=True).start()

    print(f"🚀 {BOT_NAME} (ASD Onboarding Bot) запущено на порту {PORT}")
    print(f"📡 Webhook: POST /webhook")
    print(f"💚 Health:  GET  /")
    HTTPServer(("0.0.0.0", PORT), MattermostHandler).serve_forever()
