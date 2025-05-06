# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler
)

# تنظیمات پایه
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# مراحل گفتگو
GET_TASK, GET_DATE = range(2)

# دیتابیس ساده
tasks_db = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """منوی اصلی با صفحه کلید شیک"""
    keyboard = [
        ['➕ ثبت وظیفه جدید'],
        ['📅 لیست وظایف', '⏰ یادآوری ها'],
        ['ℹ️ راهنما']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "✋ سلام! به **ربات شخصی مدیریت کارها** خوش آمدید!\n\n"
        "✅ می‌توانم:\n"
        "- کارهایت را با تاریخ ذخیره کنم\n"
        "- روز قبل بهت یادآوری کنم\n"
        "- هرچه به مهلت نزدیک‌تر شوی، بیشتر هشدار دهم!",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع فرآیند ثبت وظیفه"""
    await update.message.reply_text(
        "📝 لطفاً عنوان وظیفه را بنویسید:\n"
        "مثال: «پرداخت قبض برق»"
    )
    return GET_TASK

async def save_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ذخیره عنوان وظیفه"""
    context.user_data['task'] = update.message.text
    await update.message.reply_text(
        "⏳ لطفاً **تاریخ شمسی** مهلت انجام را وارد کنید:\n"
        "مثال: 1403-05-20"
    )
    return GET_DATE

async def save_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ذخیره تاریخ و تکمیل فرآیند"""
    user_id = update.message.from_user.id
    task = context.user_data['task']
    due_date = update.message.text
    
    if user_id not in tasks_db:
        tasks_db[user_id] = []
    
    tasks_db[user_id].append({
        'title': task,
        'due_date': due_date,
        'notified': False
    })
    
    await update.message.reply_text(
        f"✅ **وظیفه ثبت شد:**\n"
        f"📌 {task}\n"
        f"⏰ تا تاریخ {due_date}\n\n"
        f"یک روز قبل به شما یادآوری می‌کنم!",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست وظایف"""
    user_id = update.message.from_user.id
    if user_id in tasks_db and tasks_db[user_id]:
        tasks = "\n\n".join(
            f"▫️ {task['title']}\n⏳ {task['due_date']}" 
            for task in tasks_db[user_id]
        )
        await update.message.reply_text(
            f"📜 **وظایف شما:**\n\n{tasks}",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("ℹ️ هنوز هیچ وظیفه‌ای ثبت نکرده‌اید.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لغو عملیات جاری"""
    await update.message.reply_text("❌ عملیات فعلی لغو شد.")
    return ConversationHandler.END

async def check_reminders(context: ContextTypes.DEFAULT_TYPE):
    """بررسی روزانه برای یادآوری"""
    for user_id, tasks in tasks_db.items():
        for task in tasks:
            if not task['notified']:
                # اینجا منطق بررسی تاریخ و ارسال یادآوری اضافه شود
                pass

def main():
    """تنظیم و اجرای ربات"""
    app = Application.builder().token("7916992369:AAHRo1Se9hxVvTOF2wgsw2MHCrXM0acSXn0").build()

    # گفتگو برای ثبت وظیفه
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^➕ ثبت وظیفه جدید$'), add_task)],
        states={
            GET_TASK: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_task)],
            GET_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_date)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    # ثبت هندلرها
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.Regex('^📅 لیست وظایف$'), list_tasks))
    
    # تنظیم بررسی روزانه یادآوری‌ها
    job_queue = app.job_queue
    job_queue.run_repeating(check_reminders, interval=86400)  # هر 24 ساعت

    logger.info("✅ ربات مدیریت وظایف فعال شد!")
    app.run_polling()

if __name__ == '__main__':
    main()