from aiogram import types, Router, F  # تم استيراد F لاستخدامه كفلتر متقدم وآمن
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# استيراد الحوض والدوال بنظام الأسنك
from database.db import (
    add_balance,
    add_transaction,
    process_deposit_commission,
    get_deposit_bonus_rate,
    check_and_add_pending_deposit,
    fetch_and_delete_pending,
    delete_pending_only,
    get_sy_code_from_db,
    get_sh_code_from_db
)

from config import GROUP_ID

class SyriatelState(StatesGroup):
    process = State()
    amount = State()

class ShamCashState(StatesGroup):
    process = State()
    amount = State()

router = Router()

# ========================= شحن رصيد =========================
@router.callback_query(lambda c: c.data == "menu_bot_recharge")
async def deposit(c: CallbackQuery):
    
    # تحويل خيارات الشحن إلى كيبورد Inline
    deposit_bot_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📱 سيرياتيل كاش", callback_data="pay_syriatel"),
                InlineKeyboardButton(text="💳 شام كاش", callback_data="pay_sham")
            ],
            [
                InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="back_to_main")
            ]
        ]
    )
    
    # تعديل الرسالة الحالية فوراً
    await c.message.edit_text(
        text="💳 *شحن رصيد في البوت*\n\nيرجى اختيار طريقة الدفع المناسبة لك من الأزرار أدناه للبدء في عملية الشحن:",
        parse_mode="Markdown",
        reply_markup=deposit_bot_kb
    )
    
    # إنهاء حالة التحميل على الزر
    await c.answer()

# ========================= سيرياتيل كاش =========================
@router.callback_query(lambda c: c.data == "pay_syriatel")
async def syriatelcashD(c: CallbackQuery, state: FSMContext):
    await state.clear()  # تصفية أي حالات سابقة لتفادي التعليق الافتراضي
    
    # كيبورد بسيط للعودة في حال أراد المستخدم التراجع
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ إلغاء والعودة للقائمة", callback_data="back_to_main")]
    ])
    
    # تحديث الرسالة الحالية بعرض الأرقام وتوجيه المستخدم
    current_text = await get_sy_code_from_db()
    
    # تحديث الرسالة الحالية بعرض الأرقام وتوجيه المستخدم
    await c.message.edit_text(
        text="📱 *شحن عبر سيرياتيل كاش*\n\n"
             "يرجى تحويل المبلغ المطلوب إلى أحد الأرقام المتاحة أدناه:\n\n"
             f"📞 *الأرقام المتاحة (اضغط على الرقم لنسخه):*\n {current_text}"
             "🧾 *بعد إتمام التحويل:* يرجى كتابة وإرسال رقم العملية هنا في المحادثة مباشرة.",
        parse_mode="HTML",
        reply_markup=back_kb
    )
    
    # تعيين حالة استقبال رقم العملية
    await state.set_state(SyriatelState.process)
    await c.answer()

# ========================= رقم العملية =========================
@router.message(SyriatelState.process)
async def process_number_syriatelcach(m: types.Message, state: FSMContext):
    tx_text = m.text.strip()
    if not tx_text:
        await m.answer("❌ يرجى إرسال رقم عملية صحيح")
        await state.clear()
        return
        
    await state.update_data(process=tx_text)
    await m.answer("💰 أرسل المبلغ المحول")
    await state.set_state(SyriatelState.amount)

