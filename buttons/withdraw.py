import aiohttp
from aiogram import types, Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.reply import withdraw_bot_kb
# استيراد الحوض والدوال بنظام الأسنك
from database.db import (
    add_transaction, 
    check_and_add_pending_withdraw,
    accept_pending_withdraw_db,
    reject_pending_withdraw_db
)

from config import GROUP_ID

class SyriatelStateW(StatesGroup):
    process = State()
    amount = State()
    confirm = State()  # حالة تأكيد الطلب للمستخدم قبل الإرسال

class ShamCashStateW(StatesGroup):
    process = State()
    amount = State()
    confirm = State()  # حالة تأكيد الطلب للمستخدم قبل الإرسال

router = Router()

# ========================= سحب =========================
@router.callback_query(lambda c: c.data == "menu_bot_withdraw")
async def withdraw(c: CallbackQuery):
    await c.message.edit_text(
        text="💳 *سحب رصيد من البوت*\n\nيرجى اختيار طريقة السحب التي تفضلها من الأزرار أدناه:",
        parse_mode="Markdown",
        reply_markup=withdraw_bot_kb
    )
    await c.answer()

# ========================= سيرياتيل كاش سحب =========================
@router.callback_query(lambda c: c.data == "WithdrawSy")
async def syriatelW(c: CallbackQuery, state: FSMContext):
    await state.clear()  # تنظيف أي حالة سابقة منعاً للتعليق
    
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ إلغاء والعودة للقائمة", callback_data="back_to_main")]
    ])
    
    await c.message.edit_text(
        text="📱 *سحب عبر سيرياتيل كاش*\n\n"
             "⚠️ *تنبيه:* عمولة السحب هي 10% خصم من المبلغ المسحوب.\n"
             "📌 *الحد الأدنى للسحب:* 50,000 ل.س\n\n"
             "يرجى إرسال رقم الهاتف الذي ترغب باستقبال الرصيد عليه في المحادثة مباشرة.",
        parse_mode="Markdown",
        reply_markup=back_kb
    )
    
    await state.set_state(SyriatelStateW.process)
    await c.answer()

# ========================= رقم الهاتف (سيرياتيل) =========================
@router.message(SyriatelStateW.process)
async def process_number_syriatel(m: types.Message, state: FSMContext):
    tx = m.text.strip()
    if not tx.isdigit():
        await m.answer("❌ أدخل رقم هاتف صحيح (أرقام فقط)")
        await state.clear()
        return
        
    await state.update_data(process=tx)
    await m.answer("💰 أرسل المبلغ الذي تريد سحبه:")
    await state.set_state(SyriatelStateW.amount)

# ========================= المبلغ وعرض الفاتورة (سيرياتيل) =========================
@router.message(SyriatelStateW.amount)
async def process_amount_syriatel(m: types.Message, state: FSMContext):
    try:
        amount = int(m.text.strip())
        if amount < 50000:
            await m.answer("❌ عذراً، أقل قيمة يمكنك سحبها هي 50,000 ل.س.\nيرجى إرسال مبلغ يساوي الحد الأدنى أو أكبر:")
            await state.clear()
            return
            
    except ValueError:
        await m.answer("❌ أرسل مبلغ صحيح (أرقام فقط)")
        await state.clear()
        return

    await state.update_data(amount=amount)
    data = await state.get_data()
    process = data.get("process")

    # حساب الحسم والمبلغ الصافي
    fee = int(amount * 0.10)
    net_amount = amount - fee

    # إنشاء أزرار الموافقة والإلغاء للمستخدم
    confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ موافق وإرسال الطلب", callback_data="confirm_withdraw_sy"),
            InlineKeyboardButton(text="❌ إلغاء", callback_data="back_to_main")
        ]
    ])

    await m.answer(
        f"📝 *تفاصيل طلب السحب الخاص بك:*\n\n"
        f"📱 *رقم الهاتف:* {process}\n"
        f"💰 *المبلغ المطلوب:* {amount:,} ل.س\n"
        f"✂️ *عمولة الخصم (10%):* {fee:,} ل.س\n"
        f"💵 *المبلغ الصافي الذي سيصلك:* *{net_amount:,} ل.س*\n\n"
        f"اضغط على زر موافق أدناه لتأكيد حجز الرصيد وإرسال الطلب للإدارة.",
        parse_mode="Markdown",
        reply_markup=confirm_kb
    )
    await state.set_state(SyriatelStateW.confirm)
    # ========================= الموافقة والإرسال للإدارة (سيرياتيل) =========================
