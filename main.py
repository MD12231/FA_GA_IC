import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
# استيراد أنواع الأوامر لإعداد المنيو
from aiogram.types import BotCommand, BotCommandScopeDefault

# استيراد إعدادات البوت والجروب
from config import TOKEN

# استيراد دوال تهيئة قاعدة البيانات من ملف db
from database.db import init_pool, init

# استيراد الراوترات
from ichancy.ichancy_api import initialize_tokens
from handlers import user, admin, referral

# 🛑 دالة إعداد أزرار القائمة (Menu)
async def setup_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="تشغيل البوت")
    ]
    # تعيين الأوامر لجميع المستخدمين بشكل افتراضي
    await bot.set_my_commands(commands=commands, scope=BotCommandScopeDefault())
    print("✅ تم تعيين قائمة الأوامر (Menu) بنجاح.")

async def main():
    # 1. تفعيل تسجيل الأحداث (Logging)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # 2. إنشاء كائن البوت والموزع
    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    print("جاري الاتصال بقاعدة البيانات...")
    try:
        # 3. أول خطوة: إنشاء حوض الاتصالات (Pool)
        await init_pool()
        print("✅ تم إنشاء حوض الاتصالات (Pool) بنجاح.")

        # 4. ثاني خطوة: إنشاء وفحص الجداول الاعتمادية
        await init()
        print("✅ تم التحقق من الجداول وإصلاحها بنجاح.")
        
        await initialize_tokens()

    except Exception as db_err:
        print(f"❌ فشل إقلاع قاعدة البيانات: {db_err}")
        return

    # 5. تضمين الراوترات (Routers)
    dp.include_router(user.router)
    dp.include_router(admin.router)
    dp.include_router(referral.router)

    # 💡 استدعاء دالة بناء المنيو هنا قبل تشغيل الـ Polling
    await setup_bot_commands(bot)

    # 6. حذف أي تحديثات معلقة
    await bot.delete_webhook(drop_pending_updates=True)

    # 7. إطلاق البوت والبدء في استقبال رسائل المستخدمين
    print("🚀 تم الاتصال بنجاح. البوت يعمل الآن ويستقبل الطلبات...")
    try:
        await dp.start_polling(bot)
    finally:
        # إغلاق الجلسة بأمان عند إيقاف البوت
        await bot.session.close()

if __name__ == "__main__":  # تم تصحيح name هنا لضمان عمل الشرط بشكل صحيح
    try:
        # تشغيل دالة الإقلاع الرئيسية عبر asyncio
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n🛑 تم إيقاف تشغيل البوت بأمان.")