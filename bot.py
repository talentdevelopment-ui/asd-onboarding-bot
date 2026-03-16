"""
ASD Team Onboarding Bot for Mattermost
Запуск: python bot.py
Потрібні змінні середовища: ANTHROPIC_API_KEY, MATTERMOST_TOKEN
"""

import os
import json
import anthropic
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timedelta
import threading

# ──────────────────────────────────────────────
# КОНФІГУРАЦІЯ
# ──────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MATTERMOST_TOKEN  = os.environ.get("MATTERMOST_TOKEN", "")   # Outgoing webhook token
PORT = int(os.environ.get("PORT", 8080))

# ──────────────────────────────────────────────
# СИСТЕМНИЙ ПРОМПТ — база знань ASD Team
# ──────────────────────────────────────────────
SYSTEM_PROMPT = """Ти — офіційний AI-помічник для онбордингу нових співробітників компанії ASD Team (Advanced Software Development), Чернівці, Україна.

ЗАГАЛЬНА ІНФОРМАЦІЯ:
- ASD — українська аутсорсингова IT-компанія, заснована у 2007 році Павлом Бойком. Понад 18 років на ринку.
- Офіс: м. Чернівці, вул. Рівненська 5А. Сайт: https://asd.team/  Email: hrasdteam@gmail.com
- Цінності: Cooperation, Decency, Customer Orientation, Responsibility for the Result
- CEO: Бойко Павло. COO: Соловйова Ольга. Head of HR: Джобулда Юлія. HRA: Богдана Басараба.

ROADMAP ОНБОРДИНГУ:
- День 1: Welcome meeting з HR, зустріч з PM/ментором, заповнити чеклист
- Тиждень 1: Заповнити анкету в Notion, налаштувати всі інструменти
- 1 місяць: Зустріч з HR перед проміжним фідбеком
- 1.5 місяці: Проміжний feedback (PM, TL, HR)
- 2.5 місяці: Зустріч з HR перед закінченням випробувального терміну
- 3 місяці: Закінчення випробувального терміну (PM, TL, HR)

CHECKLIST (надсилати через Mattermost HRA):
1. Фото на аватар Mattermost + фото для Employee Directory
2. NDA договір — підписати та надіслати HR
3. Копії паспорту та ідентифікаційного коду + CV компанії
4. Розмір футболки (S/M/L...) + реквізити Нової Пошти

ІНСТРУМЕНТИ:
- Notion ASD Home: https://www.notion.so/ASD-Home-710107f8bc2a42daaf7f7635c2591bf7
- Техніка та ПЗ: https://www.notion.so/Software-f2e839672460432188164879005ec08f
- Feedbacks: https://www.notion.so/Feedbacks-c6b54977a19f44d5b2eca7632035d072
- Offboarding: https://www.notion.so/offboarding-78d836122d7a4f6db52251b0ac8f4fc2
- Відрядження: https://www.notion.so/3a1aeac68ad74231af72c9040d997a85
- Ladders: https://www.notion.so/Ladders-d6022381305e479cb0a5a3a71dc17f93
- Assessment flow: https://www.notion.so/Assessment-level-up-flow-4cc50edc9bb4402993487adac5c16f77
- Delivery Flow: https://www.notion.so/Delivery-Flow-165adb762c6f41e098c51e771ad05a45
- AI Policy: https://www.notion.so/AI-policy-2639415244c280ffb6b7e36f85e6b25b
- ASD Reporter — трекінг робочого часу

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
- Overtime: понаднормові/відпрацювання
- Business trip: відрядження
- Extended leave: відпустка за власний рахунок (до 10 р.д.)
ВАЖЛИВО: до кінця місяця time off ≤ overtime. Коментарі в Reporter — англійською.

BENEFITS:
- 15 р.д. оплачуваної відпустки (21 кал. день). +1 день з 3-го року. Макс 23 р.д.
- Безлімітний оплачуваний лікарняний. Корпоративний лікар: Трефаненко Ірина
- Гнучкий графік. Відпустку можна взяти відразу після випробувального терміну
- Щорічний перегляд зарплати. Бонуси (новорічні, при підвищенні, на ДН)
- Well-being: психолог Оксана, лікар Ірина, заняття з англійської (Ірина Сапожник)
- Реферальна програма. Допомога при релокейті (перший тиждень оренди)
- Навчання за рахунок компанії: конференції, курси, сертифікація

ПРАВИЛА МІТИНГІВ:
- Завжди вмикати камеру
- Вимикати мікрофон якщо не говориш
- Підтверджувати запрошення в Google Calendar
- Додавати учасників за корпоративною поштою (@asd.team)
- Нагадування мінімум за 10 хвилин

ПРАВИЛА:
- Відповідай ВИКЛЮЧНО українською мовою
- Давай конкретні відповіді з посиланнями на Notion де можливо
- Будь дружнім і корисним
- Якщо не знаєш точну відповідь — направ до HR: hrasdteam@gmail.com або Богдани в Mattermost
- Відповідай стисло, максимум 3-4 абзаци
- Використовуй форматування Mattermost: **жирний**, *курсив*, - списки"""