# ========================= المبلغ =========================
@router.message(SyriatelState.amount)
async def process_amount_syriatelCash(m: types.Message, state: FSMContext):
    data = await state.get_data()
    process = data.get("process")

    try:
        amount = int(m.text.strip())
        
        if amount < 20000:
            await m.answer("❌ عذراً، أقل قيمة يمكنك شحنها هي 20,000 ل.س.\nيرجى إرسال مبلغ يساوي الحد الأدنى أو أكبر:")
            await state.clear()
            return
            
    except ValueError:
        await m.answer("❌ أرسل مبلغ صحيح (أرقام فقط)")
        await state.clear()
        return

    uid = m.from_user.id
    success = await check_and_add_pending_deposit(user_id=uid, amount=amount, tx_type="SyriatelCash")
    if not success:
        await m.answer("❌ لديك طلب قيد المراجعة سابقاً بالفعل.")
        await state.clear()
        return
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ قبول", callback_data=f"acceptD_SY_{uid}"),
                InlineKeyboardButton(text="❌ رفض", callback_data=f"rejectD_SY_{uid}")
            ]
        ]
    )

    await m.answer("⏳ انتظر قليلاً للتحقق من العملية من قبل الإدارة")
    
    try:
        await m.bot.send_message(
            GROUP_ID,
            f"📥 طلب شحن جديد\n\n"
            f"نوع الشحن: SyriatelCash\n\n"
            f"👤 ID المستخدم: {uid}\n"
            f"🧾 رقم العملية: {process}\n"
            f"💰 المبلغ: {amount} ل.س",
            reply_markup=kb
        )
    except Exception as e:
        print(f"فشل إرسال الإشعار للجروب: {e}")
        await m.answer("⚠️ حدثت مشكلة أثناء إرسال طلبك للإدارة.")
        
    await state.clear()

# ========================= قبول العملية (سيرياتيل) =========================
@router.callback_query(F.data.startswith("acceptD_SY_"))
async def accept_syriatelcash(call: CallbackQuery):
    uid = int(call.data.split("_")[2])

    # جلب قيمة الشحن وحذفها من المعلق
    amount = await fetch_and_delete_pending(uid)

    if amount is None:
        await call.answer("❌ العملية غير موجودة أو تم معالجتها مسبقاً", show_alert=True)
        return

    # 1. تسجيل المعاملة الأساسية في قاعدة البيانات
    await add_transaction(
        user_id=uid,
        tx_type="deposit",
        amount=amount,
        status="completed",
        txid="SyriatelCash"
    )
    
    # تحديث رسالة الإدارة فوراً لتأكيد القبول
    await call.message.edit_text(call.message.text + "\n\n✅ تم قبول العملية بنجاح!")
    await call.answer()  # إغلاق مؤشر التحميل عند الآدمن

    # 2. معالجة عمولة الإيداع
    await process_deposit_commission(user_id=uid, deposit_amount=amount)
    
    # 3. حساب البونص إن وجد
    bonus_rate = await get_deposit_bonus_rate()
    bonus_amount = amount * bonus_rate
    total_amount = amount + bonus_amount
    
    # 4. إضافة إجمالي الرصيد لحساب المستخدم
    await add_balance(uid, total_amount)
    
    # 5. التحقق من شرط الجوهرة المجانية التلقائية (جوهرة لكل 20,000 ل.س بدون كسور)
    calculated_gems = amount // 20000
    if calculated_gems > 0:
        try:
            await call.bot.send_message(
                chat_id=uid, 
                text=f"💎 <b>تهانينا!</b> نظراً لأن قيمة شحنك هي {amount:,} ل.س، "
                     f"تم إضافة <b>{calculated_gems}</b> جوهرة مجانية إلى رصيدك الماسي!\n"
                     f"تفقد زر (جواهري) لمعرفة رصيدك واستبداله.",
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"تعذر إرسال رسالة الجوهرة للمستخدم {uid}: {e}")

    # 6. إرسال إشعار شحن الرصيد للمستخدم
    try:
        if bonus_amount > 0:
            await call.bot.send_message(
                chat_id=uid,
                text=f"✅ <b>تم تأكيد شحن حسابك!</b>\n\n"
                     f"💰 المبلغ المشحون: {amount:,} ل.س\n"
                     f"🎁 مكافأة البونص ({int(bonus_rate*100)}%): {bonus_amount:,} ل.س\n"
                     f"💵 الرصيد الإجمالي المضاف: <b>{total_amount:,} ل.س</b>",
                parse_mode="HTML"
            )
        else:
            await call.bot.send_message(
                chat_id=uid,
                text=f"✅ <b>تم تأكيد العملية بنجاح!</b>\n\n💰 تم إضافة <b>{amount:,} ل.س</b> إلى رصيدك الخاص.",
                parse_mode="HTML"
            )
    except Exception as e:
        print(f"تعذر إرسال رسالة الرصيد للمستخدم {uid}: {e}")

