from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🎰 ichancy", callback_data="menu_ichancy"),
            InlineKeyboardButton(text="💳 شحن رصيد في البوت", callback_data="menu_bot_recharge")
        ],
        [
            InlineKeyboardButton(text="💸 سحب رصيد من البوت", callback_data="menu_bot_withdraw"),
            InlineKeyboardButton(text="👥 نظام الاحالات", callback_data="menu_referrals")
        ],
        [
            InlineKeyboardButton(text="🎁 كود هدية", callback_data="menu_gift_code"),
            InlineKeyboardButton(text="💝 اهداء رصيد", callback_data="menu_gift_balance")
        ],
        [
            InlineKeyboardButton(text="📨 رسالة للادمن", callback_data="menu_msg_admin")
        ],
        [
            InlineKeyboardButton(text="📚 الشروحات", callback_data="menu_tutorials"), # هاد الزر يلي بيفتح قائمة الشروحات السابقة
            InlineKeyboardButton(text="📜 السجل", callback_data="menu_logs")
        ],
        [
            InlineKeyboardButton(text="💎 جواهري", callback_data="my_gemss"),
            InlineKeyboardButton(text="🔄 استبدال الجواهر", callback_data="exchange_menu")
        ],
        [
            InlineKeyboardButton(text="🎉 البونصات والعروض الحالية", callback_data="menu_offers")
        ],
        [
            InlineKeyboardButton(text="🎮 دخول مباشر للالعاب", callback_data="menu_direct_games"),
            InlineKeyboardButton(text="🕹 أقسام ايشانسي", callback_data="menu_sections")
        ],
        [
            # إذا كان هاد الزر لتحميل التطبيق، يمكنك وضع رابط مباشر (url) بدلاً من callback_data
            InlineKeyboardButton(text="📱 Ichancy Apk", url="https://android.betcoapps.com/novichok/ichancy_com/ichancy_com.apk?dl=1") 
        ],
        [
            InlineKeyboardButton(text="💰 الرصيد", callback_data="menu_check_balance")
        ]
    ]
)

explanations = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❓ ما هو موقع Ichancy؟", callback_data="explanations_0")],
        [InlineKeyboardButton(text="💰 كيفية شحن الرصيد ضمن بوت Ichancy", callback_data="explanations_1")],
        [InlineKeyboardButton(text="👤 كيفية إنشاء حساب Ichancy جديد", callback_data="explanations_2")],
        [InlineKeyboardButton(text="💳 كيفيّة سحب الرصيد من بوت Ichancy", callback_data="explanations_3")],
        [InlineKeyboardButton(text="🔄 كيفية شحن رصيد ضمن حساب Ichancy", callback_data="explanations_4")],
        [InlineKeyboardButton(text="💸 كيفية سحب رصيد من حساب Ichancy", callback_data="explanations_5")],
        [InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="explanations_6")]
    ])

ichancymenu = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="📝 إنشاء حساب Ichancy", callback_data="register_ichancy")
        ],
        [
            InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="back_to_main")
        ]
    ]
)

# 2. كيبورد المستخدم المسجل بالفعل (Inline)
ichancymenuregistered = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 شحن رصيد بالحساب", callback_data="deposit_ichancy"),
            InlineKeyboardButton(text="💸 سحب رصيد من الحساب", callback_data="withdraw_ichancy")
        ],
        [
            InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="back_to_main")
        ]
    ]
)

adminmenu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="المستخدمين")],
        [KeyboardButton(text="حسابات ichancy")],
        [KeyboardButton(text="اضافة كود")],
        [KeyboardButton(text="📜 سجل مستخدم")],
        [KeyboardButton(text="💰 توزيع أرباح الإحالات")],  
        [KeyboardButton(text="تعديل نص البونصات و العروض الحالية")], 
        [KeyboardButton(text="اضافة او حذف البونص")], 
        [KeyboardButton(text="الإذاعة")],
        [KeyboardButton(text="القائمة الرئيسية")],
    ],
    resize_keyboard=True, 
    input_field_placeholder="👨‍✈️ لوحة تحكم الإدارة"
)

withdraw_bot_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📱 سيرياتيل كاش", callback_data="WithdrawSy"),
                InlineKeyboardButton(text="💳 شام كاش", callback_data="WithdrawSH")
            ],
            [
                InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="back_to_main")
            ]
        ]
    )