# ──────────────────────────────────────────────
# НАГАДУВАННЯ ДЛЯ ПЕРШОГО ТИЖНЯ
# ──────────────────────────────────────────────
WEEKLY_REMINDERS = {
    1: """👋 **День 1 — Welcome day!**

Ласкаво просимо до #ASDTeam! Ось твій план на сьогодні:
- ✅ Welcome meeting з HR (Юлія / Богдана)
- ✅ Зустріч з PM / ментором
- ✅ Поставити аватар у Mattermost
- ✅ Надіслати фото Богдані в Mattermost (для Employee Directory)
- ✅ Ознайомитись з [Onboarding book в Notion](https://www.notion.so/ASD-Home-710107f8bc2a42daaf7f7635c2591bf7)

Якщо маєш питання — пиши мені! 🤖""",

    2: """📋 **День 2 — Документи**

Сьогодні потрібно:
- ✅ Підписати NDA договір та надіслати HR
- ✅ Надати копії паспорту та ідентифікаційного коду
- ✅ Заповнити CV компанії
- ✅ Написати розмір футболки (S/M/L...) та реквізити Нової Пошти
- ℹ️ Всю інформацію надсилай Богдані в особисті повідомлення в Mattermost

[Всі деталі в Notion →](https://www.notion.so/ASD-Home-710107f8bc2a42daaf7f7635c2591bf7)""",

    3: """⏱ **День 3 — ASD Reporter**

Час розібратись з трекінгом часу:
- ✅ Увійти в ASD Reporter
- ✅ Внести перший Worklog (щодня обов'язково!)
- ✅ Відкрити Google Calendar для колег
- ✅ Підтверджувати запрошення на мітинги
- ℹ️ Коментарі в Reporter — **англійською**

Питання? Пиши мені або Богдані 😊""",

    4: """📚 **День 4 — Notion ASD Home**

Досліджуй головний хаб компанії:
- ✅ [ASD Home](https://www.notion.so/ASD-Home-710107f8bc2a42daaf7f7635c2591bf7) — всі розділи Team, How to, Helpful info
- ✅ Знайди себе в Employee Directory
- ✅ Прочитай Mission, Vision, Values
- ✅ Ознайомся з [AI Policy](https://www.notion.so/AI-policy-2639415244c280ffb6b7e36f85e6b25b)
- ✅ Переглянь Well-being program — там багато крутого для тебе!""",

    5: """🚀 **День 5 — Завершення тижня**

Останній штрих першого тижня:
- ✅ [Ladders](https://www.notion.so/Ladders-d6022381305e479cb0a5a3a71dc17f93) — матриці компетенцій твоєї спеціалізації
- ✅ [Assessment flow](https://www.notion.so/Assessment-level-up-flow-4cc50edc9bb4402993487adac5c16f77) — як проходять оцінки
- ✅ [Delivery Flow](https://www.notion.so/Delivery-Flow-165adb762c6f41e098c51e771ad05a45) — цикл проєкту
- ✅ Заповнити анкету в Notion (перший тиждень)

Вітаємо з першим тижнем в #ASDTeam! 🎉 Ти молодець!"""
}

# ──────────────────────────────────────────────
# ЗБЕРЕЖЕННЯ КОНТЕКСТУ РОЗМОВ
# ──────────────────────────────────────────────
conversation_history = {}  # user_id -> list of messages

