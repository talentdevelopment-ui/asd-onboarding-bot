"""
ASD Team Onboarding Bot for Mattermost
Google Gemini API — безкоштовно до 1500 запитів/день
Змінні середовища: GEMINI_API_KEY, MATTERMOST_TOKEN
"""

import os, json, urllib.request, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

GEMINI_API_KEY   = os.environ.get("GEMINI_API_KEY", "")
MATTERMOST_TOKEN = os.environ.get("MATTERMOST_TOKEN", "")
PORT = int(os.environ.get("PORT", 10000))

SYSTEM_PROMPT = """Ти — офіційний AI-помічник для онбордингу нових співробітників компанії ASD Team (Advanced Software Development), Чернівці, Україна.

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

CHECKLIST (надсилати через Mattermost HRA Богдані):
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

MATTERMOST КАНАЛИ: Town Square, Off-Topic, Our_team, Company Important Info, Volunteering, ASD Well-being, Talent development

ASD REPORTER: Time off, Vacation, Sick day (довідка НЕ потрібна; стоматолог = відгул!), Overtime, Business trip, Extended leave. Коментарі — англійською.

BENEFITS: 15 р.д. відпустки, безлімітний лікарняний, гнучкий графік, щорічний перегляд зарплати, well-being програма, навчання за рахунок компанії.

ПРАВИЛА: відповідай українською, стисло (3-4 абзаци), з посиланнями на Notion, дружньо. Якщо не знаєш — направ до hrasdteam@gmail.com або Богдани."""

WEEKLY_REMINDERS = {
    1: "👋 **День 1 — Welcome day!**\n\n- ✅ Welcome meeting з HR (Юлія / Богдана)\n- ✅ Зустріч з PM / ментором\n- ✅ Поставити аватар у Mattermost\n- ✅ Надіслати фото Богдані (для Employee Directory)\n- ✅ [Onboarding book в Notion](https://www.notion.so/ASD-Home-710107f8bc2a42daaf7f7635c2591bf7)\n\nПитання? Пиши мені! 🤖",
    2: "📋 **День 2 — Документи**\n\n- ✅ Підписати NDA та надіслати HR\n- ✅ Копії паспорту та ідентифікаційного коду\n- ✅ Заповнити CV компанії\n- ✅ Розмір футболки + реквізити Нової Пошти\n- ℹ️ Все → Богдані в особисті в Mattermost",
    3: "⏱ **День 3 — ASD Reporter**\n\n- ✅ Увійти в ASD Reporter\n- ✅ Перший Worklog (щодня обов'язково!)\n- ✅ Відкрити Google Calendar для колег\n- ✅ Підтверджувати запрошення на мітинги\n- ℹ️ Коментарі в Reporter — **англійською**",
    4: "📚 **День 4 — Notion ASD Home**\n\n- ✅ [ASD Home](https://www.notion.so/ASD-Home-710107f8bc2a42daaf7f7635c2591bf7) — всі розділи\n- ✅ Employee Directory — знайди себе та колег\n- ✅ Mission, Vision, Values\n- ✅ [AI Policy](https://www.notion.so/AI-policy-2639415244c280ffb6b7e36f85e6b25b)\n- ✅ Well-being program",
    5: "🚀 **День 5 — Фінал першого тижня!**\n\n- ✅ [Ladders](https://www.notion.so/Ladders-d6022381305e479cb0a5a3a71dc17f93) — матриці компетенцій\n- ✅ [Assessment flow](https://www.notion.so/Assessment-level-up-flow-4cc50edc9bb4402993487adac5c16f77)\n- ✅ [Delivery Flow](https://www.notion.so/Delivery-Flow-165adb762c6f41e098c51e771ad05a45)\n- ✅ Заповнити анкету в Notion\n\n🎉 Вітаємо з першим тижнем в #ASDTeam!"
}

conversation_history = {}

