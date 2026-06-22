from aiogram import Router
from keyboards.reply import explanations, menu

router = Router()

# ========================= الشروحات =========================
from aiogram.types import CallbackQuery

@router.callback_query(lambda c: c.data == "menu_tutorials")
async def tutorials(c: CallbackQuery):
    
    # نقوم بتعديل نص الرسالة الحالية ونعرض أزرار الشروحات ليكون التنقل سلس جداً دون تكرار الرسائل
    await c.message.edit_text(
        text='📚 *الرجاء اختيار الشرح المناسب من القائمة أدناه:*',
        parse_mode="Markdown",
        reply_markup=explanations  # كيبورد الشروحات الـ Inline الذي يحتوي على (explanations_0, explanations_1... إلخ)
    )
    
    # إنهاء حالة التحميل للزر في تلغرام
    await c.answer()

@router.callback_query(lambda c: c.data == "explanations_0")
async def process_what_is_ichancy(c: CallbackQuery):
    
    text = """📚 *ما هو موقع Ichancy؟*

موقع Ichancy هو منصة ترفيهية متكاملة تُقدم خدمات المراهنات الرياضية، ألعاب السلوت، ألعاب الكازينو، وألعاب متنوعة (Games)، مع نظام آلي لحساب الأرباح بناءً على النسب المرتبطة بكل خيار.

🔹 *أقسام الموقع:*

1️⃣ *الرياضة (Sports):*
يتيح للمستخدمين المراهنة على مجموعة واسعة من الأحداث الرياضية، مثل كرة القدم، كرة السلة، التنس وغيرها، مع خيارات متعددة ونسب متغيرة.
💡 _آلية العمل:_ يختار المراهن خيارًا رياضيًا واحدًا أو أكثر قبل بدء الحدث. تُضرب النسبة المحددة (Odds) في مبلغ الرهان لتحديد العائد المحتمل.

2️⃣ *السلوت (Slot):*
ألعاب الحظ الممتعة برسومات جذابة وآليات دوران بسيطة، حيث يمكن للمستخدم تجربة حظه والفوز بمكافآت فورية.

3️⃣ *الكازينو (Casino):*
مجموعة متنوعة من ألعاب الكازينو التقليدية مثل الروليت، البلاك جاك، البوكر، وغيرها، ضمن تجربة محاكاة احترافية.

4️⃣ *الألعاب (Games):*
يضم هذا القسم ألعابًا إلكترونية وتفاعلية مسلية (مثل Crash و Rocketon و Golden Tree وغيرها).

🌐 *لزيارة الموقع الرسمي:* [اضغط هنا](https://ichancy.com)"""

    # استخدام edit_message_text لتعديل نفس الرسالة بدل إرسال رسالة جديدة (أجمل للمستخدم)
    await c.message.edit_text(text, parse_mode="Markdown", disable_web_page_preview=True)
    
    # ضروري جداً تنهي الكولباك عشان تختفي علامة الساعة الرملية من الزر في تلغرام
    await c.answer()


@router.callback_query(lambda c: c.data == "explanations_1")
async def process_bot_recharge_tutorial(c: CallbackQuery):
    
    text = """💰 *كيفية شحن الرصيد ضمن بوت Ichancy*

يرجى اتباع الخطوات التالية لإتمام عملية شحن الرصيد بنجاح:

1️⃣ اضغط على خيار *「 شحن رصيد 」* في القائمة الرئيسية للبوت.
2️⃣ اختر طريقة الدفع المناسبة لك من بين الخيارات المتاحة (سيريتل كاش، USDT، إلخ).
3️⃣ قم بإرسال المبلغ الذي ترغب في شحنه إلى الرقم أو العنوان المخصّص المظهر لك.
⚠️ _ملاحظة:_ أقل مبلغ يمكن شحنه هو 1 دولار أمريكي (أو ما يعادله بالعملة المحلية).
4️⃣ بعد إتمام التحويل، أدخل كود عملية التحويل (رقم المعاملة)، ثم أدخل قيمة المبلغ المرسل بدقة.

✅ بعد مراجعة النظام للعملية، سيتم شحن حسابك في البوت بنجاح!"""

    # تعديل الرسالة الحالية لإظهار الشرح
    await c.message.edit_text(text, parse_mode="Markdown")
    
    # إنهاء حالة التحميل للزر
    await c.answer()


