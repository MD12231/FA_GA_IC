from aiogram import types, BaseMiddleware, Router, F, Bot
from typing import Callable, Dict, Any, Awaitable
from keyboards.reply import menu, ichancymenu, ichancymenuregistered
from aiogram.fsm.state import State, StatesGroup
from subscribed import is_subscribed
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, TelegramObject, CallbackQuery
from logger import logger
from encryption import decrypt_password, encrypt_password
import asyncio

class GiftState(StatesGroup):
    waiting_code = State()

# استيراد دوال الأسنك وحوض الاتصالات الرئيسي
from database.db import (
    db_pool,
    add_user,
    get_balance,
    save_user_to_db,
    add_referral,
    add_balance,
    get_user,
    get_bonus_from_db,
    get_user_referral_stats,
    redeem_gift_code_db,
    get_user_transactions_paginated,
    get_gems,
    exchange_gems_to_balance,
    reduce_user_balance,
    increase_user_balance,
    save_support_ticket,
    get_user_by_message,
    transfer_gift_balance
)
from config import TOKKEN, PARENT_ID
from aiogram.fsm.context import FSMContext

from buttons.games_ichancy import router as games_router
from buttons.deposit import router as deposit_router
from buttons.tutorials import router as tutorials_router
from buttons.withdraw import router as withdraw_router

from ichancy.ichancy_api import register_new_player_async, get_player_balance_async, withdraw_from_player_async, find_player_id_by_username, deposit_to_player_async

# إنشاء الراوتر بدلاً من الـ Dispatcher القديم
router = Router()

class RegisterState(StatesGroup):
    username = State()
    password = State()

class DepositState(StatesGroup):
    amountichancy = State()

class WithdrawState(StatesGroup):
    amount = State()

class TransferState(StatesGroup):
    waiting_for_id = State()
    waiting_for_amount = State()

class SupportStates(StatesGroup):
    waiting_for_user_msg = State()

# 🚨 تم تعيين آيدي مجموعتك الحقيقي هنا بنجاح
ADMIN_GROUP_ID = -1004310258428


class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        if not await is_subscribed(user_id, event.bot):
            await event.answer(
                f"❌ يجب الاشتراك بالقناة أولاً:\nhttps://t.me/FalconGalaxyIchancy"
            )
            return
        return await handler(event, data)

# ربط الميدل وير بالراوتر الحالي
router.message.middleware(SubscriptionMiddleware())
router.callback_query.middleware(SubscriptionMiddleware())

# تضمين الراوترات الفرعية داخل راوتر المستخدم الرئيسي
router.include_router(games_router)
router.include_router(withdraw_router)
router.include_router(deposit_router)
router.include_router(tutorials_router)


from aiogram.filters import CommandObject, Command
from aiogram.types import Message


