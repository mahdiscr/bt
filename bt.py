from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, filters
import re

# دیتابیس ساده برای ذخیره اطلاعات کاربران (فقط Mahdi و Nilo باقی می‌مانند)
user_profiles = {
    "7284988649532227585": {"name": "Mahdi", "category": "Leader", "mode": None, "achievements": ["Leader"]},
    "7265369518667399169": {"name": "Nilo", "category": "Leader", "mode": None, "achievements": ["Leader"]}
}

# متن بنر اخبار
news_banner = "📢 اخبار جدید کلن: به زودی رویداد ویژه‌ای برگزار می‌شود! آماده باشید! 🎉"

# کلاس برای مدیریت حالت‌های کاربران
class UserState:
    def __init__(self):
        self.states = {}

    def set_state(self, chat_id, state):
        self.states[chat_id] = state

    def get_state(self, chat_id):
        return self.states.get(chat_id)

    def clear_state(self, chat_id):
        if chat_id in self.states:
            del self.states[chat_id]

user_states = UserState()

# ذخیره message_id پیام‌های هر دسته در کانال
channel_messages = {}  # به‌صورت {category: message_id}

# آیدی کانال
CHANNEL_ID = "@oro_clan"  # جایگزین کنید با آیدی واقعی کانال

# تابع برای بررسی اعتبار یو‌آیدی
def is_valid_user_id(user_id):
    # یو‌آیدی فقط می‌تواند شامل حروف لاتین، اعداد و کاراکترهای خاص مانند _ باشد.
    pattern = r'^[a-zA-Z0-9_]+$'
    return re.match(pattern, user_id) is not None

# تابع برای ایجاد دکمه‌های شیشه‌ای برگشت به صفحه اصلی
def get_back_to_main_menu_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 برگشت به صفحه اصلی", callback_data='back_to_main')]])

# تابع برای ایجاد صفحه اصلی
def get_main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 اعضای کلن", callback_data='clan_members')],
        [InlineKeyboardButton("📰 اخبار های کلن", callback_data='clan_news')],
        [InlineKeyboardButton("👑 ادمین", callback_data='admin')]
    ])

# تابع برای ایجاد منوی اعضای کلن
def get_clan_members_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📜 لیست اعضای کلن", callback_data='list_members')],
        [InlineKeyboardButton("📜 فهرست اعضای دسته یک", callback_data='list_category_1')],
        [InlineKeyboardButton("🔍 بررسی عضویت", callback_data='check_membership')],
        [InlineKeyboardButton("🔙 برگشت به صفحه اصلی", callback_data='back_to_main')]
    ])

# تابع برای ایجاد منوی ادمین
def get_admin_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ اضافه کردن کاربر", callback_data='add_user')],
        [InlineKeyboardButton("➖ حذف کاربر", callback_data='remove_user')],
        [InlineKeyboardButton("📢 تنظیم بنر اخبار", callback_data='set_news_banner')],
        [InlineKeyboardButton("🏆 مدیریت افتخارات کاربران", callback_data='manage_achievements')],
        [InlineKeyboardButton("📤 اپلود همگانی", callback_data='bulk_upload')],
        [InlineKeyboardButton("🔙 برگشت به صفحه اصلی", callback_data='back_to_main')]
    ])

