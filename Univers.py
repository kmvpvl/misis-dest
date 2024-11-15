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

# Настройка логирования для отслеживания работы бота и отладки
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен вашего бота
TOKEN = '7256680549:AAG1PC03lmgHF2Sg0rG9zWpJu7cIXTAdCuQ'  #

# Определение состояний для ConversationHandler
CHOOSING_SECTION, CHOOSING_PATH, CHOOSING_SUBROUTE, COLLECTING_RATING, COLLECTING_FEEDBACK_TEXT = range(5)

# Словарь с путями и соответствующими видеофайлами
VIDEO_FILES = {
    "path1": "videos/1.mp4",  # Из столовой до корпуса Т
    "path2": "videos/2.mp4",  # Из корпуса Л в спортивный зал
    "path3": "videos/3.mp4",      # Из корпуса Б в корпус К
    "path4a": "videos/4a.mp4",  # Из корпуса А в корпус Л по улице
    "path4b": "videos/4b.mp4",  # Из корпуса А в корпус Л внутри здания
    "path5a": "videos/5a.mp4",  # Из корпуса Б в корпус Л по улице
    "path5b": "videos/5b.mp4",  # Внутри здания, если музей открыт
    "path5c": "videos/5c.mp4",  # Внутри здания, если музей закрыт
    "path5d": "videos/5d.mp4",  # Дополнительный проход через к.Т без очереди
    "path6a": "videos/6a.mp4",  # Из корпуса Б в корпус Г по улице
    "path6b": "videos/6b.mp4",  # Из корпуса Б в корпус Г внутри здания, если музей открыт
    "path6c": "videos/6c.mp4",  # Из корпуса Б в корпус Г внутри здания, если музей закрыт
    "path7a": "videos/7a.mp4",  # Из корпуса А в корпус Б по улице мимо шоссе
    "path7b": "videos/7b.mp4",  # Из корпуса А в корпус Б по улице между корпусов
    "path7c": "videos/7c.mp4",  # Из корпуса А в корпус Б внутри университета
    "path8a": "videos/8a.mp4",  # Из корпуса Л в корпус Г внутри университета
    "path8b": "videos/8b.mp4",  # Из корпуса Л в корпус Г по улице
}

# Инициализация путей и подмаршрутов
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
            "b": {"text": "внутри здания, если музей открыт", "video": "path5b"},
            "c": {"text": "внутри здания, если музей закрыт", "video": "path5c"},
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