@router.message(Command("start"))
async def cmd_start(message: Message, command: CommandObject):
    user_id = message.from_user.id
    referrer_param = command.args  # التقاط المعامل الممرر بعد الفراغ في الرابط (?start=referrer_id)
    
    # 1. محاولة إضافة المستخدم لقاعدة البيانات كـ مستخدم جديد
    # دالة add_user تعيد True إذا تم الإدخال بنجاح (مستخدم جديد) أو False إذا كان مسجلاً مسبقاً
    is_new_user = await add_user(user_id) 
    
    if is_new_user:
        # 2. إذا كان مستخدماً جديداً، نتحقق من وجود رابط إحالة صالح
        if referrer_param and referrer_param.isdigit():
            referrer_id = int(referrer_param)
            
            # منع المستخدم من إحالة نفسه برمجياً لحماية النظام
            if referrer_id != user_id:
                # استخدام دالتك add_referral لتسجيل العلاقة وزيادة عداد المحيل
                referral_success = await add_referral(user_id=user_id, referrer_id=referrer_id)
                
                if referral_success:
                    # إرسال إشعار للمحيل الأصلي لإعلامه بالتشغيل الجديد وعقد الولاء
                    try:
                        await message.bot.send_message(
                            chat_id=referrer_id,
                            text=f"👥 <b>إحالة جديدة!</b>\nسجل مستخدم جديد في البوت عن طريق رابطك بنجاح.",
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        print(f"⚠️ فشل إرسال إشعار الإحالة للمستخدم {referrer_id}: {e}")
    else:
        # إذا لم يكن مستخدماً جديداً، لا نمنحه إحالة ولا نعدل على بياناته الحالية
        pass

    # 3. جلب الرصيد وعرض واجهة الترحيب الرئيسية للبوت كالمعتاد
    balance = await get_balance(user_id)
    welcome_text = f"🎰 <b>أهلاً بك في بوت Falcon Galaxy Ichancy</b>\n\n💰 رصيدك الحالي: <b>{balance:,} ل.س</b>"
    
    # تفضل دائماً إرسال القائمة الرئيسية المجهزة مسبقاً لديك (menu)
    await message.answer(
        text=welcome_text,
        parse_mode="HTML",
        reply_markup=menu  # الكيبورد الرئيسي الخاص بك (تأكد من استيراده أو تعريفه)
    )

@router.callback_query(lambda c: c.data == "menu_check_balance")
async def process_check_balance(c: CallbackQuery):
    # جلب الرصيد من قاعدة البيانات
    bal = await get_balance(c.from_user.id)
    
    # إظهار الرصيد في نافذة منبثقة (Alert)
    await c.answer(
        text=f"💰 رصيدك الحالي هو: {bal:,} ل.س", 
        show_alert=True  # True تعني نافذة منبثقة بوسط الشاشة مع زر موافق
    )





@router.callback_query(lambda c: c.data == "menu_ichancy")
async def ichancy(c: CallbackQuery):
    user_id = c.from_user.id
    
    # جلب بيانات المستخدم من قاعدة البيانات
    user = await get_user(user_id)
    
    if user:
        username, password, email = user
        ppass = decrypt_password(password)
        
        # تنسيق النص للمستخدم المسجل بالفعل مع ميزة النسخ التلقائي لليوزر والباسورد
        registered_text = (
            "🎰 <b>مرحباً بك في Ichancy</b>\n\n"
            f"👤 <b>اسم المستخدم:</b> <code>{username}</code>\n"
            f"🔑 <b>كلمة المرور:</b> <code>{ppass}</code>\n"
            f"🆔 <b>الحساب الخاص بك:</b> <code>{user_id}</code>\n\n"
            "✅ <i>أنت مسجل بالفعل في النظام، يمكنك استخدام البيانات أعلاه لتسجيل الدخول.</i>"
        )
        
        await c.message.edit_text(
            text=registered_text,
            parse_mode="HTML",
            reply_markup=ichancymenuregistered
        )
        await c.answer()
        return

    # تنسيق النص للمستخدم الجديد غير المسجل
    unregistered_text = (
        "🎰 <b>مرحباً بك في Ichancy</b>\n\n"
        f"🆔 <b>معرّف الحساب الخاص بك:</b> <code>{user_id}</code>\n\n"
        "⚠️ <i>أنت غير مسجل حالياً، يرجى الضغط على زر التسجيل أدناه لإنشاء حسابك.</i>"
    )
    
    # تعديل الرسالة وعرض كيبورد التسجيل
    await c.message.edit_text(
        text=unregistered_text,
        parse_mode="HTML",
        reply_markup=ichancymenu
    )
    await c.answer()

# 1. استقبال الضغطة على زر إنشاء الحساب (تحولت إلى كولباك)
@router.callback_query(lambda c: c.data == "register_ichancy")
async def register_ichancy(c: CallbackQuery, state: FSMContext):
    # مسح حالة القائمة القديمة وكتابة التوجيه للمستخدم
    await c.message.edit_text(
        text="📝 *يرجى إدخال اسم المستخدم الجديد (Username):*",
        parse_mode="Markdown"
    )
    await state.set_state(RegisterState.username)
    await c.answer()

# 2. استقبال اسم المستخدم (تبقى رسالة نصية لأن المستخدم يكتب)
@router.message(RegisterState.username)
async def reg_username(m: types.Message, state: FSMContext):
    username = m.text.strip()
    await state.update_data(username=username)
    
    await m.answer(
        text="🔑 *يرجى إدخال كلمة المرور الخاصة بالحساب (Password):*",
        parse_mode="Markdown"
    )
    await state.set_state(RegisterState.password)

# 3. استقبال كلمة المرور وإتمام عملية التسجيل
@router.message(RegisterState.password)
async def reg_password(m: types.Message, state: FSMContext):
    usertelegram = m.from_user.id
    password = m.text.strip()
    data = await state.get_data()
    username = data["username"]
    passs = encrypt_password(password)

    # كيبورد بسيط للعودة في حال النجاح أو الفشل
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 العودة للقائمة الرئيسية", callback_data="back_to_main")]
    ])

    response_result = await register_new_player_async(player_username=username, player_password=password)
    
    if response_result and response_result.get("success") is True:
        await m.answer(
            f"🎉 *تهانياً! تم إنشاء حسابك على Ichancy بنجاح.*\n\n"
            f"👤 *اسم المستخدم:* {username}7_777\n"
            f"🔑 *كلمة المرور:* {password}\n"
            f"📧 *البريد الإلكتروني:* {username}7_777@gmail.com\n\n"
            "💡 _يمكنك الآن الضغط على البيانات أعلاه لنسخها وتأكيد دخولك عبر أزرار المنصة._",
            parse_mode="Markdown",
            reply_markup=back_kb # تم استبدال menu بالـ Inline Keyboard للعودة
        )
        await save_user_to_db(user_id=usertelegram, email=f"{username}7_777@pirate.com", password=passs, username=f"{username}7_777")
    else:
        error_reason = response_result.get("error", "حدث خطأ غير معروف في السيرفر")
        await m.answer(
            f"❌ *عذراً، فشل إنشاء الحساب.*\n\n"
            f"⚠️ *السبب:* {error_reason}\n\n"
            f"يرجى المحاولة مجدداً باستخدام اسم مستخدم آخر.",
            parse_mode="Markdown",
            reply_markup=back_kb # تم استبدال menu بالـ Inline Keyboard للعودة
        )
    
    await state.clear()

# 1. استقبال الضغطة على زر الشحن (Inline)
@router.callback_query(lambda c: c.data == "deposit_ichancy")
async def reg_depositichancy(c: CallbackQuery, state: FSMContext):
    await c.message.edit_text(
        text="💰 <b>يرجى إرسال المبلغ المراد شحنه:</b>",
        parse_mode="HTML" # تم التغيير لـ HTML لتوحيد التنسيق
    )
    await state.set_state(DepositState.amountichancy)
    await c.answer()