@router.callback_query(SyriatelStateW.confirm, F.data == "confirm_withdraw_sy")
async def send_syriatel_withdraw_to_admin(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    process = data.get("process")
    amount = data.get("amount")
    uid = call.from_user.id

    # حجز الرصيد الفعلي والتحقق منه في قاعدة البيانات الآن
    success, status = await check_and_add_pending_withdraw(user_id=uid, amount=amount, tx_type="SyriatelCash")

    if not success:
        if status == "insufficient_balance":
            await call.message.edit_text("❌ رصيدك الحالي غير كافي لإتمام عملية السحب.")
        elif status == "has_pending":
            await call.message.edit_text("❌ لديك طلب (سحب أو شحن) قيد المراجعة سابقاً بالفعل.")
        else:
            await call.message.edit_text("❌ حدث خطأ ما، يرجى إعادة المحاولة لاحقاً.")
        await state.clear()
        return

    fee = int(amount * 0.10)
    net_amount = amount - fee

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ قبول", callback_data=f"acceptW_S_{uid}"),
            InlineKeyboardButton(text="❌ رفض", callback_data=f"rejectW_S_{uid}")
        ]
    ])

    await call.message.edit_text("⏳ تم تأكيد حجز الرصيد بنجاح، وجاري مراجعة طلبك من قبل الإدارة.")
    
    try:
        await call.bot.send_message(
            GROUP_ID,
            f"📤 طلب سحب جديد (سيرياتيل كاش)\n\n"
            f"👤 ID المستخدم: <code>{uid}</code>\n"
            f"🧾 رقم الهاتف للتحويل (اضغط للنسخ): <code>{process}</code>\n\n"
            f"💰 المبلغ المطلوب سحبه: {amount:,} ل.س\n"
            f"✂️ عمولة الخصم (10%): {fee:,} ل.س\n"
            f"💵 <b>المبلغ الصافي المراد تحويله:</b> <b>{net_amount:,} ل.س</b>",
            reply_markup=kb,
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"فشل إرسال إشعار سحب سيرياتيل للجروب: {e}")
        
    await state.clear()

# ========================= قبول ورفض سيرياتيل =========================
@router.callback_query(F.data.startswith("acceptW_S_"))
async def accept_syriatel_withdraw(call: types.CallbackQuery):
    uid = int(call.data.split("_")[2])
    amount = await accept_pending_withdraw_db(uid)
    if amount is None:
        await call.answer("❌ العملية غير موجودة أو تم معالجتها مسبقاً", show_alert=True)
        return
    await add_transaction(user_id=uid, tx_type="withdraw", amount=amount, status="completed", txid="SyriatelCash")
    await call.message.edit_text(call.message.text + "\n\n✅ تم قبول العملية وتأكيد السحب!")
    try:
        await call.bot.send_message(uid, f"✅ تم تأكيد طلب سحبك بنجاح بمبلغ {amount} ل.س عبر سيرياتيل كاش.\n📱 سيتم تحويل الرصيد إلى رقمك خلال مدة تتراوح من 5 دقائق إلى 6 ساعات.")
    except Exception as e:
        print(f"تعذر إرسال رسالة السحب للمستخدم {uid}: {e}")

