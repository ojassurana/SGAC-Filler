import os
import json
import re
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters, ContextTypes
from validate_IC import validate_nric_fin
from clicker import download_arrival_card

# Conversation states
IC, DOB, EMAIL, ARRIVAL_DATE, SICK_QUESTION, CONFIRM_INFO = range(6)

# File to store user data
USER_DATA_FILE = "user_data.json"

# Email validation regex
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

# Load user data
def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

# Save user data
def save_user_data(data):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# Validate email format
def is_valid_email(email):
    return EMAIL_REGEX.match(email) is not None

# Start command for new users
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_data = load_user_data()
    
    # Check if user already has saved data
    if user_id in user_data:
        # User already exists, show confirmation like /enter
        saved_info = user_data[user_id]
        context.user_data['ic'] = saved_info['ic']
        context.user_data['dob'] = saved_info['dob']
        context.user_data['email'] = saved_info['email']
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Yes, correct", callback_data="info_correct"),
                InlineKeyboardButton("❌ No, update", callback_data="info_incorrect")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"👋 *Welcome back!*\n\n"
            f"*Your saved information:*\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"📋 *IC/FIN:* `{saved_info['ic']}`\n"
            f"🎂 *Date of Birth:* `{saved_info['dob']}`\n"
            f"📧 *Email:* `{saved_info['email']}`\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"Is this information still correct?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return CONFIRM_INFO
    
    # New user - show welcome and disclaimer
    # First message with welcome and disclaimer
    await update.message.reply_text(
        "*🇸🇬 Welcome to Singapore Arrival Card Bot!*\n\n"
        "I'll help you submit your arrival card quickly and easily.\n\n"
        "━━━━━━━━━━━━━━━━━\n"
        "⚠️ *Disclaimer*\n"
        "• _This bot is NOT affiliated with ICA_\n"
        "• We comply with *PDPA guidelines* to protect your personal data\n"
        "• By proceeding, you *consent to our data collection & usage*\n"
        "• [Privacy Policy](https://docs.google.com/document/d/1gc5WjsPp8KS6Is4FWrfEiZcODx1_0po76Qsiq6fxyUM/edit?usp=sharing) | [Terms & Conditions](https://docs.google.com/document/d/12W7b2xAbcxVBbfdcpU1xvMPcv_2gsk1D0ar0had1LsI/edit?usp=sharing)\n"
        "━━━━━━━━━━━━━━━━━",
        parse_mode='Markdown',
        disable_web_page_preview=True
    )
    
    # Second message asking for NRIC/FIN
    await update.message.reply_text(
        "📋 Please enter your *NRIC/FIN* number:",
        parse_mode='Markdown'
    )
    return IC