# 2. استقبال المبلغ
@router.message(DepositState.amountichancy)
async def reg_amount(m: types.Message, state: FSMContext):
    # تعريف زر العودة في البداية لتجنب الـ NameError في الـ Except
    back_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 العودة للقائمة الرئيسية", callback_data="back_to_main")]])
    
    try:
        try:
            amount = int(m.text)
        except ValueError:
            await m.answer("❌ <b>خطأ: يرجى إرسال أرقام فقط.</b>", parse_mode="HTML")
            return
        
        if amount < 20000:
            await m.answer("⚠️ <b>الحد الأدنى لعملية الشحن هو 20000.</b>", parse_mode="HTML", reply_markup=back_kb)
            await state.clear()
            return

        from_id = m.from_user.id
        user = await get_user(from_id)

        if not user:
            await m.answer("❌ <b>لم يتم العثور على الحساب.</b>", parse_mode="HTML", reply_markup=back_kb)
            await state.clear()
            return
        
        sender_balance = await get_balance(from_id)
        if sender_balance < amount:
            await m.answer("❌ <b>رصيدك غير كافي لهذه العملية.</b>", parse_mode="HTML", reply_markup=back_kb)
            await state.clear()
            return
        
        username, password, email = user
        
        # رسالة الانتظار
        loading_msg = await m.answer("🔍 <b>جاري التحقق من الحساب على السيرفر...</b>", parse_mode="HTML")

        # 1. البحث عن اللاعب وجلب معرفه الرقمي
        user_info = await find_player_id_by_username(target_username=username)
        if not user_info or not user_info.get("found"):
            try: await loading_msg.delete()
            except: pass
            await m.answer(f"❌ <b>فشل الشحن. اللاعب <code>{username}</code> غير موجود على السيرفر.</b>", parse_mode="HTML", reply_markup=back_kb)
            await state.clear()
            return

        target_player_id = user_info["id"]
        
        # 🌟 [تعديل أمني] خصم الرصيد محلياً أولاً قبل إرسال الطلب للسيرفر الخارجي
        db_success = await reduce_user_balance(user_id=from_id, amount=amount)
        if not db_success:
            try: await loading_msg.delete()
            except: pass
            await m.answer("❌ <b>حدث خطأ أثناء محاولة خصم الرصيد من نظام البوت، تم إلغاء العملية.</b>", parse_mode="HTML", reply_markup=back_kb)
            await state.clear()
            return

        # 2. إرسال طلب الشحن التلقائي للسيرفر المالي بعد ضمان الخصم
        depositichancy = await deposit_to_player_async(
            player_id=target_player_id,  
            amount=amount,
            comment="شحن تلقائي عبر البوت"
        )

        try: await loading_msg.delete()
        except: pass

        if depositichancy and depositichancy.get("success") is True:
            # نجاح كامل
            await m.answer(
                f"✅ <b>تم شحن {amount} بنجاح لحسابك.</b>\n\n"
                f"👤 اللاعب: <code>{username}</code>\n"
                f"🆔 معرف اللاعب: <code>{target_player_id}</code>",
                parse_mode="HTML",
                reply_markup=back_kb
            )
        else:
            # 🌟 [تعديل أمني] فشل الشحن الخارجي -> نعيد الرصيد للمستخدم فوراً
            await add_balance(user_id=from_id, amount=amount) # افترضت أن اسم الدالة هكذا
            
            error_reason = depositichancy.get("error", "حدث خطأ في منظومة الشحن") if depositichancy else "لا يوجد استجابة من السيرفر"
            await m.answer(f"❌ <b>فشل الشحن وتم إعادة الرصيد لحسابك.</b>\n\n⚠️ السبب: {error_reason}", parse_mode="HTML", reply_markup=back_kb)
            
        await state.clear()
        
    except Exception as general_error:
        print(f"[CRITICAL HANDLER ERROR] {str(general_error)}")
        await m.answer(f"❌ <b>حدث خطأ داخلي غير متوقع:</b>\n<code>{str(general_error)}</code>", parse_mode="HTML", reply_markup=back_kb)
        await state.clear()

# 1. استقبال الضغطة على زر السحب (Inline)
@router.callback_query(lambda c: c.data == "withdraw_ichancy")
async def start_withdraw(c: CallbackQuery, state: FSMContext):
    await c.message.edit_text(
        text="💸 <b>يرجى إرسال المبلغ الذي ترغب بسحبه:</b>",
        parse_mode="HTML" # تم التوحيد إلى HTML لسلامة النص
    )
    await state.set_state(WithdrawState.amount)
    await c.answer()