def get_ai_response(user_id: str, user_message: str) -> str:
    """Отримати відповідь від Claude з урахуванням контексту розмови."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    if user_id not in conversation_history:
        conversation_history[user_id] = []

    conversation_history[user_id].append({
        "role": "user",
        "content": user_message
    })

    # Зберігаємо лише останні 10 повідомлень
    if len(conversation_history[user_id]) > 10:
        conversation_history[user_id] = conversation_history[user_id][-10:]

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=conversation_history[user_id]
    )

    reply = response.content[0].text

    conversation_history[user_id].append({
        "role": "assistant",
        "content": reply
    })

    return reply


# ──────────────────────────────────────────────
# WEBHOOK HANDLER
# ──────────────────────────────────────────────
class MattermostWebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body.decode('utf-8'))
        except Exception:
            self.send_response(400)
            self.end_headers()
            return

        # Перевірка токена
        token = data.get('token', '')
        if MATTERMOST_TOKEN and token != MATTERMOST_TOKEN:
            self.send_response(403)
            self.end_headers()
            return

        user_id = data.get('user_id', 'unknown')
        user_name = data.get('user_name', 'colleague')
        text = data.get('text', '').strip()
        channel_name = data.get('channel_name', '')

        # Ігнорувати повідомлення від бота
        if data.get('bot_id'):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{}')
            return

        # Обробка команд
        response_text = self._handle_message(user_id, user_name, text, channel_name)

        response_body = json.dumps({
            "text": response_text,
            "response_type": "in_channel" if text.startswith('/') else "in_channel"
        }).encode('utf-8')

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(response_body))
        self.end_headers()
        self.wfile.write(response_body)

    def _handle_message(self, user_id, user_name, text, channel) -> str:
        # Спеціальні команди
        lower = text.lower()

        if lower in ['/start', '/старт', 'привіт', 'hello', '/help', '/допомога']:
            return f"""👋 Привіт, @{user_name}! Я — **ASD Onboarding Bot** 🤖

Я знаю все про #ASDTeam і допоможу тобі освоїтись:

**Що я вмію:**
- Відповідати на питання про компанію, процеси, інструменти
- Пояснити як користуватись ASD Reporter, Notion, Mattermost
- Розповісти про бенефіти та правила

**Корисні команди:**
- `/checklist` — чеклист першого дня
- `/roadmap` — план на 3 місяці
- `/contacts` — контакти команди
- `/links` — посилання на Notion

Або просто пиши мені будь-яке питання! 😊"""

        elif lower in ['/checklist', '/чеклист']:
            return """📋 **Чеклист нового працівника**
*(всю інформацію надсилати Богдані в Mattermost)*

**1. Фото та профіль**
- Поставити впізнаване фото на аватар в Mattermost
- Надіслати фото HR (для Employee Directory)