@router.callback_query(F.data.startswith("rejectW_S_"))
async def reject_syriatel_withdraw(call: types.CallbackQuery):
    uid = int(call.data.split("_")[2])
    amount = await reject_pending_withdraw_db(uid)
    if amount is None:
        await call.answer("❌ العملية معالجة مسبقاً أو غير موجودة", show_alert=True)
        return
    await call.message.edit_text(call.message.text + "\n\n❌ تم رفض العملية وإعادة الرصيد للمستخدم.")
    try:
        await call.bot.send_message(uid, f"❌ تم رفض طلب السحب الخاص بك عبر سيرياتيل كاش من قبل الإدارة.\n💰 تم إعادة الرصيد المحجوز ({amount} ل.س) إلى حسابك في البوت بالكامل.")
    except Exception as e:
        print(f"تعذر مراسلة المستخدم عند الرفض: {e}")


# ========================== شام كاش سحب =========================
@router.callback_query(lambda c: c.data == "WithdrawSH")
async def shamcashW(c: CallbackQuery, state: FSMContext):
    await state.clear()
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ إلغاء والعودة للقائمة", callback_data="back_to_main")]
    ])
    
    await c.message.edit_text(
        text="💳 *سحب عبر شام كاش*\n\n"
             "⚠️ *تنبيه:* عمولة السحب هي 10% خصم من المبلغ المسحوب.\n"
             "📌 *الحد الأدنى للسحب:* 50,000 ل.س\n\n"
             "📲 لاستلام أرباحك، يرجى إرسال رابط الاستقبال الخاص بك.\n"
             "_(يمكنك الحصول عليه من تطبيق شام كاش 👈 زر الاستقبال)_\n\n"
             "👑 *تنبيه هام:* يرجى عدم إرفاق صورة باركود (QR)، فقط أرسل الرابط كنص.\n\n"
             "📞 للدعم الفني: @SHARK_SUPPORT_ICHANCY",
        parse_mode="Markdown",
        reply_markup=back_kb
    )
    
    await state.set_state(ShamCashStateW.process)
    await c.answer()

# ========================= رابط الاستقبال (شام كاش) =========================
@router.message(ShamCashStateW.process)
async def process_number_shamcash(m: types.Message, state: FSMContext):
    await state.update_data(process=m.text.strip())
    await m.answer("💰 أرسل المبلغ الذي تريد سحبه:")
    await state.set_state(ShamCashStateW.amount)

# ========================= المبلغ وعرض الفاتورة (شام كاش) =========================
@router.message(ShamCashStateW.amount)
async def process_amount_shamcash(m: types.Message, state: FSMContext):
    try:
        amount = int(m.text.strip())
        if amount < 50000:
            await m.answer("❌ عذراً، أقل قيمة يمكنك سحبها هي 50,000 ل.س.\nيرجى إرسال مبلغ يساوي الحد الأدنى أو أكبر:")
            await state.clear()
            return
    except ValueError:
        await m.answer("❌ أرسل مبلغ صحيح (أرقام فقط)")
        await state.clear()
        return

    await state.update_data(amount=amount)
    data = await state.get_data()
    process = data.get("process")

    # حساب الحسم والمبلغ الصافي للشام كاش
    fee = int(amount * 0.10)
    net_amount = amount - fee

    confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ موافق وإرسال الطلب", callback_data="confirm_withdraw_sh"),
            InlineKeyboardButton(text="❌ إلغاء", callback_data="back_to_main")
        ]
    ])

    await m.answer(
        f"📝 *تفاصيل طلب السحب الخاص بك (شام كاش):*\n\n"
        f"🔗 *رابط الاستقبال:* {process}\n"
        f"💰 *المبلغ المطلوب:* {amount:,} ل.س\n"
        f"✂️ *عمولة الخصم (10%):* {fee:,} ل.س\n"
        f"💵 *المبلغ الصافي الذي سيصلك:* *{net_amount:,} ل.س*\n\n"
        f"اضغط على زر موافق أدناه لتأكيد حجز الرصيد وإرسال الطلب للإدارة.",
        parse_mode="Markdown",
        reply_markup=confirm_kb
    )
    await state.set_state(ShamCashStateW.confirm)