# 2. استقبال المبلغ ومعالجة السحب
@router.message(WithdrawState.amount)
async def do_withdraw(m: types.Message, state: FSMContext):
    back_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 العودة للقائمة الرئيسية", callback_data="back_to_main")]])
    
    try:
        try:
            amount = int(m.text)
        except ValueError:
            await m.answer("❌ <b>خطأ: يرجى إرسال أرقام فقط.</b>", parse_mode="HTML")
            return
        
        if amount < 20000:
            await m.answer("⚠️ <b>أقل قيمة سحب يجب أن تكون 20000.</b>", parse_mode="HTML", reply_markup=back_kb)
            await state.clear()
            return

        from_id = m.from_user.id
        user = await get_user(from_id)

        if not user:
            await m.answer("❌ <b>لم يتم العثور على الحساب.</b>", parse_mode="HTML", reply_markup=back_kb)
            await state.clear()
            return

        username, password, email = user
        
        # إرسال رسالة الانتظار
        loading_msg = await m.answer("🔍 <b>جاري فحص الحساب والتحقق من الرصيد على المنصة...</b>", parse_mode="HTML")

        # 1. التحقق من وجود حساب اللاعب
        user_info = await find_player_id_by_username(target_username=username)
        if not user_info or not user_info.get("found"):
            try: await loading_msg.delete()
            except: pass
            await m.answer(f"❌ <b>فشل السحب. حساب اللاعب <code>{username}</code> غير موجود.</b>", parse_mode="HTML", reply_markup=back_kb)
            await state.clear()
            return

        target_player_id = user_info["id"]
        
        # 2. جلب رصيد اللاعب الحالي على المنصة
        balance_check = await get_player_balance_async(player_id=target_player_id)
        
        if not balance_check or not balance_check.get("success"):
            try: await loading_msg.delete()
            except: pass
            error_msg = balance_check.get("error", "تعذر قراءة بيانات المحفظة الحالية")
            await m.answer(f"❌ <b>تم إلغاء العملية.</b>\n⚠️ السبب: {error_msg}", parse_mode="HTML", reply_markup=back_kb)
            await state.clear()
            return
            
        server_player_balance = balance_check["balance"]
        if server_player_balance < amount:
            try: await loading_msg.delete()
            except: pass
            await m.answer(
                f"❌ <b>طلب سحب غير صالح.</b>\n\n"
                f"⚠️ رصيدك الحالي في اللعبة: <code>{server_player_balance}</code> NSP\n"
                f"💰 المبلغ المطلوب سحبه: <code>{amount}</code> NSP\n\n"
                "رصيدك في اللعبة غير كافٍ لإتمام هذه العملية.",
                parse_mode="HTML",
                reply_markup=back_kb
            )
            await state.clear()
            return

        # 3. إرسال طلب السحب الفعلي للسيرفر
        withdraw_result = await withdraw_from_player_async(
            player_id=target_player_id,
            amount=amount,
            comment="سحب تلقائي آمن عبر البوت"
        )

        try: await loading_msg.delete()
        except: pass

        # ضبط الـ Indentation وتعديل الشروط لضمان الأمان
        if withdraw_result and withdraw_result.get("success") is True:
            # 4. تحديث قاعدة البيانات محلياً بزيادة الرصيد للمستخدم
            db_success = await increase_user_balance(user_id=from_id, amount=amount)
            
            if db_success:
                await m.answer(f"✅ <b>تم تأكيد السحب بنجاح!</b>\n\n"
                    f"👤 اللاعب: <code>{username}</code>\n"
                    f"💰 المبلغ المسحوب: <code>{amount}</code> NSP\n"
                    "📥 تم إضافة الرصيد إلى محفظتك في البوت بنجاح.",
                    parse_mode="HTML",
                    reply_markup=back_kb
                )
            else:
                # 🌟 [حماية حرجة] فشل التحديث في البوت بعد الخصم من اللعبة -> إعادة الأموال للعبة فوراً (Rollback)
                await deposit_to_player_async(
                    player_id=target_player_id,
                    amount=amount,
                    comment="إعادة رصيد تلقائية بسبب خطأ في نظام البوت الداخلي"
                )
                await m.answer(
                    f"⚠️ <b>حدث خطأ داخلي في قاعدة بيانات البوت أثناء تسجيل العملية.</b>\n"
                    f"إجراء أمني: تم إلغاء السحب وإعادة المبلغ <code>{amount}</code> تلقائياً إلى حسابك في اللعبة لحمايتك.", 
                    parse_mode="HTML", 
                    reply_markup=back_kb
                )
        else:
            error_reason = withdraw_result.get("error", "حدث خطأ أثناء معالجة السحب") if withdraw_result else "لا توجد استجابة من السيرفر"
            await m.answer(f"❌ <b>فشلت عملية السحب من المنصة</b>\n\n⚠️ السبب: {error_reason}", parse_mode="HTML", reply_markup=back_kb)
            
        await state.clear()

    except Exception as general_error:
        print(f"[CRITICAL WITHDRAW ERROR] {str(general_error)}")
        try: await loading_msg.delete()
        except: pass
        await m.answer(f"❌ <b>حدث خطأ داخلي غير متوقع:</b>\n<code>{str(general_error)}</code>", parse_mode="HTML", reply_markup=back_kb)
        await state.clear()









