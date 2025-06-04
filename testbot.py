import json
import random
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters, CallbackQueryHandler
)

# 👉 নিজের বটের টোকেন ও চ্যানেল ID-গুলো দিয়ে দাও
TOKEN = "7645340647:AAEVYTWHYCZhhQfd1QVlouLpsIyE61YQsL4"
CHANNELS = [
    "-1002271283410",  # Online Income Max
    "-1002476961589"   # Technical Monster Official
]
DATA_FILE = "database.json"
PHOTO_PATH = "airdrop_image.jpg"

# ডাটাবেজ লোড/ক্রিয়েট
try:
    with open(DATA_FILE, "r") as f:
        db = json.load(f)
except:
    db = {}

def save_db():
    with open(DATA_FILE, "w") as f:
        json.dump(db, f, indent=4)

def get_user_data(user_id):
    uid = str(user_id)
    if uid not in db:
        db[uid] = {
            "points": 0,
            "referrals": [],
            "verified": False,
            "inviter": None,
            "withdraw_info": None
        }
    return db[uid]

# ভেরিফিকেশন puzzle
def generate_puzzle():
    a, b = random.randint(1, 9), random.randint(1, 9)
    return f"{a} + {b} = ?", a + b

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = get_user_data(user.id)

    if user_data["verified"]:
        await send_airdrop_intro(update, context)
        return

    if context.args:
        referrer_id = context.args[0]
        if str(referrer_id) != str(user.id):
            user_data["inviter"] = referrer_id

    question, answer = generate_puzzle()
    context.user_data["answer"] = answer
    await update.message.reply_text(
        f"🤖 হিউম্যান ভেরিফিকেশন প্রশ্ন: {question}\nউত্তর দিন:"
    )

# puzzle উত্তর
async def puzzle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = get_user_data(user.id)

    if user_data["verified"] or "answer" not in context.user_data:
        return

    try:
        user_answer = int(update.message.text)
        correct_answer = context.user_data["answer"]

        if user_answer == correct_answer:
            user_data["verified"] = True
            save_db()
            await update.message.reply_text(
                "✅ ভেরিফিকেশন সম্পন্ন হয়েছে! ওয়েলকামিং পোস্ট পাঠানো হচ্ছে..."
            )
            await send_airdrop_intro(update, context)
        else:
            await update.message.reply_text(
                "❌ ভুল উত্তর! আবার চেষ্টা করুন /start দিয়ে।"
            )
    except:
        await update.message.reply_text("⚠️ দয়া করে শুধুমাত্র সংখ্যায় উত্তর দিন।")

# Airdrop পোস্ট
async def send_airdrop_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caption = (
        "🔥 *Airdrop Fire* শুরু হয়েছে!\n"
        "💰 পুরস্কার পুল: ১০,০০০ USDT\n\n"
        "✅ নিচের দুইটি চ্যানেলে জয়েন করুন এবং তারপর '✅ আমি জয়েন করেছি' বাটনে ক্লিক করুন:"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📢 Online Income Max", url="https://t.me/onlineincome_max")
        ],
        [
            InlineKeyboardButton("📢 Technical Monster", url="https://t.me/Technical_Monster_Official")
        ],
        [
            InlineKeyboardButton("✅ আমি জয়েন করেছি", callback_data="joined")
        ]
    ])

    try:
        with open(PHOTO_PATH, "rb") as photo:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=photo,
                caption=caption,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            print("✅ Photo sent successfully.")
    except Exception as e:
        print(f"❌ Photo sending error: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=caption + "\n\n⚠️ [ছবি লোড হয়নি, শুধু টেক্সট দেখানো হচ্ছে]",
            parse_mode="Markdown",
            reply_markup=keyboard
        )

# Join বাটন হ্যান্ডলার
async def handle_joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    user_data = get_user_data(user_id)

    for channel_id in CHANNELS:
        try:
            member = await context.bot.get_chat_member(channel_id, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                await query.answer("❌ এখনো সব চ্যানেলে জয়েন করেননি!", show_alert=True)
                return
        except Exception as e:
            print(f"Channel check error: {e}")
            await query.answer("⚠️ চ্যানেল চেক করতে সমস্যা হচ্ছে।", show_alert=True)
            return

    if user_data["inviter"]:
        inviter_data = get_user_data(user_data["inviter"])
        if user_id not in inviter_data["referrals"]:
            inviter_data["referrals"].append(user_id)
            inviter_data["points"] += 5
            await context.bot.send_message(
                chat_id=user_data["inviter"],
                text=f"🎉 নতুন রেফারেল! ৫ কয়েন পেয়েছেন। মোট: {inviter_data['points']}"
            )
    user_data["points"] += 5
    save_db()

    await query.edit_message_text(
        "✅ ধন্যবাদ! আপনি সফলভাবে জয়েন করেছেন। এখন আপনি রেফার করতে পারেন /refer দিয়ে।"
    )

# /refer
async def refer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = get_user_data(user.id)
    link = f"https://t.me/{context.bot.username}?start={user.id}"
    await update.message.reply_text(
        f"🔗 আপনার রেফার লিংক:\n{link}\n👥 রেফার: {len(user_data['referrals'])}\n💸 কয়েন: {user_data['points']}"
    )

# /withdraw
async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = get_user_data(user.id)

    if user_data["points"] < 300:
        await update.message.reply_text("❌ উইথড্র করতে হলে কমপক্ষে ৩০০ কয়েন লাগবে।")
        return

    await update.message.reply_text(
        "✅ আপনার বিকাশ/নগদ নম্বর পাঠান (উদাহরণ: 01xxxxxxxxx):"
    )
    context.user_data["awaiting_withdraw_number"] = True

# Withdraw নাম্বার নেওয়া
async def handle_withdraw_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_withdraw_number"):
        number = update.message.text.strip()
        if not re.match(r"^01\d{9}$", number):
            await update.message.reply_text("⚠️ সঠিক ১১-সংখ্যার নাম্বার দিন (০১ দিয়ে শুরু)।")
            return

        user_data = get_user_data(update.effective_user.id)
        user_data["withdraw_info"] = number
        save_db()

        await update.message.reply_text(
            f"✅ উইথড্র রিকোয়েস্ট নেওয়া হয়েছে!\nবিকাশ/নগদ: {number}\n⚠️ অ্যাডমিন যাচাই করবে।"
        )
        context.user_data["awaiting_withdraw_number"] = False

# /help
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚙️ কমান্ডসমূহ:\n/start - শুরু করুন\n/refer - রেফার লিংক\n/withdraw - উইথড্র\n/help - সহায়তা"
    )

# Text router
async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_withdraw_number"):
        await handle_withdraw_number(update, context)
    elif "answer" in context.user_data:
        await puzzle_answer(update, context)
    else:
        await update.message.reply_text("⚠️ দয়া করে /start দিয়ে শুরু করুন।")

# main
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("refer", refer))
    app.add_handler(CommandHandler("withdraw", withdraw))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CallbackQueryHandler(handle_joined, pattern="^joined$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

    print("🤖 Bot is running...")
    app.run_polling()
