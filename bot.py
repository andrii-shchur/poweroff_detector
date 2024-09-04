import logging

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from const import GROUPS, TELEGRAM_BOT_TOKEN
from database import (
    create_subscriptions_table_if_not_exists,
    delete_group_subscription,
    get_groups_by_chat_id,
    set_group_subscription,
)

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

CHOOSING = 0
UNSUBSCRIBING = 1


def get_available_groups_for_user(chat_id: int) -> tuple[str, ...]:
    return tuple(sorted(GROUPS.difference(get_groups_by_chat_id(chat_id))))


def get_subscribed_groups_for_user(chat_id: int) -> tuple[str, ...]:
    return tuple(sorted(get_groups_by_chat_id(chat_id)))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [get_available_groups_for_user(update.message.chat_id)]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

    await update.message.reply_text('Вітаю, виберіть свою групу:', reply_markup=reply_markup)
    return CHOOSING


async def subscribe_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [get_available_groups_for_user(update.message.chat_id)]
    if not reply_keyboard[0]:
        await update.message.reply_text('Ви підписались на всі доступні групи.')
        return ConversationHandler.END
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

    await update.message.reply_text('Виберіть групу, на яку хочете підписатись:', reply_markup=reply_markup)
    return CHOOSING


async def unsubscribe_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [get_subscribed_groups_for_user(update.message.chat_id)]
    if not reply_keyboard[0]:
        await update.message.reply_text('Ви не підписані на жодну групу.')
        return ConversationHandler.END
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

    await update.message.reply_text('Виберіть групу, від якої хочете відписатись:', reply_markup=reply_markup)
    return UNSUBSCRIBING


async def handle_group_unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    group = update.message.text
    if group in get_subscribed_groups_for_user(update.message.chat_id):
        delete_group_subscription(group_name=group, chat_id=update.message.chat_id)
        await update.message.reply_text(
            f'Ви відписались від групи {group}. Тепер вам не будуть приходити сповіщення про зміни графіків у даній групі.\n\n'
            f'Щоб підписатись ще на одну групу, скористайтесь командою /subscribe_group\n'
            f'Щоб відписатись від групи, скористайтесь командою /unsubscribe_group\n'
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text('Введено некоректну групу. Скористайтесь кнопками нижче')
        return UNSUBSCRIBING


async def handle_group_choosing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    group = update.message.text
    if group in get_available_groups_for_user(update.message.chat_id):
        set_group_subscription(group_name=group, chat_id=update.message.chat_id)
        await update.message.reply_text(
            f'Ви обрали групу {group}. Тепер вам будуть приходити сповіщення про зміни графіків у даній групі.\n\n'
            f'Щоб підписатись ще на одну групу, скористайтесь командою /subscribe_group\n'
            f'Щоб відписатись від групи, скористайтесь командою /unsubscribe_group\n'
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text('Введено некоректну групу. Скористайтесь кнопками нижче')
        return CHOOSING


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('До зустрічі!')
    return ConversationHandler.END


def main():
    create_subscriptions_table_if_not_exists()
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler_states = {
        CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, callback=handle_group_choosing)],
        UNSUBSCRIBING: [MessageHandler(filters.TEXT & ~filters.COMMAND, callback=handle_group_unsubscribe)],
    }
    conv_handler_fallbacks = [CommandHandler("cancel", cancel)]
    groups_handler_initial = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states=conv_handler_states,
        fallbacks=conv_handler_fallbacks,
    )
    groups_handler = ConversationHandler(
        entry_points=[CommandHandler("subscribe_group", subscribe_group)],
        states=conv_handler_states,
        fallbacks=conv_handler_fallbacks,
    )
    unsubscribe_group_handler = ConversationHandler(
        entry_points=[CommandHandler("unsubscribe_group", unsubscribe_group)],
        states=conv_handler_states,
        fallbacks=conv_handler_fallbacks,
    )

    application.add_handler(groups_handler_initial)
    application.add_handler(groups_handler)
    application.add_handler(unsubscribe_group_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
