import logging
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputFile,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
import os

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = '7256680549:AAG1PC03lmgHF2Sg0rG9zWpJu7cIXTAdCuQ'

CHOOSING_SECTION, CHOOSING_PATH, CHOOSING_SUBROUTE, COLLECTING_RATING, COLLECTING_FEEDBACK_TEXT = range(5)

VIDEO_FILES = {
    "path1": "videos/1.mp4",
    "path2": "videos/2.mp4",
    "path3": "videos/3.mp4",
    "path4a": "videos/4a.mp4",
    "path4b": "videos/4b.mp4",
    "path5a": "videos/5a.mp4",
    "path5b": "videos/5b.mp4",
    "path5c": "videos/5c.mp4",
    "path5d": "videos/5d.mp4",
    "path6a": "videos/6a.mp4",
    "path6b": "videos/6b.mp4",
    "path6c": "videos/6c.mp4",
    "path7a": "videos/7a.mp4",
    "path7b": "videos/7b.mp4",
    "path7c": "videos/7c.mp4",
    "path8a": "videos/8a.mp4",
    "path8b": "videos/8b.mp4",
}

INITIAL_PATHS = {
    "path1": {"text": "Из столовой до к.Т", "video": "path1", "has_subroutes": False},
    "path2": {"text": "Из к.Л в спортивный зал", "video": "path2", "has_subroutes": False},
    "path3": {"text": "Из к.Б в к.К.", "video": "path3", "has_subroutes": False},
    "path4": {
        "text": "Из к.А в к.Л",
        "has_subroutes": True,
        "subroutes": {
            "a": {"text": "по улице", "video": "path4a"},
            "b": {"text": "внутри здания", "video": "path4b"},
        },
    },
    "path5": {
        "text": "Из к.Б в к.Л.",
        "has_subroutes": True,
        "subroutes": {
            "a": {"text": "по улице", "video": "path5a"},
            "b": {"text": "внутри университета , музей открыт", "video": "path5b"},
            "c": {"text": "внутри университета , музей закрыт", "video": "path5с"},
            "d": {"text": "дополнительный проход через к.Т без очереди", "video": "path5d"},
        },
    },
    "path6": {
        "text": "Из к.Б в к.Г",
        "has_subroutes": True,
        "subroutes": {
            "a": {"text": "по улице", "video": "path6a"},
            "b": {"text": "внутри здания, если музей открыт", "video": "path6b"},
            "c": {"text": "внутри здания, если музей закрыт", "video": "path6c"},
        },
    },
    "path7": {
        "text": "Из к.А в к.Б.",
        "has_subroutes": True,
        "subroutes": {
            "a": {"text": "по улице мимо шоссе", "video": "path7a"},
            "b": {"text": "по улице между корпусов", "video": "path7b"},
            "c": {"text": "внутри университета", "video": "path7c"},
        },
    },
    "path8": {
        "text": "Из к.Л в к.Г.",
        "has_subroutes": True,
        "subroutes": {
            "a": {"text": "внутри университета", "video": "path8a"},
            "b": {"text": "по улице", "video": "path8b"},
        },
    },
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [
            InlineKeyboardButton("Навигатор", callback_data='navigator'),
            InlineKeyboardButton("Отзыв", callback_data='feedback')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Привет! Этот бот поможет выбрать маршрут или оставить отзыв. Выбери нужный раздел:",
        reply_markup=reply_markup
    )
    return CHOOSING_SECTION

async def main_menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'navigator':
        keyboard = [
            [InlineKeyboardButton(path["text"], callback_data=key)] for key, path in INITIAL_PATHS.items()
        ]
        keyboard.append([InlineKeyboardButton("Главное меню", callback_data='main_menu')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "Выберите маршрут:",
            reply_markup=reply_markup
        )
        return CHOOSING_PATH
    elif data == 'feedback':
        await query.edit_message_text("Пожалуйста, оцените наш бот по шкале от 1 до 5:")
        return COLLECTING_RATING

async def choose_path(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    selected_path = INITIAL_PATHS.get(query.data)

    if not selected_path:
        await query.edit_message_text("Выбранный маршрут не найден. Пожалуйста, выберите снова.")
        return CHOOSING_SECTION

    if not selected_path.get("has_subroutes"):
        video_key = selected_path.get("video")
        video_path = VIDEO_FILES.get(video_key)
        if video_path and os.path.exists(video_path):
            with open(video_path, 'rb') as video_file:
                await query.message.reply_video(InputFile(video_file))
            await query.message.reply_text(
                f"Вы выбрали маршрут: {selected_path['text']}.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Главное меню", callback_data="main_menu")]
                ])
            )
        else:
            await query.message.reply_text(
                "Видео для этого маршрута не найдено.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Главное меню", callback_data="main_menu")]
                ])
            )
        return CHOOSING_SECTION
    else:
        subroutes = selected_path.get("subroutes", {})
        keyboard = [
            [InlineKeyboardButton(sub["text"], callback_data=f"{query.data}:{key}")]
            for key, sub in subroutes.items()
        ]
        keyboard.append([InlineKeyboardButton("Назад", callback_data='back_to_paths')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"Вы выбрали: {selected_path['text']}. Теперь выберите способ передвижения:",
            reply_markup=reply_markup
        )
        return CHOOSING_SUBROUTE

async def choose_subroute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back_to_paths":
        keyboard = [
            [InlineKeyboardButton(path["text"], callback_data=key)] for key, path in INITIAL_PATHS.items()
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Выберите маршрут:", reply_markup=reply_markup)
        return CHOOSING_PATH

    path_key, sub_key = data.split(":")
    selected_path = INITIAL_PATHS.get(path_key)
    selected_subroute = selected_path["subroutes"].get(sub_key) if selected_path else None

    if not selected_subroute:
        await query.edit_message_text("Выбранный подмаршрут не найден. Пожалуйста, выберите снова.")
        return CHOOSING_SECTION

    video_key = selected_subroute.get("video")
    video_path = VIDEO_FILES.get(video_key)
    if video_path and os.path.exists(video_path):
        with open(video_path, 'rb') as video_file:
            await query.message.reply_video(InputFile(video_file))
        await query.message.reply_text(
            f"Вы выбрали маршрут: {selected_path['text']} → {selected_subroute['text']}.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Главное меню", callback_data="main_menu")]
            ])
        )
    else:
        await query.message.reply_text(
            "Видео для этого подмаршрута не найдено.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Главное меню", callback_data="main_menu")]
            ])
        )
    return CHOOSING_SECTION