# ========================= رفض العملية (سيرياتيل) =========================
@router.callback_query(F.data.startswith("rejectD_SY_"))
async def rejectsyriatelcash(call: types.CallbackQuery):
    uid = int(call.data.split("_")[2])

    await delete_pending_only(uid)
    
    await call.message.edit_text(call.message.text + "\n\n❌ تم رفض العملية")
    try:
        await call.bot.send_message(uid, "❌ يوجد خطأ بالعملية، يرجى التحقق منها وتعديل البيانات المعطاة.")
    except Exception as e:
        print(f"تعذر مراسلة المستخدم المرفوض: {e}")
        # ========================== شام كاش =========================
@router.callback_query(lambda c: c.data == "pay_sham")
async def shamcashD(c: CallbackQuery, state: FSMContext):
    await state.clear()  # تصفية أي حالات سابقة لتفادي التعليق
    
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ إلغاء والعودة للقائمة", callback_data="back_to_main")]
    ])
   
    current_text = await get_sh_code_from_db()
    
    await c.message.edit_text(
        text="💳 *شحن عبر شام كاش*\n\n"
             "يرجى تحويل المبلغ المطلوب إلى العنوان أدناه:\n\n"
             f"📍 *العنوان:* \n<code>{current_text}</code>\n\n"
             "⚠️ *تنبيه هام:* من فضلك لا تقم بإخفاء هوية حساب شام كاش الذي تقوم بالشحن منه.\n\n"
             "🧾 *بعد التحويل:* يرجى إرسال رقم العملية هنا في المحادثة.",
        parse_mode="HTML",
        reply_markup=back_kb
    )
    
    await state.set_state(ShamCashState.process)
    await c.answer()

# ========================= رقم عملية شام كاش =========================
@router.message(ShamCashState.process)
async def process_number_shamcash(m: types.Message, state: FSMContext):
    tx_text = m.text.strip()
    if not tx_text:
        await m.answer("❌ يرجى إرسال رقم عملية صحيح")
        await state.clear()
        return
     
    await state.update_data(process=tx_text)
    await m.answer("💰 أرسل المبلغ المحول")
    await state.set_state(ShamCashState.amount)

# ========================= مبلغ شام كاش =========================
@router.message(ShamCashState.amount)
async def process_amount_shamcash(m: types.Message, state: FSMContext):
    data = await state.get_data()
    process = data.get("process")

    try:
        amount = int(m.text.strip())

        if amount < 20000:
            await m.answer("❌ عذراً، أقل قيمة يمكنك شحنها هي 20,000 ل.س.\nيرجى إرسال مبلغ يساوي الحد الأدنى أو أكبر:")
            await state.clear()
            return
            
    except ValueError:
        await m.answer("❌ أرسل مبلغ صحيح (أرقام فقط)")
        await state.clear()
        return

    uid = m.from_user.id
    success = await check_and_add_pending_deposit(user_id=uid, amount=amount, tx_type="shamcash")
 
    if not success:
        await m.answer("❌ لديك طلب قيد المراجعة سابقاً بالفعل.")
        await state.clear()
        return
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ قبول", callback_data=f"acceptD_SH_{uid}"),
                InlineKeyboardButton(text="❌ رفض", callback_data=f"rejectD_SH_{uid}")
            ]
        ]
    )

    await m.answer("⏳ انتظر قليلاً للتحقق من العملية من قبل الإدارة")
    
    try:
        await m.bot.send_message(
            GROUP_ID,
            f"📥 طلب شحن جديد\n\n"
            f"نوع الشحن: ShamCash\n\n"
            f"👤 ID المستخدم: {uid}\n"
            f"🧾 رقم العملية: {process}\n"
            f"💰 المبلغ: {amount} ل.س",
            reply_markup=kb
        )
    except Exception as e:
        print(f"فشل إرسال الإشعار للجروب: {e}")
        await m.answer("⚠️ حدثت مشكلة أثناء إرسال طلبك للإدارة.")
   
    await state.clear()