# Validate and save IC
async def get_ic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ic = update.message.text.strip().upper()
    
    if ic == "/CANCEL":
        await update.message.reply_text(
            "❌ *Process cancelled*\n\n"
            "Use /start to begin again.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    if not validate_nric_fin(ic):
        await update.message.reply_text(
            "❌ *Invalid NRIC/FIN format*\n\n"
            "Please enter a valid NRIC/FIN or type /cancel to stop:\n\n"
            "_Format: 1 letter + 7 digits + 1 letter_\n"
            "_Example: S1234567A_",
            parse_mode='Markdown'
        )
        return IC
    
    context.user_data['ic'] = ic
    await update.message.reply_text(
        f"✅ *IC Validated!*\n"
        f"Your IC: `{ic}`\n\n"
        f"📅 Please enter your *Date of Birth*:\n\n"
        f"_Format: DD/MM/YYYY_\n"
        f"_Example: 25/12/1990_",
        parse_mode='Markdown'
    )
    return DOB

# Get Date of Birth
async def get_dob(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dob = update.message.text.strip()
    
    # Validate date format
    try:
        datetime.strptime(dob, "%d/%m/%Y")
        context.user_data['dob'] = dob
        
        await update.message.reply_text(
            f"✅ *Date of Birth saved!*\n\n"
            f"📧 Please enter your *Email Address*:\n\n"
            f"_This will be used for your arrival card submission_\n"
            f"_Example: john.doe@gmail.com_",
            parse_mode='Markdown'
        )
        return EMAIL
    except ValueError:
        await update.message.reply_text(
            "❌ *Invalid date format*\n\n"
            "Please enter in DD/MM/YYYY format:\n"
            "_Example: 25/12/1990_",
            parse_mode='Markdown'
        )
        return DOB

# Get Email
async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip().lower()
    
    if not is_valid_email(email):
        await update.message.reply_text(
            "❌ *Invalid email format*\n\n"
            "Please enter a valid email address:\n"
            "_Example: john.doe@gmail.com_",
            parse_mode='Markdown'
        )
        return EMAIL
    
    context.user_data['email'] = email
    
    # Generate date buttons
    keyboard = generate_date_buttons()
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"✅ *Email saved!*\n\n"
        f"✈️ *When are you entering Singapore?*\n\n"
        f"Please select your arrival date:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return ARRIVAL_DATE

# Generate date buttons for the next 3 days
def generate_date_buttons():
    today = datetime.now()
    dates = []
    
    for i in range(3):
        date = today + timedelta(days=i)
        # Format as "DD/MM/" for the button (matching the clicker.py format)
        date_str = date.strftime("%d/%m/")
        # Display format for button text
        display_str = date.strftime("%d %B")
        if i == 0:
            display_str = f"📅 {display_str} (Today)"
        elif i == 1:
            display_str = f"📅 {display_str} (Tomorrow)"
        else:
            display_str = f"📅 {display_str}"
        
        dates.append([InlineKeyboardButton(display_str, callback_data=f"date_{date_str}")])
    
    return dates

# Handle arrival date selection
async def arrival_date_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Extract date from callback data
    date_str = query.data.replace("date_", "")
    context.user_data['arrival_date'] = date_str
    
    # Ask sick question
    keyboard = [
        [InlineKeyboardButton("✅ No symptoms & no YF travel", callback_data="sick_no")],
        [InlineKeyboardButton("❌ Have symptoms or YF travel", callback_data="sick_yes")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🏥 *Health Declaration*\n\n"
        "Do you have any of the following?\n\n"
        "🤒 *Symptoms:* fever, cough, sore throat, runny nose, etc.\n"
        "✈️ *Travel History:* visited [countries with Yellow Fever risk](https://www.moh.gov.sg/diseases-updates/yellow-fever) in the past 6 days\n\n"
        "*Please select your status:*",
        reply_markup=reply_markup,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )
    return SICK_QUESTION

# Handle sick question response
async def sick_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "sick_yes":
        await query.edit_message_text(
            "⚠️ *Health & Travel Advisory*\n\n"
            "Since you either:\n"
            "• Have health symptoms, or\n"
            "• Have visited a Yellow Fever risk country in the past 6 days\n\n"
            "You'll need to submit your arrival card manually and may need additional documentation.\n\n"
            "🔗 *Please visit:*\n"
            "https://eservices.ica.gov.sg/sgarrivalcard/\n\n"
            "ℹ️ For Yellow Fever requirements, check [MOH's website](https://www.moh.gov.sg/diseases-updates/yellow-fever)",
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        # Save user data for future use
        user_id = str(update.effective_user.id)
        user_data = load_user_data()
        user_data[user_id] = {
            'ic': context.user_data['ic'],
            'dob': context.user_data['dob'],
            'email': context.user_data['email']
        }
        save_user_data(user_data)
        return ConversationHandler.END
    
    # If not sick, proceed with submission
    await query.edit_message_text(
        "⏳ *Processing your submission...*\n\n"
        "Please wait while I:\n"
        "• Fill out your arrival card\n"
        "• Solve the security check\n"
        "• Generate your PDF\n\n"
        "_This may take 15-30 seconds..._",
        parse_mode='Markdown'
    )
    
    # Save user data
    user_id = str(update.effective_user.id)
    user_data = load_user_data()
    user_data[user_id] = {
        'ic': context.user_data['ic'],
        'dob': context.user_data['dob'],
        'email': context.user_data['email']
    }
    save_user_data(user_data)
    
    # Submit arrival card
    try:
        # Determine if it's NRIC (starts with S/T) or FIN (starts with F/G)
        ic = context.user_data['ic']
        is_resident = ic[0] in ['S', 'T']
        
        await download_arrival_card(
            resident=is_resident,
            arrival_date=context.user_data['arrival_date'],
            ic=ic,
            dob=context.user_data['dob'],
            email=context.user_data['email']
        )
        
        # Send the PDF
        pdf_path = f"{ic}.pdf"
        if os.path.exists(pdf_path):
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=open(pdf_path, 'rb'),
                caption=(
                    "✅ *Success!*\n\n"
                    "Your Singapore Arrival Card has been generated.\n\n"
                    "📱 *Next steps:*\n"
                    "• Save this PDF to your phone\n"
                    "• Show it at immigration if requested\n"
                ),
                parse_mode='Markdown'
            )
            # Send follow-up message about data management
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=(
                    "🔐 *Your Data & Quick Access*\n"
                    "━━━━━━━━━━━━━━━━━\n\n"
                    "⚡️ *Quick Re-entry:*\n"
                    "Just type /enter for your next trip!\n"
                    "No need to fill in details again 🎉\n\n"
                    "🗑 *Want to delete your data?*\n"
                    "Use /delete to remove all your\n"
                    "stored information immediately\n\n"
                    "See you on your next trip! 🇸🇬"
                ),
                parse_mode='Markdown'
            )
            # Clean up the PDF file
            os.remove(pdf_path)
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=(
                    "❌ *Generation Failed*\n\n"
                    "Unable to generate your arrival card.\n\n"
                    "Please try again with /start or submit manually at:\n"
                    "https://eservices.ica.gov.sg/sgarrivalcard/"
                ),
                parse_mode='Markdown'
            )
    except Exception as e:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=(
                f"❌ *Error Occurred*\n\n"
                f"_{str(e)}_\n\n"
                f"Please try again with /start or submit manually at:\n"
                f"https://eservices.ica.gov.sg/sgarrivalcard/"
            ),
            parse_mode='Markdown'
        )
    
    return ConversationHandler.END

