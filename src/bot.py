import datetime
import logging

from telegram import Bot, ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from const import GROUPS, TELEGRAM_BOT_TOKEN, DayName
from database import (
    create_subscriptions_table_if_not_exists,
    delete_group_subscription,
    get_chat_ids_for_group,
    get_groups_by_chat_id,
    set_group_subscription,
)
from detection import OnOffInterval

logging.basicConfig(
    filename='app.log', filemode='a+', format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

log = logging.getLogger(__name__)

CHOOSING = 0
UNSUBSCRIBING = 1


def get_available_groups_for_user(chat_id: int) -> tuple[str, ...]:
    available_groups_set = set(GROUPS).difference(get_groups_by_chat_id(chat_id))
    return tuple(sorted(available_groups_set))


def get_subscribed_groups_for_user(chat_id: int) -> tuple[str, ...]:
    return tuple(sorted(get_groups_by_chat_id(chat_id)))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.message.chat_id
    reply_keyboard = [get_available_groups_for_user(chat_id)]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

    await update.message.reply_text('Вітаю, виберіть свою групу:', reply_markup=reply_markup)
    log.info(f'User {chat_id=} started a bot')
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


async def handle_group_choosing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    group = update.message.text
    chat_id = update.message.chat_id
    if group in get_available_groups_for_user(chat_id):
        set_group_subscription(group_name=group, chat_id=chat_id)
        await update.message.reply_text(
            f'Ви додали групу {group}. Тепер вам будуть приходити сповіщення про зміни графіків у даній групі.\n\n'
            f'Щоб підписатись ще на одну групу, скористайтесь командою /subscribe_group\n'
            f'Щоб відписатись від групи, скористайтесь командою /unsubscribe_group\n'
        )
        log.info(f'User {chat_id=} subscribed to group {group}')
        return ConversationHandler.END
    else:
        await update.message.reply_text('Введено некоректну групу. Скористайтесь кнопками нижче')
        return CHOOSING


async def handle_group_unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    group = update.message.text
    chat_id = update.message.chat_id
    if group in get_subscribed_groups_for_user(chat_id):
        delete_group_subscription(group_name=group, chat_id=chat_id)
        await update.message.reply_text(
            f'Ви відписались від групи {group}. Тепер вам не будуть приходити сповіщення про зміни графіків у даній групі.\n\n'
            f'Щоб підписатись ще на одну групу, скористайтесь командою /subscribe_group\n'
            f'Щоб відписатись від групи, скористайтесь командою /unsubscribe_group\n'
        )
        log.info(f'User {chat_id=} unsubscribed from group {group}')
        return ConversationHandler.END
    else:
        await update.message.reply_text('Введено некоректну групу. Скористайтесь кнопками нижче')
        return UNSUBSCRIBING


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('До зустрічі!')
    return ConversationHandler.END


async def send_updates(schedule: dict[str, list[OnOffInterval]], schedule_date: datetime.date) -> None:
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    if schedule_date == datetime.date.today():
        day_name = DayName.TODAY
    elif schedule_date == datetime.date.today() + datetime.timedelta(days=1):
        day_name = DayName.TOMORROW
    else:
        day_name = schedule_date.strftime('%d.%m.%Y')

    group_to_chat_id = get_chat_ids_for_group()
    now_hour = datetime.datetime.now().hour
    for group_name, chat_ids in group_to_chat_id.items():
        filtered_schedule = filter(
            lambda x: (
                (x.start_hour >= now_hour or x.end_hour > now_hour >= x.start_hour)
                if day_name == DayName.TODAY
                else True
            ),
            filter(
                lambda x: x.state == 'off',
                schedule[group_name],
            ),
        )
        next_outages = list(map(str, filtered_schedule))
        message_text = f'❗️В групі {group_name} змінився графік відключень на {day_name}.\n'
        if next_outages:
            message_text += f'🔴Наступні відключення: {", ".join(next_outages)}\n'
        else:
            message_text += '🟢Відключень немає'
        for chat_id in chat_ids:
            await bot.send_message(
                chat_id=chat_id,
                text=message_text,
            )


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