@router.callback_query(lambda c: c.data == "menu_referrals")
async def process_referrals_system(c: CallbackQuery):
    user_id = c.from_user.id
    
    # جلب بيانات الإحالات من قاعدة البيانات
    row = await get_user_referral_stats(user_id)

    if not row:
        await c.answer("⚠️ لا يوجد بيانات خاصة بك حالياً في النظام.", show_alert=True)
        return

    referrals, balance, pending_commission = row

    # إنشاء زر العودة للقائمة الرئيسية أسفل الإحصائيات
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 العودة للقائمة الرئيسية", callback_data="back_to_main")]
    ])

    # نص نظام الإحالات منسق بـ HTML كما فضّلت في كودك
    text = (
        f"👥 <b>نظام إحالات Ichancy Shark</b>\n\n"
        f"يقدّم لك فرصة لدخل إضافي كل 10 أيام.\n"
        f"احصل على نسبة ثابتة <b>1%</b> لكل عمليات الشحن القادمة عن طريق رابط إحالتك!\n\n"
        f"📊 <b>إحصائياتك الحالية:</b>\n"
        f"• عدد إحالاتك: <code>{referrals}</code> مستخدم\n"
        f"• أرباحك المعلقة (ستوزع بعد انتهاء الـ 10 أيام): <code>{pending_commission:,}</code> ل.س\n\n"
        f"🔗 <b>رابط الإحالة الخاص بك:</b>\n"
        f"<code>https://t.me/Falcon_Galaxy_Ichancy_Bot?start={user_id}</code>\n\n"
        f"<i>💡 اضغط على الرابط أعلاه لنسخه تلقائياً.</i>"
    )

    # تعديل الرسالة الحالية وعرض الإحصائيات مع زر العودة
    await c.message.edit_text(
        text=text,
        parse_mode="HTML",
        reply_markup=back_kb,
        disable_web_page_preview=True # لمنع ظهور معاينة لروابط تليغرام داخل التشات
    )
    await c.answer()

# مستقبل كولباك لزر العودة إلى القائمة الرئيسية (إذا لم تكن قد أضفته سابقاً)
@router.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main_menu(c: CallbackQuery):
    # جلب الرصيد مجدداً لتحديث الواجهة الرئيسية للمستخدم عند العودة
    balance = await get_balance(c.from_user.id)
    welcome_text = f"🎰 <b>أهلاً بك في بوت Falcon Galaxy Ichancy</b>\n\n💰 رصيدك الحالي: <b>{balance:,} ل.س</b>"
    
    await c.message.edit_text(
        text=welcome_text, 
        parse_mode="HTML", 
        reply_markup=menu
    )
    await c.answer()







# 1. استقبال الضغط على زر "كود هدية" من القائمة الرئيسية
@router.callback_query(lambda c: c.data == "menu_gift_code")
async def gift(c: CallbackQuery, state: FSMContext):
    # تصفير أي حالات سابقة لضمان عدم حدوث تداخل
    await state.clear()
    
    # نقوم بطلب الكود من المستخدم بتعديل نفس الرسالة، أو إرسال رسالة جديدة
    # هنا يفضل إرسال رسالة جديدة أو تعديل الرسالة مع زر إلغاء لتسهيل التجربة
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ إلغاء العملية", callback_data="back_to_main")]
    ])
    
    await c.message.edit_text(
        text="🎁 *يرجى إرسال كود الهدية الخاص بك الآن في الشات:*",
        parse_mode="Markdown",
        reply_markup=cancel_kb
    )
    
    # تفعيل حالة انتظار الكود النصي من المستخدم
    await state.set_state(GiftState.waiting_code)
    await c.answer()

# 2. استقبال الكود النصي (يبقى message لأن المستخدم سيكتب نصاً)
@router.message(GiftState.waiting_code)
async def redeem_code(m: types.Message, state: FSMContext):
    code = m.text.strip().upper()
    uid = m.from_user.id

    # معالجة الكود في قاعدة البيانات
    success, status_or_amount = await redeem_gift_code_db(user_id=uid, code=code)

    # تجهيز كيبورد العودة للقائمة الرئيسية آلياً بعد انتهاء العملية
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 العودة للقائمة الرئيسية", callback_data="back_to_main")]
    ])

    if not success:
        if status_or_amount == "not_found":
            await m.answer("❌ الكود الذي أدخلته غير صحيح أو منتهي الصلاحية.", reply_markup=back_kb)
        elif status_or_amount == "already_used":
            await m.answer("❌ عذراً، هذا الكود مستخدم مسبقاً من قبلك أو من قبل مستخدم آخر.", reply_markup=back_kb)
        else:
            await m.answer("⚠️ حدث خطأ أثناء تفعيل الكود، يرجى المحاولة مرة أخرى لاحقاً.", reply_markup=back_kb)
        
        await state.clear()
        return

    amount = status_or_amount
    
    # تنسيق رسالة النجاح
    success_text = (
        f"🎉 *مبروك! تم تفعيل كود الهدية بنجاح.*\n\n"
        f"💰 تم إضافة *{amount:,} ل.س* إلى رصيدك الحالي."
    )
    
    await m.answer(text=success_text, parse_mode="Markdown", reply_markup=back_kb)
    
    # إنهاء الحالة (FSM) لتنظيف الذاكرة
    await state.clear()












# 1. استقبال زر "إهداء رصيد" من القائمة الرئيسية
@router.callback_query(lambda c: c.data == "menu_gift_balance")
async def ask_id(c: CallbackQuery, state: FSMContext):
    await state.clear()
    
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ إلغاء العملية", callback_data="back_to_main")]
    ])
    
    await c.message.edit_text(
        text="💝 *إهداء رصيد*\n\nالخطوة (1/2): يرجى إرسال الـ (ID) الخاص بالشخص الذي تود إهداء الرصيد له:",
        parse_mode="Markdown",
        reply_markup=cancel_kb
    )
    await state.set_state(TransferState.waiting_for_id)
    await c.answer()

# 2. استقبال الـ ID والانتقال لطلب المبلغ
@router.message(TransferState.waiting_for_id)
async def ask_amount(m: types.Message, state: FSMContext):
    if not m.text.isdigit():
        await m.answer("⚠️ يرجى إرسال الـ ID بشكل صحيح (أرقام فقط):")
        return
    
    await state.update_data(to_id=int(m.text))
    await m.answer("✅ تم تحديد الشخص.\n\nالخطوة (2/2): الآن أرسل المبلغ الذي تود إهدائه:")
    await state.set_state(TransferState.waiting_for_amount)

