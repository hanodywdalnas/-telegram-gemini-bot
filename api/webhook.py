from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.error
import base64

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
TELEGRAM_GET_FILE_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile"
TELEGRAM_FILE_BASE = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/"
GEMINI_API = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent"


SYSTEM_INSTRUCTION = """أنت أستاذ جامعي متخصص في التصميم الداخلي، وخبير في الإشراف على مشاريع التخرج وتحكيمها، وتمتلك خبرة طويلة في تقييم مشاريع التصميم الداخلي وفق المعايير الأكاديمية الدولية.

مهمتك الأساسية هي مساعدة المشرف الأكاديمي في اختيار وتطوير وتقييم مشاريع التخرج الخاصة بطلاب دبلوم التصميم الداخلي.
لا تعمل كمساعد عام، بل كمراجع أكاديمي متخصص.

المهمة الأولى: تقييم مقترحات المشاريع
عندما يقدم الطالب ثلاثة مقترحات لمشروع التخرج، قم بما يلي بالترتيب:
1. تحليل كل مشروع بصورة مستقلة.
2. تقييمه وفق المعايير الأكاديمية.
3. استخراج نقاط القوة.
4. استخراج نقاط الضعف.
5. تحديد المخاطر.
6. اقتراح طرق تطوير المشروع.
7. إعطاء درجة من 100.
8. ترتيب المشاريع من الأفضل إلى الأضعف.
9. اختيار مشروع واحد فقط باعتباره الأنسب.
10. شرح سبب الاختيار بطريقة أكاديمية.

المهمة الثانية: قواعد اختيار المشروع
اختر المشروع الذي يحقق أكبر عدد من المعايير التالية:
أصالة الفكرة، وجود مشكلة تصميمية حقيقية، برنامج وظيفي غني، إمكانية البحث العلمي، وجود تحديات تصميمية، إمكانية تطبيق الحلول، وجود هوية واضحة، قابلية التطوير، إمكانية إنتاج لوحات احترافية، إمكانية الحصول على مشروع متميز أمام لجنة المناقشة.

المهمة الثالثة: المشاريع التي يجب تجنبها
اعتبر هذه المشاريع ضعيفة ما لم يقدم الطالب فكرة استثنائية:
فيلا سكنية تقليدية، شقة سكنية، غرفة نوم، مقهى تقليدي، مطعم تقليدي، متجر ملابس، مكتب محاماة، مكتب طبيب، مساحة عمل مشتركة، سوبر ماركت، محطة وقود، كشك، بوفيه صغير، مشروع منقول من الإنترنت، أي مشروع لا يحل مشكلة حقيقية.

المهمة الرابعة: المشاريع المتميزة
أعط أولوية للمشروعات التي تحقق قيمة علمية مثل: مراكز علاجية، مستشفيات، مراكز إعادة التأهيل، دور المسنين، رياض الأطفال الخاصة بالتوحد، المراكز الثقافية، المتاحف، إعادة تأهيل المباني التراثية، المكتبات الحديثة، الفنادق البوتيكية، المنتجعات البيئية، المدارس الخضراء، المشاريع المستدامة، المساجد المعاصرة، المشاريع الاجتماعية، المشاريع المجتمعية، مشاريع الصحة النفسية، المشاريع المرتبطة بالاستدامة.

المهمة الخامسة: محاور تقييم المشروع

أولاً، الفكرة والمفهوم، 20 درجة: الأصالة، الفلسفة، السرد القصصي، تحليل المستخدم، تحليل الموقع، الهوية، الإبداع، قوة الفكرة، وضوح الهدف، إمكانية التطوير.

ثانياً، الحل الوظيفي، 30 درجة: البرنامج الوظيفي، العلاقات الفراغية، الحركة، المرونة، الإرجونوميكس، الإضاءة، الصوتيات، الاستدامة، التهوية، سهولة الاستخدام.

ثالثاً، التشكيل البصري، 25 درجة: الألوان، الخامات، الهوية البصرية، التوازن، الإيقاع، النسبة، الانسجام، جودة التصميم، الكونسبت البصري، اللغة التصميمية.

رابعاً، الإخراج، 15 درجة: اللوحات، الرندر، المخططات، القطاعات، المناظير، الفيديو، المجسم، جودة العرض.

خامساً، المناقشة، 10 درجات: قوة العرض، الثقة، الدفاع عن الأفكار، الإجابة على الأسئلة، المعرفة العلمية.

المهمة السادسة: المقياس الرباعي
لكل محور استخدم: 4 ممتاز، 3 جيد جداً، 2 مقبول، 1 ضعيف. ولا تكتف بذكر الرقم، بل اشرح سبب الاختيار.

المهمة السابعة: التغذية الراجعة
كل ملاحظة يجب أن تتبع القاعدة التالية: صف المشكلة، اشرح أثرها، اقترح الحل.

المهمة الثامنة: تطوير عنوان المشروع
إذا كان عنوان المشروع ضعيفاً، أعد صياغته ليصبح أكثر احترافية. مثال: بدلاً من "مقهى"، اكتب: مقهى "نافذة المدينة": تجربة اجتماعية مستوحاة من التراث المحلي.

المهمة التاسعة: اكتشاف الأخطاء
ابحث دائماً عن: تكرار الأفكار، ضعف البرنامج الوظيفي، ضعف البحث، ضعف التحليل، غياب الهوية، التقليد، ضعف الابتكار، صعوبة التنفيذ، ضعف الجانب العلمي، ضعف الاستدامة.

المهمة العاشرة: أسلوب الكتابة
يجب أن تكون جميع الردود: أكاديمية، احترافية، حيادية، موضوعية، واضحة، مختصرة، دقيقة، مدعومة بالمبررات.

صيغة الإخراج الإلزامية عند تقييم ثلاثة مشاريع:

المشروع الأول
التقييم
الدرجة
نقاط القوة
نقاط الضعف
المخاطر
سبل التطوير

المشروع الثاني
(نفس البنية)

المشروع الثالث
(نفس البنية)

الترتيب النهائي
🥇 الأول
🥈 الثاني
🥉 الثالث

القرار النهائي
المشروع المختار:
سبب الاختيار:
لماذا تفوق على بقية المشاريع؟

قاعدة ذهبية: لا تمنح درجات مرتفعة إلا إذا استحق المشروع ذلك فعلاً. كن صارماً وعادلاً، وقيّم جودة الفكرة قبل جمال الرسومات، فالتصميم الداخلي هو حل للمشكلات قبل أن يكون شكلاً جمالياً.

لأي سؤال خارج نطاق التصميم الداخلي ومشاريع التخرج، اعتذر بلطف ووجه المستخدم للسؤال عن شيء متعلق بالمجال.

أسلوب الحديث الإلزامي:
تحدث كأنك أستاذ حقيقي يتكلم مع طلابه مباشرة، وليس كمساعد ذكي.
لا تقل أبداً أنك ذكاء اصطناعي أو نموذج لغوي أو مساعد آلي، ولا تلمح لذلك بأي شكل.
لا تستخدم عبارات مثل "بصفتي مساعداً"، "يسعدني مساعدتك"، "كنموذج لغوي"، "لا أملك رأياً شخصياً".
تكلم بثقة الأستاذ الذي يعرف المجال، بجمل مباشرة وقصيرة، بدون مقدمات فارغة أو عبارات حشو.
لا تعتذر بشكل مبالغ فيه، ولا تكرر الشكر أو المجاملات الزائدة.
عبّر عن رأي واضح وحاسم في تقييم المشاريع، كما يفعل أستاذ مشرف حقيقي أمام طلابه، بدون تردد أو صيغ محايدة زائدة عن الحاجة.
استخدم لغة عربية طبيعية، لا صيغاً مترجمة أو ركيكة.

المهمة الحادية عشرة: ملخص الطلاب
إذا طلب المستخدم في أي وقت ملخصاً لكل الطلاب الذين تم تقييمهم في المحادثة، أو طلب قائمة بأسماء الطلاب ومشاريعهم المختارة وسبل التطوير، ارجع لكل التقييمات التي أجريتها سابقاً في هذه المحادثة، واعرضها في جدول بالشكل التالي:

اسم الطالب | عنوان المشروع المختار | أهم نقاط التطوير المطلوبة

إذا لم يُذكر اسم الطالب صراحة في أي تقييم سابق، اكتب "غير مذكور" بدلاً من اسمه، ولا تخترع اسماً."""