**2. Документи**
- Заповнити [NDA договір](https://www.notion.so/ASD-Home-710107f8bc2a42daaf7f7635c2591bf7) та надіслати HR
- Надати копії паспорту та ідентифікаційного коду
- Заповнити CV компанії

**3. Технічне**
- Написати розмір футболки (S/M/L...)
- Реквізити для відправки посилки Нова Пошта

**4. Перший тиждень**
- Заповнити анкету в [Notion](https://www.notion.so/ASD-Home-710107f8bc2a42daaf7f7635c2591bf7)"""

        elif lower in ['/roadmap', '/роадмап']:
            return """🗺 **Roadmap онбордингу**

**День 1:**
- Welcome meeting з HR (Юлія / Богдана)
- Зустріч з PM / ментором
- Заповнити чеклист

**Тиждень 1:**
- Заповнення анкети в [Notion](https://www.notion.so/ASD-Home-710107f8bc2a42daaf7f7635c2591bf7)
- Налаштувати всі інструменти

**1 місяць:** Зустріч з HR перед проміжним фідбеком
**1.5 місяці:** Проміжний feedback (PM, TL, HR)
**2.5 місяці:** Зустріч з HR перед кінцем випробувального терміну
**3 місяці:** Закінчення випробувального терміну ✅"""

        elif lower in ['/contacts', '/контакти']:
            return """👥 **Контакти команди ASD**

**Керівництво:**
- **Бойко Павло** — CEO (Засновник)
- **Соловйова Ольга** — COO

**HR команда:**
- **Джобулда Юлія** — Head of HR (есесменти)
- **Богдана Басараба** — HRA (твоя перша точка контакту!)

**Підтримка:**
- **Трефаненко Дмитро** — Офіс-менеджер (техніка)
- **Трефаненко Ірина** — Корпоративний лікар
- **Оксана Пендерецька** — Корпоративний психолог
- **Ірина Сапожник** — Викладач англійської
- **Юлія Одинак** — Фінансист (ФОП, податки)

📧 Email: hrasdteam@gmail.com
🌐 Сайт: https://asd.team/"""

        elif lower in ['/links', '/посилання']:
            return """🔗 **Корисні посилання Notion**

- [🏠 ASD Home](https://www.notion.so/ASD-Home-710107f8bc2a42daaf7f7635c2591bf7) — головний хаб
- [💻 Техніка та ПЗ](https://www.notion.so/Software-f2e839672460432188164879005ec08f)
- [💬 Feedbacks](https://www.notion.so/Feedbacks-c6b54977a19f44d5b2eca7632035d072)
- [✈️ Відрядження](https://www.notion.so/3a1aeac68ad74231af72c9040d997a85)
- [📊 Ladders](https://www.notion.so/Ladders-d6022381305e479cb0a5a3a71dc17f93)
- [🎯 Assessment flow](https://www.notion.so/Assessment-level-up-flow-4cc50edc9bb4402993487adac5c16f77)
- [🔄 Delivery Flow](https://www.notion.so/Delivery-Flow-165adb762c6f41e098c51e771ad05a45)
- [🤖 AI Policy](https://www.notion.so/AI-policy-2639415244c280ffb6b7e36f85e6b25b)
- [🚪 Offboarding](https://www.notion.so/offboarding-78d836122d7a4f6db52251b0ac8f4fc2)"""

        else:
            # AI відповідь
            try:
                return get_ai_response(user_id, text)
            except Exception as e:
                return f"⚠️ Вибач, сталась помилка. Спробуй ще раз або звернись до HR: hrasdteam@gmail.com\n\nПомилка: {str(e)}"

    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")


# ──────────────────────────────────────────────
# ПЛАНУВАЛЬНИК НАГАДУВАНЬ
# ──────────────────────────────────────────────
new_employees = {}  # user_id -> {"start_date": date, "mattermost_url": str, "bot_token": str}

def schedule_reminders(user_id: str, mattermost_url: str, bot_token: str):
    """Запланувати нагадування для нового співробітника."""
    new_employees[user_id] = {
        "start_date": datetime.now().date(),
        "mattermost_url": mattermost_url,
        "bot_token": bot_token
    }
    print(f"[REMINDERS] Scheduled reminders for user {user_id}")

def send_reminder(user_id: str, day: int, mattermost_url: str, bot_token: str):
    """Надіслати нагадування через Mattermost API."""
    import urllib.request
    text = WEEKLY_REMINDERS.get(day)
    if not text:
        return

    payload = json.dumps({
        "channel_id": user_id,  # Direct message
        "message": text
    }).encode('utf-8')

    req = urllib.request.Request(
        f"{mattermost_url}/api/v4/posts",
        data=payload,
        headers={
            "Authorization": f"Bearer {bot_token}",
            "Content-Type": "application/json"
        }
    )
    try:
        urllib.request.urlopen(req)
        print(f"[REMINDERS] Sent day {day} reminder to {user_id}")
    except Exception as e:
        print(f"[REMINDERS] Error sending reminder: {e}")

def reminder_scheduler():
    """Фонова задача для перевірки та надсилання нагадувань."""
    import time
    while True:
        today = datetime.now().date()
        for user_id, info in list(new_employees.items()):
            days_since_start = (today - info["start_date"]).days + 1
            if 1 <= days_since_start <= 5:
                send_reminder(user_id, days_since_start,
                              info["mattermost_url"], info["bot_token"])
                if days_since_start == 5:
                    del new_employees[user_id]
        time.sleep(86400)  # Перевіряти раз на добу


# ──────────────────────────────────────────────
# ЗАПУСК
# ──────────────────────────────────────────────
if __name__ == "__main__":
    if not ANTHROPIC_API_KEY:
        print("❌ Потрібна змінна ANTHROPIC_API_KEY")
        exit(1)

    # Запуск планувальника нагадувань у фоні
    reminder_thread = threading.Thread(target=reminder_scheduler, daemon=True)
    reminder_thread.start()

    print(f"🚀 ASD Onboarding Bot запущено на порту {PORT}")
    print(f"📡 Webhook URL: http://your-server:{PORT}/webhook")

    server = HTTPServer(('0.0.0.0', PORT), MattermostWebhookHandler)
    server.serve_forever()