# Enter command for returning users
async def enter_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_data = load_user_data()
    
    if user_id not in user_data:
        await update.message.reply_text(
            "❌ *No saved information found*\n\n"
            "You haven't registered yet!\n"
            "Please use /start to register first.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    saved_info = user_data[user_id]
    context.user_data['ic'] = saved_info['ic']
    context.user_data['dob'] = saved_info['dob']
    context.user_data['email'] = saved_info['email']
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, correct", callback_data="info_correct"),
            InlineKeyboardButton("❌ No, update", callback_data="info_incorrect")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👋 *Welcome back!*\n\n"
        f"*Your saved information:*\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"📋 *IC/FIN:* `{saved_info['ic']}`\n"
        f"🎂 *Date of Birth:* `{saved_info['dob']}`\n"
        f"📧 *Email:* `{saved_info['email']}`\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"Is this information still correct?",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return CONFIRM_INFO

# Handle info confirmation
async def confirm_info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "info_incorrect":
        await query.edit_message_text(
            "📝 *Update Required*\n\n"
            "Please provide your updated information:",
            parse_mode='Markdown'
        )
        # Send the welcome messages for re-registration
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=(
                "*🇸🇬 Let's update your information*\n\n"
                "━━━━━━━━━━━━━━━━━\n"
                "⚠️ *Disclaimer*\n"
                "• _This bot is NOT affiliated with ICA_\n"
                "• We comply with PDPA guidelines to protect your personal data\n"
                "• By proceeding, you consent to our data collection & usage\n"
                "• [Privacy Policy](https://docs.google.com/document/d/1gc5WjsPp8KS6Is4FWrfEiZcODx1_0po76Qsiq6fxyUM/edit?usp=sharing) | [Terms & Conditions](https://docs.google.com/document/d/12W7b2xAbcxVBbfdcpU1xvMPcv_2gsk1D0ar0had1LsI/edit?usp=sharing)\n"
                "━━━━━━━━━━━━━━━━━"
            ),
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="📋 Please enter your *NRIC/FIN* number:",
            parse_mode='Markdown'
        )
        return IC
    
    # Info is correct, proceed to date selection
    keyboard = generate_date_buttons()
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "✈️ *Quick Check-in*\n\n"
        "*When are you entering Singapore?*\n\n"
        "Please select your arrival date:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return ARRIVAL_DATE