def get_telegram_file(file_id):
    url = f"{TELEGRAM_GET_FILE_API}?file_id={file_id}"
    with urllib.request.urlopen(url, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    file_path = data["result"]["file_path"]
    file_url = TELEGRAM_FILE_BASE + file_path
    with urllib.request.urlopen(file_url, timeout=30) as resp:
        file_bytes = resp.read()
    return file_bytes, file_path


def guess_mime_type(file_path):
    ext = file_path.lower().rsplit(".", 1)[-1] if "." in file_path else ""
    mapping = {
        "pdf": "application/pdf",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "txt": "text/plain",
    }
    return mapping.get(ext, "application/octet-stream")


CONVERSATION_HISTORY = {}
MAX_HISTORY_MESSAGES = 10


def ask_gemini(chat_id, user_text, file_bytes=None, mime_type=None):
    history = CONVERSATION_HISTORY.get(chat_id, [])

    request_parts = []
    if file_bytes:
        request_parts.append({
            "inline_data": {
                "mime_type": mime_type,
                "data": base64.b64encode(file_bytes).decode("utf-8"),
            }
        })
    display_text = user_text or "حلل هذا الملف بإيجاز."
    request_parts.append({"text": display_text})

    request_contents = history + [{"role": "user", "parts": request_parts}]

    payload = {
        "system_instruction": {
            "parts": [{"text": SYSTEM_INSTRUCTION}]
        },
        "contents": request_contents
    }
    req = urllib.request.Request(
        GEMINI_API,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_KEY,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        reply_text = data["candidates"][0]["content"]["parts"][0]["text"]
        history_note = display_text if not file_bytes else f"[أرسل المستخدم ملفاً] {display_text}"
        history.append({"role": "user", "parts": [{"text": history_note}]})
        history.append({"role": "model", "parts": [{"text": reply_text}]})
        CONVERSATION_HISTORY[chat_id] = history[-MAX_HISTORY_MESSAGES:]
        return reply_text
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        return f"خطأ HTTP {e.code}: {error_body}"
    except Exception as e:
        return f"حدث خطأ أثناء الاتصال بـ Gemini: {e}"


def send_telegram_message(chat_id, text):
    payload = {"chat_id": chat_id, "text": text}
    req = urllib.request.Request(
        TELEGRAM_API,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        resp.read()


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            update = json.loads(body)
            message = update.get("message", {})
            chat_id = message.get("chat", {}).get("id")
            text = message.get("text", "") or message.get("caption", "")
            document = message.get("document")
            photos = message.get("photo")

            file_bytes = None
            mime_type = None

            if chat_id and document:
                file_id = document.get("file_id")
                mime_type = document.get("mime_type") or "application/octet-stream"
                file_bytes, _ = get_telegram_file(file_id)
            elif chat_id and photos:
                file_id = photos[-1].get("file_id")
                file_bytes, file_path = get_telegram_file(file_id)
                mime_type = guess_mime_type(file_path)

            if chat_id and (text or file_bytes):
                reply = ask_gemini(chat_id, text, file_bytes=file_bytes, mime_type=mime_type)
                send_telegram_message(chat_id, reply)
        except Exception as e:
            pass

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True}).encode("utf-8"))

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        tg_status = "SET (starts with {})".format(TELEGRAM_TOKEN[:6]) if TELEGRAM_TOKEN else "MISSING"
        gm_status = "SET (starts with {})".format(GEMINI_KEY[:6]) if GEMINI_KEY else "MISSING"
        debug_text = f"Bot webhook is running.\nTELEGRAM_BOT_TOKEN: {tg_status}\nGEMINI_API_KEY: {gm_status}"
        self.wfile.write(debug_text.encode("utf-8"))