async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    keyboard = [
        [
            InlineKeyboardButton("Навигатор", callback_data='navigator'),
            InlineKeyboardButton("Отзыв", callback_data='feedback')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Главное меню:", reply_markup=reply_markup)
    return CHOOSING_SECTION

async def collect_rating(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text.strip()
    user_id = update.message.from_user.id

    if user_input.isdigit() and 1 <= int(user_input) <= 5:
        context.user_data['rating'] = int(user_input)
        await update.message.reply_text("Спасибо! Напишите ваш отзыв:")
        return COLLECTING_FEEDBACK_TEXT
    else:
        await update.message.reply_text("Пожалуйста, введите оценку от 1 до 5:")
        return COLLECTING_RATING

async def collect_feedback_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text.strip()
    user_id = update.message.from_user.id
    rating = context.user_data.get('rating')

    with open("feedbacks.txt", "a", encoding='utf-8') as f:
        f.write(f"User {user_id}: Оценка {rating}, Отзыв: {user_input}\n")

    await update.message.reply_text("Спасибо за ваш отзыв!")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Действие отменено. Чтобы начать заново, отправьте /start.')
    return ConversationHandler.END

def main():
    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING_SECTION: [
                CallbackQueryHandler(main_menu_choice, pattern='^(navigator|feedback)$'),
                CallbackQueryHandler(back_to_main_menu, pattern='^main_menu$')
            ],
            CHOOSING_PATH: [
                CallbackQueryHandler(choose_path, pattern='^path\d+$'),
                CallbackQueryHandler(back_to_main_menu, pattern='^main_menu$')
            ],
            CHOOSING_SUBROUTE: [
                CallbackQueryHandler(choose_subroute, pattern='^path\d+:[a-z]$'),
                CallbackQueryHandler(back_to_main_menu, pattern='^main_menu$')
            ],
            COLLECTING_RATING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, collect_rating),
                CommandHandler('cancel', cancel)
            ],
            COLLECTING_FEEDBACK_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, collect_feedback_text),
                CommandHandler('cancel', cancel),
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()