# 3. إتمام عملية التحويل بعد استقبال المبلغ
# 3. إتمام عملية التحويل بعد استقبال المبلغ
@router.message(TransferState.waiting_for_amount)
async def process_transfer(m: types.Message, state: FSMContext):
    if not m.text.isdigit():
        await m.answer("⚠️ يرجى إرسال المبلغ بشكل صحيح (أرقام فقط):")
        return
    
    amount = int(m.text)
    if amount <= 0:
        await m.answer("⚠️ يجب أن يكون المبلغ أكبر من 0.")
        return
        
    data = await state.get_data()
    to_id = data['to_id']
    from_id = m.from_user.id
    
    # استدعاء الدالة الآمنة من قاعدة البيانات
    success, status = await transfer_gift_balance(from_id, to_id, amount)
    
    if not success:
        if status == "insufficient_balance":
            await m.answer("❌ رصيدك غير كافي لإتمام عملية الإهداء.")
        elif status == "receiver_not_found":
            await m.answer("❌ هذا الـ ID غير مسجل في البوت، يرجى التأكد من الرقم.")
        elif status == "self_transfer":
            await m.answer("⚠️ لا يمكنك إهداء الرصيد لنفسك!")
        else:
            await m.answer("❌ حدث خطأ غير متوقع أثناء معالجة العملية، يرجى المحاولة لاحقاً.")
        
        await state.clear()
        return

    # في حال النجاح التام:
    await m.answer(f"💝 تم إرسال <b>{amount:,} ل.س</b> بنجاح إلى المستخدم <code>{to_id}</code>", parse_mode="HTML")
    
    # إشعار الطرف الآخر
    try:
        await m.bot.send_message(
            chat_id=to_id, 
            text=f"💝 وصلت إليك هدية بقيمة <b>{amount:,} ل.س</b> وأضيفت إلى رصيدك بنجاح!",
            parse_mode="HTML"
        )
    except Exception:
        pass # لتفادي توقف الكود لو كان الطرف الآخر حظر البوت
        
    await state.clear()












@router.message(lambda m: m.text == "☎️ تواصل معنا")
async def support(m: types.Message):
    await m.answer("اكتب الرسالة وسيتم ارسالها للادمن")









PAGE_SIZE = 5

@router.callback_query(lambda c: c.data == "menu_logs")
async def my_transactions(c: CallbackQuery):
    
    # بناء كيبورد السجل المطور مع زر العودة
    history_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📥 الإيداعات", callback_data="list_deposit_0"),
                InlineKeyboardButton(text="📤 السحوبات", callback_data="list_withdraw_0")
            ],
            # إضافة سطر العودة للقائمة الرئيسية
            [
                InlineKeyboardButton(text="🔙 العودة للقائمة الرئيسية", callback_data="back_to_main")
            ]
        ]
    )
    
    # تعديل الرسالة الحالية لتحديث الواجهة فوراً
    await c.message.edit_text(
        text="📊 *سجل العمليات الخاص بك*\n\nيرجى اختيار نوع السجل الذي ترغب في استعراضه من الأزرار أدناه:",
        parse_mode="Markdown",
        reply_markup=history_kb
    )
    
    # إنهاء حالة التحميل على الزر
    await c.answer()





async def show_list(call: types.CallbackQuery, filter_type: str, page: int):
    uid = call.from_user.id
    offset = page * PAGE_SIZE

    if filter_type == "deposit":
        query_type = "%deposit%"
        title = "📥 الإيداعات"
    else:
        query_type = "%withdraw%"
        title = "📤 السحوبات"
    
    rows, total = await get_user_transactions_paginated(
        user_id=uid,
        query_type=query_type,
        limit=PAGE_SIZE,
        offset=offset
    )
    if not rows:
        await call.message.answer("📭 لا يوجد بيانات")
        return
    text = f"{title} - صفحة {page+1}\n\n"
    for type_, amount, status, txid, date in rows:
        text += (
            f" {type_}\n"
            f"💰 {amount}\n"
            f"📌 {status}\n"
            f"🧾 {txid}\n"
            f"🕒 {date}\n"
            f"──────────\n"
        )
    
    has_next = offset + PAGE_SIZE < total
    has_prev = page > 0

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="◀️", callback_data=f"{filter_type}_{page-1}" if has_prev else "ignore"),
            InlineKeyboardButton(text=f"{page+1}", callback_data="ignore"),
            InlineKeyboardButton(text="▶️", callback_data=f"{filter_type}_{page+1}" if has_next else "ignore"),
        ]
    ])
    await call.message.answer(text, reply_markup=kb)

@router.callback_query(lambda c: c.data.startswith("list_deposit"))
async def deposits(call: types.CallbackQuery):
    _, _, page = call.data.split("_")
    await show_list(call, "deposit", int(page))

@router.callback_query(lambda c: c.data.startswith("list_withdraw"))
async def withdraws(call: types.CallbackQuery):
    _, _, page = call.data.split("_")
    await show_list(call, "withdraw", int(page))

@router.callback_query(lambda c: c.data.startswith("deposit_") or c.data.startswith("withdraw_"))
async def paginate(call: types.CallbackQuery):
    filter_type, page = call.data.split("_")
    await show_list(call, filter_type, int(page))