@router.callback_query(lambda c: c.data == "explanations_3")
async def process_bot_withdraw_tutorial(c: CallbackQuery):
    text = """💳 *كيفيّة سحب الرصيد من بوت Ichancy*

لإتمام عملية السحب بنجاح، يرجى اتباع الخطوات التالية:

1️⃣ اضغط على خيار *「 سحب رصيد 」* من واجهة البوت الرئيسية.
2️⃣ اختر طريقة السحب المناسبة لك من بين الوسائل المتاحة (سيريتل كاش، إلخ).
3️⃣ أدخل بياناتك المطلوبة (مثل رقم الحساب أو المحفظة) بدقة بحسب الطريقة المختارة.
4️⃣ أدخل المبلغ الذي ترغب بسحبه.

✅ *تم تقديم طلب السحب بنجاح!*
⏳ يتم معالجة طلب السحب وتحويل الأموال خلال مدة أقصاها نصف ساعة."""

    await c.message.edit_text(text, parse_mode="Markdown")
    await c.answer()



@router.callback_query(lambda c: c.data == "explanations_4")
async def process_site_recharge_tutorial(c: CallbackQuery):
    text = """🔄 *كيفية شحن رصيد ضمن حساب Ichancy (الموقع)*

لشحن رصيد إلى حسابك في موقع Ichancy عبر البوت، يرجى اتباع الخطوات التالية:

1️⃣ اضغط على خيار *「 Ichancy 」* في واجهة البوت الرئيسية.
2️⃣ اختر *「 شحن حساب Ichancy 」*.
3️⃣ أدخل معرّف الحساب (ID) أو اسم المستخدم الخاص بحساب Ichancy الذي ترغب بشحنه.
4️⃣ أدخل المبلغ المطلوب شحنه بالليرة السوريّة.
5️⃣ انتظر حوالي 15 ثانية حتى تتم معالجة العملية آلياً.

✅ *تم شحن حساب الموقع بنجاح!*"""

    await c.message.edit_text(text, parse_mode="Markdown")
    await c.answer()


@router.callback_query(lambda c: c.data == "explanations_5")
async def process_site_withdraw_tutorial(c: CallbackQuery):
    text = """💸 *كيفية سحب رصيد من حساب Ichancy (الموقع)*

لسحب رصيد من حسابك في موقع Ichancy وتنزيله في البوت، يرجى اتباع التالي:

1️⃣ اضغط على خيار *「 Ichancy 」* في واجهة البوت الرئيسية.
2️⃣ اختر *「 سحب رصيد من حساب Ichancy 」*.
3️⃣ أدخل معرّف الحساب (ID) أو اسم المستخدم الخاص بحساب Ichancy للتحقق.
4️⃣ أدخل المبلغ المطلوب سحبه بالدولار ($).
5️⃣ انتظر حوالي 15 ثانية حتى تنتهي المعالجة وتحديث الرصيد.

✅ *تم سحب الرصيد من الحساب بنجاح!*"""

    await c.message.edit_text(text, parse_mode="Markdown")
    await c.answer()


@router.callback_query(lambda c: c.data == "explanations_6")
async def process_back_to_main_menu(c: CallbackQuery):
    # هون بنحذف رسالة الشروحات القديمة وبنرسل رسالة القائمة الرئيسية الجديدة مع الكيبورد (menu)
    await c.message.delete()
    await c.message.answer("🔙 تم العودة إلى القائمة الرئيسية", reply_markup=menu)
    await c.answer()