# ========================= قبول العملية (شام كاش) =========================
@router.callback_query(F.data.startswith("acceptD_SH_"))
async def accept_shamcash(call: types.CallbackQuery):
    uid = int(call.data.split("_")[2])

    # جلب قيمة الشحن وحذفها من المعلق
    amount = await fetch_and_delete_pending(uid)

    if amount is None:
        await call.answer("❌ العملية غير موجودة أو تم معالجتها مسبقاً", show_alert=True)
        return

    # 1. تسجيل المعاملة الأساسية في قاعدة البيانات (مرة واحدة فقط)
    await add_transaction(
        user_id=uid,
        tx_type="deposit",
        amount=amount,
        status="completed",
        txid="ShamCash"
    )
    
    # تحديث رسالة الإدارة فوراً لتأكيد القبول
    await call.message.edit_text(call.message.text + "\n\n✅ تم قبول العملية بنجاح!")
    await call.answer()  # إغلاق مؤشر التحميل عند الآدمن

    # 2. معالجة عمولة الإيداع
    await process_deposit_commission(user_id=uid, deposit_amount=amount)
    
    # 3. حساب البونص إن وجد
    bonus_rate = await get_deposit_bonus_rate()
    bonus_amount = amount * bonus_rate
    total_amount = amount + bonus_amount
    
    # 4. إضافة إجمالي الرصيد لحساب المستخدم
    await add_balance(uid, total_amount)
    
    # 5. التحقق من شرط الجوهرة المجانية التلقائية (جوهرة لكل 20,000 ل.س بدون كسور)
    calculated_gems = amount // 20000
    if calculated_gems > 0:
        try:
            await call.bot.send_message(
                chat_id=uid, 
                text=f"💎 <b>تهانينا!</b> نظراً لأن قيمة شحنك هي {amount:,} ل.س، "
                     f"تم إضافة <b>{calculated_gems}</b> جوهرة مجانية إلى رصيدك الماسي!\n"
                     f"تفقد زر (جواهري) لمعرفة رصيدك واستبداله.",
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"تعذر إرسال رسالة الجوهرة للمستخدم {uid}: {e}")

    # 6. إرسال إشعار شحن الرصيد للمستخدم
    try:
        if bonus_amount > 0:
            await call.bot.send_message(
                chat_id=uid,
                text=f"✅ <b>تم تأكيد شحن حسابك (شام كاش)!</b>\n\n"
                     f"💰 المبلغ المشحون: {amount:,} ل.س\n"
                     f"🎁 مكافأة البونص ({int(bonus_rate*100)}%): {bonus_amount:,} ل.س\n"
                     f"💵 الرصيد الإجمالي المضاف: <b>{total_amount:,} ل.س</b>",
                parse_mode="HTML"
            )
        else:
            await call.bot.send_message(
                chat_id=uid,
                text=f"✅ <b>تم تأكيد العملية بنجاح (شام كاش)!</b>\n\n💰 تم إضافة <b>{amount:,} ل.س</b> إلى رصيدك الخاص.",
                parse_mode="HTML"
            )
    except Exception as e:
        print(f"تعذر إرسال رسالة للمستخدم {uid}: {e}")

# ========================= رفض العملية (شام كاش) =========================
@router.callback_query(F.data.startswith("rejectD_SH_"))
async def rejectshamcash(call: types.CallbackQuery):
    uid = int(call.data.split("_")[2])

    await delete_pending_only(uid)
    
    await call.message.edit_text(call.message.text + "\n\n❌ تم رفض العملية")
    try:
        await call.bot.send_message(uid, "❌ يوجد خطأ بالعملية، يرجى التحقق منها وتعديل البيانات المعطاة.")
    except Exception as e:
        print(f"تعذر مراسلة المستخدم المرفوض: {e}")
