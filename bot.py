import logging
import os

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from const import GROUPS

if not os.environ.get('PRODUCTION'):
    from dotenv import load_dotenv

    load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

CHOOSING = 0


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [GROUPS]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

    await update.message.reply_text('Вітаю, виберіть свою групу:', reply_markup=reply_markup)
    return CHOOSING


async def choose_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [GROUPS]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

    await update.message.reply_text('Виберіть свою групу:', reply_markup=reply_markup)
    return CHOOSING


async def handle_group_choosing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    group = update.message.text
    if group in GROUPS:
        await update.message.reply_text(
            f'Ви обрали групу {group}. Тепер вам будуть приходити сповіщення про зміни графіків в даній групі.\n\n'
            f'Щоб змінити вибір, скористайтесь командою /choose_group'
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text('Введено некоректну групу. Скористайтесь кнопками нижче')
        return CHOOSING


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('До зустрічі!')
    return ConversationHandler.END


def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler_states = {CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, callback=handle_group_choosing)]}
    conv_handler_fallbacks = [CommandHandler("cancel", cancel)]
    groups_handler_initial = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states=conv_handler_states,
        fallbacks=conv_handler_fallbacks,
    )
    groups_handler = ConversationHandler(
        entry_points=[CommandHandler("choose_group", choose_group)],
        states=conv_handler_states,
        fallbacks=conv_handler_fallbacks,
    )

    application.add_handler(groups_handler_initial)
    application.add_handler(groups_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