# تابع برای ارسال صفحه اصلی
async def send_main_menu(update: Update, context: CallbackContext, message: str = None):
    welcome_message = (
        message or "🌟 **سلام! به ربات کلن oro خوش آمدید.** 🌟\n\n"
        "ما اینجا هستیم تا تجربه‌ی بهتری از مدیریت و تعامل با کلن براتون فراهم کنیم.\n\n"
        "لطفا یکی از گزینه‌های زیر را انتخاب کنید:"
    )
    if update.message:
        await update.message.reply_text(welcome_message, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")
    else:
        await update.callback_query.edit_message_text(welcome_message, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")

# تابع برای ارسال یا ادیت لیست دسته‌بندی‌ها در کانال
async def update_channel_members_list(context: CallbackContext):
    global channel_messages

    # ایجاد لیست دسته‌بندی‌ها
    categories = {}
    leaders = []  # لیست لیدرها

    # جمع‌آوری اعضا بر اساس دسته‌بندی
    for user_id, user in user_profiles.items():
        category = user['category']
        if category == "Leader":
            leaders.append(f"👑 {user['name']} ({user_id})")
        else:
            if category not in categories:
                categories[category] = []
            # اگر دسته یک باشد، دستاوردها را اضافه کنید
            if category == "1":
                achievements = "🏆 " + ", ".join(user['achievements']) if user['achievements'] else "🛑 بدون دستاورد"
                categories[category].append(f"👤 {user['name']} ({user_id})\n{achievements}")
            else:
                # برای سایر دسته‌ها فقط نام و یو‌آیدی نمایش داده شود
                categories[category].append(f"👤 {user['name']} ({user_id})")

    # ارسال یا ادیت پیام‌ها برای هر دسته (حتی دسته‌های خالی)
    all_categories = {"1", "2", "3", "4", "5"}  # دسته‌های یک تا پنج
    for category in sorted(all_categories):
        if category in categories:
            members = categories[category]
            message_text = f"🌟 **دسته {category}:**\n\n"
            message_text += "\n".join(members)
        else:
            message_text = f"🌟 **دسته {category}:**\n\n🛑 هیچ عضوی وجود ندارد."

        if category in channel_messages:
            # اگر پیام قبلی وجود دارد، آن را ادیت کنید
            try:
                await context.bot.edit_message_text(
                    chat_id=CHANNEL_ID,
                    message_id=channel_messages[category],
                    text=message_text,
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"خطا در ادیت پیام برای دسته {category}: {e}")
        else:
            # اگر پیام قبلی وجود ندارد، پیام جدید ارسال کنید و message_id را ذخیره کنید
            sent_message = await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=message_text,
                parse_mode="Markdown"
            )
            channel_messages[category] = sent_message.message_id

    # ارسال یا ادیت پیام برای لیدرها
    if leaders:
        message_text = "👑 **لیست لیدرها:**\n\n"
        message_text += "\n".join(leaders)
    else:
        message_text = "👑 **لیست لیدرها:**\n\n🛑 هیچ لیدری وجود ندارد."

    if "Leader" in channel_messages:
        # اگر پیام قبلی وجود دارد، آن را ادیت کنید
        try:
            await context.bot.edit_message_text(
                chat_id=CHANNEL_ID,
                message_id=channel_messages["Leader"],
                text=message_text,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"خطا در ادیت پیام برای لیدرها: {e}")
    else:
        # اگر پیام قبلی وجود ندارد، پیام جدید ارسال کنید و message_id را ذخیره کنید
        sent_message = await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=message_text,
            parse_mode="Markdown"
        )
        channel_messages["Leader"] = sent_message.message_id# دستور /start
async def start(update: Update, context: CallbackContext) -> None:
    await send_main_menu(update, context)
    user_states.set_state(update.message.chat_id, "ASK_ROLE")