# ========================= الموافقة والإرسال للإدارة (شام كاش) =========================
@router.callback_query(ShamCashStateW.confirm, F.data == "confirm_withdraw_sh")
async def send_shamcash_withdraw_to_admin(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    process = data.get("process")
    amount = data.get("amount")
    uid = call.from_user.id

    # حجز الرصيد والتحقق منه في قاعدة البيانات للشام كاش
    success, status = await check_and_add_pending_withdraw(user_id=uid, amount=amount, tx_type="ShamCash")

    if not success:
        if status == "insufficient_balance":
            await call.message.edit_text("❌ رصيدك الحالي غير كافي لإتمام عملية السحب.")
        elif status == "has_pending":
            await call.message.edit_text("❌ لديك طلب (سحب أو شحن) قيد المراجعة سابقاً بالفعل.")
        else:
            await call.message.edit_text("❌ حدث خطأ ما، يرجى إعادة المحاولة لاحقاً.")
        await state.clear()
        return

    fee = int(amount * 0.10)
    net_amount = amount - fee

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ قبول", callback_data=f"acceptW_SH_{uid}"),
            InlineKeyboardButton(text="❌ رفض", callback_data=f"rejectW_SH_{uid}")
        ]
    ])
    await call.message.edit_text("⏳ تم تأكيد حجز الرصيد بنجاح، وجاري مراجعة طلبك من قبل الإدارة.")
    
    try:
        # هنا تم إضافة وسم <code> ليكون الرابط والـ ID قابلين للنسخ المباشر بضغطة واحدة
        await call.bot.send_message(
            GROUP_ID,
            f"📤 <b>طلب سحب جديد (شام كاش)</b>\n\n"
            f"👤 ID المستخدم: <code>{uid}</code>\n"
            f"🔗 رابط الاستقبال (اضغط للنسخ):\n<code>{process}</code>\n\n"
            f"💰 المبلغ المطلوب سحبه: {amount:,} ل.س\n"
            f"✂️ عمولة الخصم (10%): {fee:,} ل.س\n"
            f"💵 <b>المبلغ الصافي المراد تحويله:</b> <b>{net_amount:,} ل.س</b>",
            reply_markup=kb,
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"فشل إرسال إشعار السحب للجروب: {e}")
        
    await state.clear()

# ========================= قبول ورفض شام كاش =========================
@router.callback_query(F.data.startswith("acceptW_SH_"))
async def accept_shamcash(call: types.CallbackQuery):
    uid = int(call.data.split("_")[2])
    amount = await accept_pending_withdraw_db(uid)
    if amount is None:
        await call.answer("❌ العملية غير موجودة أو تم معالجتها مسبقاً", show_alert=True)
        return
    await add_transaction(user_id=uid, tx_type="withdraw", amount=amount, status="completed", txid="ShamCash")
    await call.message.edit_text(call.message.text + "\n\n✅ تم قبول العملية وتأكيد السحب!")
    try:
        await call.bot.send_message(uid, f"✅ تم تأكيد طلب سحبك بنجاح بمبلغ {amount} ل.س\n💳 سيتم تحويل الرصيد إلى محفظتك خلال مدة تتراوح من 5 دقائق إلى 6 ساعات.")
    except Exception as e:
        print(f"تعذر إرسال رسالة السحب للمستخدم {uid}: {e}")

@router.callback_query(F.data.startswith("rejectW_SH_"))
async def rejectshamcash(call: types.CallbackQuery):
    uid = int(call.data.split("_")[2])
    amount = await reject_pending_withdraw_db(uid)
    if amount is None:
        await call.answer("❌ العملية معالجة مسبقاً أو غير موجودة", show_alert=True)
        return
    await call.message.edit_text(call.message.text + "\n\n❌ تم رفض العملية وإعادة الرصيد للمستخدم.")
    try:
        await call.bot.send_message(uid, f"❌ تم رفض طلب السحب الخاص بك من قبل الإدارة.\n💰 تم إعادة الرصيد المحجوز ({amount} ل.س) إلى حسابك في البوت بالكامل، يرجى مراجعة بياناتك.")
    except Exception as e:
        print(f"تعذر مراسلة المستخدم عند الرفض: {e}")