@router.callback_query(lambda c: c.data == "ignore")
async def ignore(call: types.CallbackQuery):
    await call.answer()





@router.callback_query(lambda c: c.data == "menu_offers")
async def bonus(c: CallbackQuery):
    # جلب العروض من قاعدة البيانات
    current_text = await get_bonus_from_db()
    
    # إضافة زر للعودة للقائمة الرئيسية
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 العودة للقائمة الرئيسية", callback_data="back_to_main")]
    ])
    
    # عرض العروض مع زر العودة
    await c.message.edit_text(
        text=f"🎉 *العروض والبونصات الحالية*\n\n{current_text}",
        parse_mode="Markdown",
        reply_markup=back_kb
    )
    
    await c.answer()

@router.callback_query(lambda c: c.data == "menu_direct_games")
async def process_direct_games(c: CallbackQuery):
    
    # بناء كيبورد الألعاب مع إضافة زر العودة في النهاية
    games_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎰 Golden Tree: Buy Bonus", url="https://www.ichancy.com/ar/casino/slots/all/36/pascal-gaming/77612-500008078-golden-tree:-buy-bonus?mode=real")
            ],
            [
                InlineKeyboardButton(text="🌳 Golden Tree", url="https://www.ichancy.com/ar/casino/slots/all/36/pascal-gaming/82711-500010058-golden-tree:-100-buy-bonus?mode=real"),
                InlineKeyboardButton(text="✨ Chancy: Buy Bonus", url="https://www.ichancy.com/ar/casino/slots/all/36/pascal-gaming/56245-420031709-golden-tree?mode=real")
            ],
            [
                InlineKeyboardButton(text="💎 Golden Tree: 100 Buy Bonus", url="https://www.ichancy.com/ar/casino/slots/all/247/pascal-gaming/99381-555573886-chancy-buy-bonus?mode=real"),
                InlineKeyboardButton(text="🍯 Honey Money", url="https://www.ichancy.com/ar/casino/slots/all/51/pascal-gaming/57564-420032128-honey-money?mode=real")
            ],
            # سطر إضافي لزر العودة إلى القائمة الرئيسية
            [
                InlineKeyboardButton(text="🔙 العودة للقائمة الرئيسية", callback_data="back_to_main")
            ]
        ]
    )

    # تعديل الرسالة الحالية بدلاً من إرسال رسالة جديدة
    await c.message.edit_text(
        text="🎮 *دخول مباشر للألعاب*\n\nيرجى اختيار اللعبة التي تريدها من الأزرار أدناه للتحويل الفوري:",
        parse_mode="Markdown",
        reply_markup=games_kb
    )
    
    await c.answer()









# 1. معالج زر "جواهري"
@router.callback_query(F.data == "my_gemss")
async def process_my_gems(c: CallbackQuery, state: FSMContext):
    await state.clear()  # مسح أي حالة معلقة منعاً للتداخل
    user_id = c.from_user.id
    
    # جلب عدد الجواهر من قاعدة البيانات
    user_gems = await get_gems(user_id) 
    
    msg_text = (
        f"💎 <b>عدد مجوهراتك الحالي:</b> {user_gems} جوهرة.\n\n"
        "ℹ️ <b>كيف تحصل على الجواهر؟</b>\n"
        "تحصل تلقائياً على 1 جوهرة مجانية عند القيام بأي عملية شحن/إيداع بقيمة 20,000 ليرة أو أكثر داخل البوت!"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 اذهب للاستبدال", callback_data="exchange_menu")]
    ])
    
    # تحويل الـ parse_mode إلى HTML لضمان استقرار النص والرموز
    await c.message.edit_text(text=msg_text, reply_markup=kb, parse_mode="HTML")
    await c.answer()


# 2. معالج قائمة الاستبدال وعمليات الخصم
@router.callback_query(F.data.in_({"exchange_menu", "ex_1", "ex_5", "ex_10"}))
async def process_exchange_menu(c: CallbackQuery, state: FSMContext):
    await state.clear()  # مسح أي حالة معلقة منعاً للتداخل
    user_id = c.from_user.id
    data = c.data

    # أ) إذا كان المستخدم يطلب استعراض قائمة الأسعار
    if data == "exchange_menu":
        msg_text = (
            "🔄 <b>قائمة استبدال الجواهر بالرصيد:</b>\n\n"
            "💎 1 جوهرة  ⬅️  💰 400 ليرة رصيد\n"
            "💎 5 جواهر  ⬅️  💰 2400 ليرة رصيد (🔥 عرض خاص)\n"
            "💎 10 جواهر ⬅️  💰 6000 ليرة رصيد (💥 عرض فخم)\n\n"
            "اضغط على الخيار المناسب لك من الأسفل للاستبدال الفوري:"
        )
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💎 1 جوهرة ⬅️ 400 ليرة", callback_data="ex_1")],
            [InlineKeyboardButton(text="💎 5 جواهر ⬅️ 2400 ليرة", callback_data="ex_5")],
            [InlineKeyboardButton(text="💎 10 جواهر ⬅️ 6000 ليرة", callback_data="ex_10")],
            [InlineKeyboardButton(text="🔙 عودة", callback_data="my_gemss")]
        ])
        
        await c.message.edit_text(text=msg_text, reply_markup=kb, parse_mode="HTML")
        await c.answer()

    # ب) إذا ضغط على أحد خيارات الاستبدال الفعلية
    elif data in ["ex_1", "ex_5", "ex_10"]:
        # تحديد القيم بناءً على الاختيار
        if data == "ex_1":
            gems_need, balance_give = 1, 400
        elif data == "ex_5":
            gems_need, balance_give = 5, 2400
        else:  # ex_10
            gems_need, balance_give = 10, 6000

        # تنفيذ عملية الاستبدال في قاعدة البيانات
        success = await exchange_gems_to_balance(user_id, gems_need, balance_give)

        if success:
            # إرسال تنبيه علوي بنجاح العملية
            await c.answer("✅ تم الاستبدال بنجاح! تم إضافة الرصيد إلى حسابك.", show_alert=True)
            
            # تحديث نص الرسالة لتأكيد العملية
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 العودة لقائمة الجواهر", callback_data="my_gemss")]
            ])
            await c.message.edit_text(
                text=f"🎉 <b>عملية ناجحة!</b>\nتم استبدال {gems_need} جوهرة بـ {balance_give:,} ليرة رصيد بنجاح.",
                reply_markup=kb,
                parse_mode="HTML"
            )
        else:
            # إرسال تنبيه علوي بالرفض دون تعديل الرسالة
            await c.answer("❌ عذراً، رصيد الجواهر لديك لا يكفي لإتمام هذه العملية!", show_alert=True)










