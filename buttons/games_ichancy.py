from aiogram import Router
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
router = Router()

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery


@router.callback_query(lambda c: c.data == "menu_sections")
async def process_sections(c: CallbackQuery):
    
    # بناء الأزرار الـ Inline للأقسام مع إضافة زر العودة في النهاية
    sections_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="ألعاب", url="https://www.ichancy.com/ar/for-test"),
                InlineKeyboardButton(text="ألعاب تلفاز", url="https://www.ichancy.com/ar/tv-bet")
            ],
            [
                InlineKeyboardButton(text="كازينو مباشر", url="https://www.ichancy.com/ar/live-casino"),
                InlineKeyboardButton(text="كازينو", url="https://www.ichancy.com/ar/casino/slots/all")
            ],
            # سطر إضافي لزر العودة للقائمة الرئيسية
            [
                InlineKeyboardButton(text="🔙 العودة للقائمة الرئيسية", callback_data="back_to_main")
            ]
        ]
    )
    
    # تعديل الرسالة الحالية لعرض الأقسام
    await c.message.edit_text(
        text="🕹 *أقسام ايشانسي*\n\nإختر القسم الذي تريده من الأزرار أدناه للانتقال السريع:",
        parse_mode="Markdown",
        reply_markup=sections_kb
    )
    
    # إنهاء حالة التحميل على الزر
    await c.answer()