# Функция старта бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Отправляет приветственное сообщение с двумя основными кнопками:
    - Навигатор
    - Отзыв
    """
    logger.info("Бот запущен, отправляем приветственное сообщение.")

    # Создание инлайн кнопок для главного меню
    keyboard = [
        [
            InlineKeyboardButton("Навигатор", callback_data='navigator'),
            InlineKeyboardButton("Отзыв", callback_data='feedback')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Привет, студент! Этот бот поможет тебе выбрать маршрут между корпусами или оставить отзыв. Не беспокойся, если бот какое-то время не отвечает, он думает, какой путь оптимальнее :)) Выбери нужный раздел ниже:",
        reply_markup=reply_markup
    )

    return CHOOSING_SECTION


# Функция обработки выбора основного раздела (Навигатор или Отзыв)
async def main_menu_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает выбор между Навигатором и Отзывом.
    """
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'navigator':
        # Пользователь выбрал Навигатор, показываем маршруты
        logger.info("Пользователь выбрал Навигатор.")
        keyboard = [
            [InlineKeyboardButton(path["text"], callback_data=key)] for key, path in INITIAL_PATHS.items()
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "Выберите маршрут:",
            reply_markup=reply_markup
        )
        return CHOOSING_PATH

    elif data == 'feedback':
        # Пользователь выбрал Отзыв, начинаем сбор обратной связи
        logger.info("Пользователь выбрал Отзыв.")
        await query.edit_message_text(
            "Пожалуйста, оцените наш бот по шкале от 1 до 5:",
        )
        return COLLECTING_RATING

    else:
        # Неизвестный выбор, возвращаемся в главное меню
        logger.warning(f"Неизвестный выбор в главном меню: {data}")
        keyboard = [
            [
                InlineKeyboardButton("Навигатор", callback_data='navigator'),
                InlineKeyboardButton("Отзыв", callback_data='feedback')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "Неизвестный выбор. Пожалуйста, выберите раздел:",
            reply_markup=reply_markup
        )
        return CHOOSING_SECTION


# Функция обработки выбора маршрута
async def choose_path(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает выбор маршрута из списка.
    Если маршрут имеет подмаршруты, показывает их.
    Если нет, отправляет соответствующее видео.
    """
    query = update.callback_query
    await query.answer()
    selected_path = INITIAL_PATHS.get(query.data)

    if not selected_path:
        # Если выбранный маршрут не найден, информируем пользователя и возвращаемся в главное меню
        logger.error(f"Выбранный маршрут не найден: {query.data}")
        keyboard = [
            [
                InlineKeyboardButton("Главное меню", callback_data='main_menu')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "Выбранный маршрут не найден. Пожалуйста, выберите снова или вернитесь в главное меню.",
            reply_markup=reply_markup
        )
        return CHOOSING_SECTION

    logger.info(f"Пользователь выбрал маршрут: {selected_path['text']}")

    if not selected_path.get("has_subroutes"):
        # Если маршрут не имеет подмаршрутов, отправляем видео
        video_key = selected_path.get("video")
        video_path = VIDEO_FILES.get(video_key)
        if video_path and os.path.exists(video_path):
            # Отправляем видеофайл
            with open(video_path, 'rb') as video_file:
                await query.message.reply_video(InputFile(video_file))
            await query.message.reply_text(f"Вы выбрали маршрут: {selected_path['text']}.")
        else:
            # Видео не найдено, информируем пользователя и предоставляем кнопку для возврата в главное меню
            logger.warning(f"Видео не найдено для маршрута: {selected_path['text']}")
            keyboard = [
                [
                    InlineKeyboardButton("Главное меню", callback_data='main_menu')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(
                "Видео для этого маршрута не найдено.",
                reply_markup=reply_markup
            )
        return CHOOSING_SECTION

    else:
        # Если маршрут имеет подмаршруты, показываем их пользователю
        subroutes = selected_path.get("subroutes", {})
        keyboard = [
            [
                InlineKeyboardButton(sub["text"], callback_data=f"{query.data}:{key}")
            ]
            for key, sub in subroutes.items()
        ]
        # Добавляем кнопку "Назад" для возврата к выбору маршрутов
        keyboard.append([InlineKeyboardButton("Назад", callback_data='back_to_paths')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"Вы выбрали: {selected_path['text']}. Теперь выберите способ передвижения:",
            reply_markup=reply_markup
        )
        return CHOOSING_SUBROUTE


# Функция обработки выбора подмаршрута
async def choose_subroute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает выбор подмаршрута.
    Отправляет соответствующее видео или предоставляет возможность вернуться в главное меню.
    """
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back_to_paths":
        # Пользователь нажал "Назад", возвращаемся к выбору маршрутов
        logger.info("Пользователь вернулся к выбору маршрутов.")
        keyboard = [
            [InlineKeyboardButton(path["text"], callback_data=key)] for key, path in INITIAL_PATHS.items()
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "Выберите маршрут:",
            reply_markup=reply_markup
        )
        return CHOOSING_PATH

    # Ожидаем формат "path_key:sub_key"
    try:
        path_key, sub_key = data.split(":")
    except ValueError:
        # Некорректные данные, информируем пользователя и возвращаемся к выбору подмаршрутов
        logger.error(f"Некорректные данные для подмаршрута: {data}")
        keyboard = [
            [
                InlineKeyboardButton("Главное меню", callback_data='main_menu')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "Некорректный выбор. Пожалуйста, выберите способ передвижения снова или вернитесь в главное меню.",
            reply_markup=reply_markup
        )
        return CHOOSING_SECTION

    selected_path = INITIAL_PATHS.get(path_key)
    if not selected_path or not selected_path.get("has_subroutes"):
        # Маршрут не найден или не имеет подмаршрутов
        logger.error(f"Маршрут с ключом {path_key} не найден или не имеет подмаршрутов.")
        keyboard = [
            [
                InlineKeyboardButton("Главное меню", callback_data='main_menu')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "Выбранный маршрут не найден. Пожалуйста, выберите снова или вернитесь в главное меню.",
            reply_markup=reply_markup
        )
        return CHOOSING_SECTION

    selected_subroute = selected_path["subroutes"].get(sub_key)
    if not selected_subroute:
        # Подмаршрут не найден
        logger.error(f"Подмаршрут с ключом {sub_key} не найден.")
        keyboard = [
            [
                InlineKeyboardButton("Главное меню", callback_data='main_menu')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "Выбранный подмаршрут не найден. Пожалуйста, выберите способ передвижения снова или вернитесь в главное меню.",
            reply_markup=reply_markup
        )
        return CHOOSING_SECTION

    logger.info(f"Пользователь выбрал подмаршрут: {selected_subroute['text']}")

    video_key = selected_subroute.get("video")
    video_path = VIDEO_FILES.get(video_key)
    if video_path and os.path.exists(video_path):
        # Отправляем видеофайл
        with open(video_path, 'rb') as video_file:
            await query.message.reply_video(InputFile(video_file))
        await query.message.reply_text(
            f"Вы выбрали маршрут: {selected_path['text']} → {selected_subroute['text']}."
        )
    else:
        # Видео не найдено, информируем пользователя и предоставляем кнопку для возврата в главное меню
        logger.warning(f"Видео не найдено для подмаршрута: {selected_subroute['text']}")
        keyboard = [
            [
                InlineKeyboardButton("Главное меню", callback_data='main_menu')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            "Видео для этого маршрута не найдено.",
            reply_markup=reply_markup
        )

    return CHOOSING_SECTION


# Функция для возврата в главное меню
async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Возвращает пользователя в главное меню.
    """
    query = update.callback_query
    await query.answer()
    logger.info("Пользователь вернулся в главное меню.")
    keyboard = [
        [
            InlineKeyboardButton("Навигатор", callback_data='navigator'),
            InlineKeyboardButton("Отзыв", callback_data='feedback')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "Главное меню:",
        reply_markup=reply_markup
    )
    return CHOOSING_SECTION


# Функция обработки оценки от 1 до 5
async def collect_rating(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает оценку от 1 до 5 и переходит к сбору текстового отзыва.
    """
    user_input = update.message.text.strip()
    user_id = update.message.from_user.id

    # Проверка, что введено число от 1 до 5
    if user_input.isdigit() and 1 <= int(user_input) <= 5:
        context.user_data['rating'] = int(user_input)
        logger.info(f"Пользователь {user_id} поставил оценку: {user_input}")
        await update.message.reply_text(
            "Спасибо! Теперь, пожалуйста, напишите ваш отзыв, рекомендацию, похвалу или критику:"
        )
        return COLLECTING_FEEDBACK_TEXT
    else:
        # Некорректная оценка, просим ввести снова
        await update.message.reply_text(
            "Пожалуйста, введите корректную оценку от 1 до 5:"
        )
        return COLLECTING_RATING


# Функция обработки текстового отзыва
async def collect_feedback_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает текстовый отзыв и завершает сбор обратной связи.
    """
    user_input = update.message.text.strip()
    user_id = update.message.from_user.id
    rating = context.user_data.get('rating')

    if not rating:
        # Если по какой-то причине оценка отсутствует, просим начать заново
        await update.message.reply_text(
            "Произошла ошибка при сборе вашей оценки. Пожалуйста, отправьте /start для начала."
        )
        return ConversationHandler.END

    logger.info(f"Получен отзыв от пользователя {user_id}: Оценка {rating}, Текст: {user_input}")

    # Здесь вы можете сохранить отзыв в базу данных или файл
    # Например, сохраняем в файл feedbacks.txt
    with open("feedbacks.txt", "a", encoding='utf-8') as f:
        f.write(f"User {user_id}: Оценка {rating}, Отзыв: {user_input}\n")

    await update.message.reply_text(
        "Спасибо за ваш отзыв! Если хотите оставить еще один отзыв, отправьте /start и выберите 'Отзыв'. Для выхода, отправьте /cancel."
    )

    return ConversationHandler.END


# Функция отмены текущей операции
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Позволяет пользователю отменить текущий процесс и вернуться в главное меню.
    """
    await update.message.reply_text(
        'Действие отменено. Чтобы начать заново, отправьте /start.'
    )
    return ConversationHandler.END


# Функция обработки некорректных сообщений во время сбора отзывов
async def feedback_invalid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает некорректные сообщения во время сбора отзыва.
    """
    await update.message.reply_text(
        "Пожалуйста, отправьте текст отзыва или отправьте /cancel для отмены."
    )
    return COLLECTING_FEEDBACK_TEXT


# Основная функция, запускающая бота
def main():
    """
    Основная функция для инициализации и запуска бота.
    """
    logger.info("Запускаем бота.")

    # Создание приложения
    application = ApplicationBuilder().token(TOKEN).build()

    # Создание ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING_SECTION: [
                CallbackQueryHandler(main_menu_choice, pattern='^(navigator|feedback)$')
            ],
            CHOOSING_PATH: [
                CallbackQueryHandler(choose_path, pattern='^path\d+$'),
                CallbackQueryHandler(back_to_main_menu, pattern='^main_menu$')
            ],
            CHOOSING_SUBROUTE: [
                CallbackQueryHandler(choose_subroute, pattern='^path\d+:[a-z]$'),
                CallbackQueryHandler(back_to_main_menu, pattern='^back_to_paths$')
            ],
            COLLECTING_RATING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, collect_rating),
                CommandHandler('cancel', cancel)
            ],
            COLLECTING_FEEDBACK_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, collect_feedback_text),
                CommandHandler('cancel', cancel),
                MessageHandler(filters.TEXT & ~filters.COMMAND, feedback_invalid),
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    # Добавление обработчика в приложение
    application.add_handler(conv_handler)

    # Запуск бота
    logger.info("Бот запущен и готов к работе.")
    application.run_polling()


if __name__ == '__main__':
    main()