# 1. عند ضغط المستخدم على زر الدعم
@router.callback_query(F.data == "menu_msg_admin")
async def support_start(callback: CallbackQuery, state: FSMContext):
    await state.clear() # مسح أي حالة معلقة منعاً للتداخل
    
    # تنبيه التليغرام بانتهاء الضغطة ومنع تعليق الزر
    await callback.answer() 
    
    # إرسال الرسالة للمستخدم
    await callback.message.answer("🙋‍♂️ <b>قسم الدعم الفني:</b>\n\nاكتب رسالتك أو استفسارك الآن بالتفصيل في رسالة واحدة، وسيتم تحويلها مباشرة للمسؤولين:")
    await state.set_state(SupportStates.waiting_for_user_msg)


# 2. استقبال رسالة المستخدم وإرسالها للمجموعة وحفظ البيانات في الجدول
@router.message(SupportStates.waiting_for_user_msg)
async def support_process_msg(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else "لا يوجد"
    
    support_msg = (
        f"📩 <b>رسالة دعم فني جديدة</b>\n\n"
        f"👤 <b>المرسل:</b> {message.from_user.full_name} ({username})\n"
        f"🆔 <b>الآيدي:</b> <code>{user_id}</code>\n\n"
        f"📝 <b>نص الرسالة:</b>\n{message.text}\n\n"
        f"<i>(للرد على هذا المستخدم، قم بعمل Reply مباشر على هذه الرسالة واكتب ردك)</i>"
    )
    
    try:
        # إرسال الرسالة للمجموعة (استخدام message.bot يجلب كائن البوت تلقائياً)
        sent_msg = await message.bot.send_message(chat_id=ADMIN_GROUP_ID, text=support_msg, parse_mode="HTML")
        
        # حفظ البيانات في جدول الـ support_tickets
        await save_support_ticket(group_message_id=sent_msg.message_id, user_id=user_id)
        
        await message.answer("✅ تم إرسال رسالتك إلى الدعم الفني بنجاح.\nسيأتيك الرد هنا فوراً بمجرد مراجعتها! ⏳")
        await state.clear()
        
    except Exception as e:
        print(f"🚨 خطأ أثناء إرسال الرسالة للمجموعة: {e}")
        await message.answer("❌ عذراً، حدث خطأ داخلي أثناء إرسال رسالتك.")


# 3. مراقبة الردود (Reply) داخل مجموعة الإدارة ونقلها للمستخدم تلقائياً
@router.message(F.chat.id == ADMIN_GROUP_ID, F.reply_to_message)
async def admin_reply_handler(message: Message, bot: Bot):
    # جلب آيدي الرسالة الأصلية التي قام الآدمن بعمل Reply عليها
    replied_msg_id = message.reply_to_message.message_id
    
    # البحث في قاعدة البيانات لمعرفة آيدي المستخدم المرتبط بهذه الرسالة
    try:
        target_user_id = await get_user_by_message(replied_msg_id)
    except Exception as e:
        print(f"🚨 خطأ أثناء جلب بيانات التذكرة من الداتابيز: {e}")
        return
    
    # إذا لم يجد المستخدم، فهذا يعني أن الآدمن يعمل Reply على رسالة عادية
    if not target_user_id:
        return

    try:
        # إرسال ترويسة تنبيهية للمستخدم أولاً
        await bot.send_message(
            chat_id=target_user_id, 
            text="🔔 <b>وصلك رد جديد من الدعم الفني:</b>", 
            parse_mode="HTML"
        )
        
        # نسخ رد الآدمن بالكامل وإرساله للمرسل
        await message.copy_to(chat_id=target_user_id)
        
        # وضع تفاعل علامة (✅) على رسالة الآدمن
        try:
            await message.react([{"type": "emoji", "emoji": "✅"}])
        except Exception:
            pass
            
    except Exception as e:
        print(f"🚨 فشل تحويل الرد للمستخدم: {e}")
        await message.reply("❌ لم يتمكن البوت من إرسال الرد للمستخدم، قد يكون قام بحظر البوت أو أن حساب التليغرام معطل.")