def get_gemini_response(user_id, user_message):
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    conversation_history[user_id].append({"role": "user", "parts": [{"text": user_message}]})
    if len(conversation_history[user_id]) > 10:
        conversation_history[user_id] = conversation_history[user_id][-10:]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = json.dumps({
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": conversation_history[user_id],
        "generationConfig": {"maxOutputTokens": 800, "temperature": 0.7}
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    reply = data["candidates"][0]["content"]["parts"][0]["text"]
    conversation_history[user_id].append({"role": "model", "parts": [{"text": reply}]})
    return reply

class MattermostHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.send_header("Content-Type","text/plain"); self.end_headers()
        self.wfile.write(b"ASD Onboarding Bot is running!")

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        try: data = json.loads(body.decode("utf-8"))
        except: self._r(400,"{}"); return
        if MATTERMOST_TOKEN and data.get("token") != MATTERMOST_TOKEN: self._r(403,"{}"); return
        if data.get("bot_id") or data.get("user_name") == "onboarding-bot": self._r(200,"{}"); return
        user_id = data.get("user_id","unknown")
        user_name = data.get("user_name","colleague")
        text = data.get("text","").strip()
        for m in ["@onboarding-bot","@bot"]: text = text.replace(m,"").strip()
        if not text: self._r(200,"{}"); return
        reply = self._handle(user_id, user_name, text)
        self._r(200, json.dumps({"text": reply, "response_type": "in_channel"}))

    def _r(self, code, body):
        b = body.encode() if isinstance(body,str) else body
        self.send_response(code); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",len(b)); self.end_headers(); self.wfile.write(b)

    def _handle(self, user_id, user_name, text):
        lower = text.lower().strip()
        if lower in ["привіт","hello","/start","/help","/допомога","старт"]:
            return f"👋 Привіт, @{user_name}! Я — **ASD Onboarding Bot** 🤖\n\nЗнаю все про #ASDTeam!\n\n**Команди:**\n- `/checklist` — чеклист першого дня\n- `/roadmap` — план на 3 місяці\n- `/contacts` — контакти команди\n- `/links` — посилання на Notion\n\nАбо просто пиши будь-яке питання 😊"
        if lower in ["/checklist","/чеклист"]:
            return "📋 **Чеклист нового працівника**\n*(надсилати Богдані в Mattermost)*\n\n**1. Фото**\n- Аватар у Mattermost\n- Фото для Employee Directory\n\n**2. Документи**\n- [NDA договір](https://www.notion.so/ASD-Home-710107f8bc2a42daaf7f7635c2591bf7) → підписати та надіслати HR\n- Копії паспорту та ідентифікаційного коду\n- CV компанії\n\n**3. Інше**\n- Розмір футболки (S/M/L...)\n- Реквізити Нової Пошти\n\n**4. Тиждень 1**\n- [Анкета в Notion](https://www.notion.so/ASD-Home-710107f8bc2a42daaf7f7635c2591bf7)"
        if lower in ["/roadmap","/роадмап"]:
            return "🗺 **Roadmap онбордингу**\n\n**День 1:** Welcome meeting з HR + зустріч з PM + чеклист\n**Тиждень 1:** Анкета в Notion + налаштування інструментів\n**1 місяць:** Зустріч з HR перед проміжним фідбеком\n**1.5 місяці:** Проміжний feedback (PM, TL, HR)\n**2.5 місяці:** Зустріч з HR перед кінцем випробувального терміну\n**3 місяці:** Закінчення випробувального терміну ✅"
        if lower in ["/contacts","/контакти"]:
            return "👥 **Контакти ASD Team**\n\n- **Бойко Павло** — CEO\n- **Соловйова Ольга** — COO\n- **Джобулда Юлія** — Head of HR\n- **Богдана Басараба** — HRA *(перша точка контакту!)*\n- **Трефаненко Дмитро** — Офіс-менеджер\n- **Трефаненко Ірина** — Корпоративний лікар\n- **Оксана Пендерецька** — Психолог\n- **Ірина Сапожник** — Викладач англійської\n- **Юлія Одинак** — Фінансист\n\n📧 hrasdteam@gmail.com | 🌐 https://asd.team/"
        if lower in ["/links","/посилання"]:
            return "🔗 **Посилання Notion**\n\n- [🏠 ASD Home](https://www.notion.so/ASD-Home-710107f8bc2a42daaf7f7635c2591bf7)\n- [💻 Техніка та ПЗ](https://www.notion.so/Software-f2e839672460432188164879005ec08f)\n- [💬 Feedbacks](https://www.notion.so/Feedbacks-c6b54977a19f44d5b2eca7632035d072)\n- [✈️ Відрядження](https://www.notion.so/3a1aeac68ad74231af72c9040d997a85)\n- [📊 Ladders](https://www.notion.so/Ladders-d6022381305e479cb0a5a3a71dc17f93)\n- [🎯 Assessment flow](https://www.notion.so/Assessment-level-up-flow-4cc50edc9bb4402993487adac5c16f77)\n- [🔄 Delivery Flow](https://www.notion.so/Delivery-Flow-165adb762c6f41e098c51e771ad05a45)\n- [🤖 AI Policy](https://www.notion.so/AI-policy-2639415244c280ffb6b7e36f85e6b25b)\n- [🚪 Offboarding](https://www.notion.so/offboarding-78d836122d7a4f6db52251b0ac8f4fc2)"
        try:
            return get_gemini_response(user_id, text)
        except Exception as e:
            print(f"[ERROR] {e}")
            return "⚠️ Вибач, не вдалось відповісти. Спробуй ще раз або звернись до HR: hrasdteam@gmail.com"

    def log_message(self, fmt, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {fmt % args}")

new_employees = {}

def schedule_reminders(user_id, mm_url, bot_token, dm_channel):
    new_employees[user_id] = {"start_date": datetime.now().date(), "mm_url": mm_url, "bot_token": bot_token, "dm_channel": dm_channel}

def _reminder_loop():
    import time
    while True:
        today = datetime.now().date()
        for uid, info in list(new_employees.items()):
            day = (today - info["start_date"]).days + 1
            if 1 <= day <= 5:
                try:
                    payload = json.dumps({"channel_id": info["dm_channel"], "message": WEEKLY_REMINDERS[day]}).encode()
                    req = urllib.request.Request(f"{info['mm_url']}/api/v4/posts", data=payload, headers={"Authorization": f"Bearer {info['bot_token']}", "Content-Type": "application/json"})
                    urllib.request.urlopen(req, timeout=10)
                except Exception as e:
                    print(f"[REMIND] Error: {e}")
            if day > 5:
                del new_employees[uid]
        time.sleep(86400)

if __name__ == "__main__":
    if not GEMINI_API_KEY:
        print("Потрібна змінна GEMINI_API_KEY — отримай на https://aistudio.google.com"); exit(1)
    threading.Thread(target=_reminder_loop, daemon=True).start()
    print(f"ASD Onboarding Bot (Gemini) запущено на порту {PORT}")
    HTTPServer(("0.0.0.0", PORT), MattermostHandler).serve_forever()