# پردازش کلیک روی دکمه‌ها
async def button_click(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    chat_id = query.message.chat_id
    data = query.data

    if data == "back_to_main":
        await send_main_menu(update, context)
        user_states.set_state(chat_id, "ASK_ROLE")
        return

    state = user_states.get_state(chat_id)

    if state == "ASK_ROLE":
        if data == "clan_members":
            await query.edit_message_text("لطفا یکی از گزینه‌های زیر را انتخاب کنید:", reply_markup=get_clan_members_menu_keyboard())
            user_states.set_state(chat_id, "CLAN_MEMBERS_MENU")
        elif data == "clan_news":
            await query.edit_message_text(news_banner, reply_markup=get_back_to_main_menu_keyboard())
            user_states.clear_state(chat_id)
        elif data == "admin":
            await query.edit_message_text("لطفا رمز عبور ادمین را وارد کنید:", reply_markup=get_back_to_main_menu_keyboard())
            user_states.set_state(chat_id, "ADMIN_PASSWORD")

    elif state == "CLAN_MEMBERS_MENU":
        if data == "list_members":
            members_list = "\n".join([
                "👤 نام: {} \n🆔 یو‌آیدی: {} \n🔹 دسته: {}\n".format(
                    user['name'],
                    user_id,
                    'Leader' if user['category'] == 'Leader' else f'دسته {user["category"]}'
                )
                for user_id, user in user_profiles.items()
            ])
            await query.edit_message_text(f"📋 **لیست اعضای کلن:**\n\n{members_list}", reply_markup=get_back_to_main_menu_keyboard())
            user_states.clear_state(chat_id)
        elif data == "list_category_1":
            category_1_members = [
                "👤 نام: {} \n🆔 یو‌آیدی: {} \n🏆 افتخارات: {}\n".format(
                    user['name'],
                    user_id,
                    ', '.join(user['achievements']) if user['achievements'] else 'بدون افتخار'
                )
                for user_id, user in user_profiles.items() if user['category'] == "1"
            ]
            if category_1_members:
                await query.edit_message_text(
                    "📋 **فهرست اعضای دسته یک:**\n\n" + "\n".join(category_1_members),
                    reply_markup=get_back_to_main_menu_keyboard(),
                    parse_mode="Markdown"
                )
            else:
                await query.edit_message_text("⚠️ هیچ عضوی در دسته یک وجود ندارد.", reply_markup=get_back_to_main_menu_keyboard())
            user_states.clear_state(chat_id)
        elif data == "check_membership":
            await query.edit_message_text("لطفا یو‌آیدی خود را وارد کنید:", reply_markup=get_back_to_main_menu_keyboard())
            user_states.set_state(chat_id, "USER_CHECK_MEMBERSHIP")

    elif state == "ADMIN_MENU":
        if data == "add_user":
            await query.edit_message_text("لطفا یو‌آیدی کاربر جدید را وارد کنید:", reply_markup=get_back_to_main_menu_keyboard())
            user_states.set_state(chat_id, "ADD_USER_ID")
        elif data == "remove_user":
            await query.edit_message_text("لطفا یو‌آیدی کاربری که می‌خواهید حذف کنید را وارد کنید:", reply_markup=get_back_to_main_menu_keyboard())
            user_states.set_state(chat_id, "REMOVE_USER_ID")
        elif data == "set_news_banner":
            await query.edit_message_text("لطفا متن بنر اخبار جدید را وارد کنید:", reply_markup=get_back_to_main_menu_keyboard())
            user_states.set_state(chat_id, "SET_NEWS_BANNER")
        elif data == "manage_achievements":
            await query.edit_message_text("لطفا یو‌آیدی کاربری که می‌خواهید افتخاراتش را مدیریت کنید وارد کنید:", reply_markup=get_back_to_main_menu_keyboard())
            user_states.set_state(chat_id, "MANAGE_ACHIEVEMENTS_USER_ID")
        elif data == "bulk_upload":
            await query.edit_message_text("لطفا رمز عبور ویژه را وارد کنید:", reply_markup=get_back_to_main_menu_keyboard())
            user_states.set_state(chat_id, "BULK_UPLOAD_PASSWORD")

    await query.answer()

# پردازش پیام‌های متنی
async def handle_message(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    user_input = update.message.text
    state = user_states.get_state(chat_id)

    if state == "ADMIN_PASSWORD":
        if user_input == "nilmah":
            await update.message.reply_text("احراز هویت موفق!\nلطفا انتخاب کنید:", reply_markup=get_admin_menu_keyboard())
            user_states.set_state(chat_id, "ADMIN_MENU")
        else:
            await update.message.reply_text("رمز عبور اشتباه است!", reply_markup=get_back_to_main_menu_keyboard())
            user_states.clear_state(chat_id)

    elif state == "USER_CHECK_MEMBERSHIP":
        if not is_valid_user_id(user_input):
            await update.message.reply_text("⚠️ یو‌آیدی نامعتبر است! فقط از حروف لاتین، اعداد و _ استفاده کنید.", reply_markup=get_back_to_main_menu_keyboard())
            return

        if user_input in user_profiles:
            profile = user_profiles[user_input]
            mode_text = "\nحالت: {}".format(profile['mode']) if profile['mode'] else ""
            achievements_text = "\n🏆 افتخارات: " + ", ".join(profile['achievements']) if profile['achievements'] else ""
            await update.message.reply_text(
                "✅ **عضویت تایید شد!**\n\n"
                "👤 نام: {}\n"
                "🆔 یو‌آیدی: {}\n"
                "🔹 دسته: {}{}{}".format(
                    profile['name'],
                    user_input,
                    profile['category'],
                    mode_text,
                    achievements_text
                ),
                reply_markup=get_back_to_main_menu_keyboard(),
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("⚠️ یو‌آیدی وارد شده در سیستم وجود ندارد.", reply_markup=get_back_to_main_menu_keyboard())
        user_states.clear_state(chat_id)

    elif state == "ADD_USER_ID":
        if not is_valid_user_id(user_input):
            await update.message.reply_text("⚠️ یو‌آیدی نامعتبر است! فقط از حروف لاتین، اعداد و _ استفاده کنید.", reply_markup=get_back_to_main_menu_keyboard())
            return

        await update.message.reply_text("لطفا نام کاربر را وارد کنید:", reply_markup=get_back_to_main_menu_keyboard())
        user_states.set_state(chat_id, f"ADD_USER_NAME:{user_input}")

    elif state and state.startswith("ADD_USER_NAME:"):
        user_id = state.split(":")[1]
        await update.message.reply_text("لطفا دسته کاربر را وارد کنید:", reply_markup=get_back_to_main_menu_keyboard())
        user_states.set_state(chat_id, f"ADD_USER_CATEGORY:{user_id}:{user_input}")

    elif state and state.startswith("ADD_USER_CATEGORY:"):
        user_id = state.split(":")[1]
        user_name = state.split(":")[2]
        user_profiles[user_id] = {"name": user_name, "category": user_input, "mode": None, "achievements": []}
        await update.message.reply_text(f"✅ کاربر با یو‌آیدی {user_id} اضافه شد.", reply_markup=get_back_to_main_menu_keyboard())
        user_states.clear_state(chat_id)
        await update_channel_members_list(context)  # به‌روزرسانی لیست در کانال

    elif state == "REMOVE_USER_ID":
        if not is_valid_user_id(user_input):
            await update.message.reply_text("⚠️ یو‌آیدی نامعتبر است! فقط از حروف لاتین، اعداد و _ استفاده کنید.", reply_markup=get_back_to_main_menu_keyboard())
            return

        if user_input in user_profiles:
            del user_profiles[user_input]
            await update.message.reply_text(f"✅ کاربر با یو‌آیدی {user_input} حذف شد.", reply_markup=get_back_to_main_menu_keyboard())
        else:
            await update.message.reply_text("⚠️ یو‌آیدی وارد شده در سیستم وجود ندارد!", reply_markup=get_back_to_main_menu_keyboard())
        user_states.clear_state(chat_id)
        await update_channel_members_list(context)  # به‌روزرسانی لیست در کانال

    elif state == "SET_NEWS_BANNER":
        global news_banner
        news_banner = user_input
        await update.message.reply_text("✅ بنر اخبار با موفقیت به‌روزرسانی شد!", reply_markup=get_back_to_main_menu_keyboard())
        user_states.clear_state(chat_id)

    elif state == "MANAGE_ACHIEVEMENTS_USER_ID":
        if not is_valid_user_id(user_input):
            await update.message.reply_text("⚠️ یو‌آیدی نامعتبر است! فقط از حروف لاتین، اعداد و _ استفاده کنید.", reply_markup=get_back_to_main_menu_keyboard())
            return

        if user_input in user_profiles:
            user_states.set_state(chat_id, f"ADD_ACHIEVEMENT:{user_input}")
            await update.message.reply_text("لطفا عنوان دستاورد جدید را وارد کنید:", reply_markup=get_back_to_main_menu_keyboard())
        else:
            await update.message.reply_text("⚠️ یو‌آیدی وارد شده در سیستم وجود ندارد!", reply_markup=get_back_to_main_menu_keyboard())
            user_states.clear_state(chat_id)

    elif state and state.startswith("ADD_ACHIEVEMENT:"):
        user_id = state.split(":")[1]
        if user_id in user_profiles:
            # جایگزینی دستاوردهای قدیمی با دستاورد جدید
            user_profiles[user_id]["achievements"] = [user_input]
            await update.message.reply_text(f"✅ دستاورد '{user_input}' به کاربر با یو‌آیدی {user_id} اضافه شد.", reply_markup=get_back_to_main_menu_keyboard())
        else:
            await update.message.reply_text("⚠️ یو‌آیدی وارد شده در سیستم وجود ندارد!", reply_markup=get_back_to_main_menu_keyboard())
        user_states.clear_state(chat_id)
        await update_channel_members_list(context)  # به‌روزرسانی لیست در کانال

    elif state == "BULK_UPLOAD_PASSWORD":
        if user_input == "Mahdiamam":
            await update.message.reply_text("احراز هویت موفق!\nلطفا فهرست اعضای جدید را به فرمت زیر ارسال کنید (هر عضو در یک خط):\nیو‌آیدی.نام کاربر.دسته کاربر\nمثال:\n123.test1.2\n124.test2.3", reply_markup=get_back_to_main_menu_keyboard())
            user_states.set_state(chat_id, "BULK_UPLOAD")
        else:
            await update.message.reply_text("رمز عبور اشتباه است!", reply_markup=get_back_to_main_menu_keyboard())
            user_states.clear_state(chat_id)

    elif state == "BULK_UPLOAD":
        lines = user_input.split("\n")
        added_users = []
        for line in lines:
            try:
                user_id, name, category = line.strip().split(".")
                if not is_valid_user_id(user_id):
                    await update.message.reply_text(f"⚠️ یو‌آیدی نامعتبر در خط: {line}", reply_markup=get_back_to_main_menu_keyboard())
                    continue

                if user_id not in user_profiles:
                    user_profiles[user_id] = {"name": name, "category": category, "mode": None, "achievements": []}
                    added_users.append(f"{user_id}: {name} ({category})")
                else:
                    await update.message.reply_text(f"⚠️ کاربر با یو‌آیدی {user_id} از قبل وجود دارد.", reply_markup=get_back_to_main_menu_keyboard())
            except ValueError:
                await update.message.reply_text(f"⚠️ خطا در پردازش خط: {line}", reply_markup=get_back_to_main_menu_keyboard())

        if added_users:
            await update.message.reply_text(
                "✅ اعضای زیر با موفقیت اضافه شدند:\n" + "\n".join(added_users),
                reply_markup=get_back_to_main_menu_keyboard()
            )
        else:
            await update.message.reply_text("⚠️ هیچ عضو جدیدی اضافه نشد.", reply_markup=get_back_to_main_menu_keyboard())
        user_states.clear_state(chat_id)
        await update_channel_members_list(context)  # به‌روزرسانی لیست در کانال

# تابع اصلی
def main() -> None:
    application = Application.builder().token("7565549970:AAFpSTTeII1KoqMdlTe8ZRblZDlMv2P8Erg").build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("ربات فعال شد و در حال گوش دادن به پیام‌ها است...")
    application.run_polling()

if __name__ == '__main__':
    main()