# Cancel command
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚫 *Process cancelled*\n\n"
        "You can start again anytime:\n"
        "• /start - New registration\n"
        "• /enter - Quick check-in",
        parse_mode='Markdown'
    )
    return ConversationHandler.END

# Delete command - initial request
async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_data = load_user_data()
    
    if user_id not in user_data:
        await update.message.reply_text(
            "❌ *No Data Found*\n\n"
            "You don't have any stored information to delete.",
            parse_mode='Markdown'
        )
        return
    
    # Create confirmation buttons
    keyboard = [
        [
            InlineKeyboardButton("❌ Yes, delete my data", callback_data="delete_confirm"),
            InlineKeyboardButton("↩️ No, keep my data", callback_data="delete_cancel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    saved_info = user_data[user_id]
    await update.message.reply_text(
        "⚠️ *Delete Personal Data*\n"
        "━━━━━━━━━━━━━━━━━\n\n"
        "*The following data will be deleted:*\n"
        f"📋 *IC/FIN:* `{saved_info['ic']}`\n"
        f"🎂 *Date of Birth:* `{saved_info['dob']}`\n"
        f"📧 *Email:* `{saved_info['email']}`\n\n"
        "*Are you sure?*\n"
        "This action cannot be undone.\n"
        "You'll need to register again to use the service.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Handle delete confirmation
async def delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "delete_cancel":
        await query.edit_message_text(
            "✅ *Data Preserved*\n\n"
            "Your information has been kept safe.\n"
            "You can continue using the service as usual.",
            parse_mode='Markdown'
        )
        return
    
    # Handle confirmation
    user_id = str(update.effective_user.id)
    user_data = load_user_data()
    
    if user_id in user_data:
        del user_data[user_id]
        save_user_data(user_data)
        
        await query.edit_message_text(
            "🗑️ *Data Deleted Successfully*\n\n"
            "All your personal information has been removed from our system.\n\n"
            "If you wish to use this service again:\n"
            "• Use /start to register\n",
            parse_mode='Markdown'
        )
    else:
        await query.edit_message_text(
            "❌ *Error*\n\n"
            "No data found to delete.\n"
            "You may have already deleted your information.",
            parse_mode='Markdown'
        )

# Help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Singapore Arrival Card Bot*\n"
        "━━━━━━━━━━━━━━━━━\n\n"
        "*Available Commands:*\n\n"
        "🆕 /start - Register as a new user\n"
        "🔄 /enter - Quick check-in (returning users)\n"
        "❌ /cancel - Cancel current operation\n"
        "🗑️ /delete - Delete your stored data\n"
        "❓ /help - Show this help message\n\n"
        "*How it works:*\n"
        "1. First time? Use /start to register\n"
        "2. Registered? Use /enter for quick check-in\n"
        "3. Your data is saved for future use\n\n"
        "*Need help?* Just type any command above!",
        parse_mode='Markdown'
    )

def main():
    # Get bot token from environment variable or hardcode it
    BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add simple command handlers first (these have priority)
    application.add_handler(CommandHandler("delete", delete))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(delete_callback, pattern="^delete_"))
    
    # Create conversation handler for start/registration flow
    # Now handles both new users and returning users
    start_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            IC: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_ic)],
            DOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_dob)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            CONFIRM_INFO: [CallbackQueryHandler(confirm_info_callback, pattern="^info_")],
            ARRIVAL_DATE: [CallbackQueryHandler(arrival_date_callback, pattern="^date_")],
            SICK_QUESTION: [CallbackQueryHandler(sick_callback, pattern="^sick_")]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )
    
    # Create conversation handler for returning users
    returning_user_handler = ConversationHandler(
        entry_points=[CommandHandler("enter", enter_command)],
        states={
            CONFIRM_INFO: [CallbackQueryHandler(confirm_info_callback, pattern="^info_")],
            ARRIVAL_DATE: [CallbackQueryHandler(arrival_date_callback, pattern="^date_")],
            SICK_QUESTION: [CallbackQueryHandler(sick_callback, pattern="^sick_")]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )
    
    # Add conversation handlers after simple commands
    application.add_handler(start_handler)
    application.add_handler(returning_user_handler)
    
    # Start the bot
    print("🤖 Bot is starting...")
    application.run_polling()

if __name__ == "__main__":
    main()
