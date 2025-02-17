import asyncio
import sys
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from openai import OpenAI
import re
import os
import signal

from config import *
from logger import setup_logger
from utils import RateLimiter, split_message, format_ai_response

# Setup logger
logger = setup_logger()

# Initialize OpenAI client for OpenRouter
client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=OPENROUTER_API_KEY)

# Initialize rate limiter
rate_limiter = RateLimiter(MAX_REQUESTS_PER_MINUTE, REQUEST_WINDOW_SECONDS)

# Create PID file path
PID_FILE = "bot.pid"

def check_single_instance():
    """Ensure only one instance of the bot is running."""
    logger.info("Проверка запущенных экземпляров бота...")
    if os.path.exists(PID_FILE):
        with open(PID_FILE, 'r') as f:
            old_pid = int(f.read().strip())
            try:
                os.kill(old_pid, 0)
                logger.error(f"Бот уже запущен с PID {old_pid}")
                sys.exit(1)
            except OSError:
                logger.info(f"Найден устаревший PID файл (PID: {old_pid}), можно продолжать")
                pass

    current_pid = os.getpid()
    logger.info(f"Записываем текущий PID: {current_pid}")
    with open(PID_FILE, 'w') as f:
        f.write(str(current_pid))

def cleanup():
    """Clean up resources when bot shuts down."""
    logger.info("Выполняется очистка ресурсов...")
    try:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
            logger.info("PID файл успешно удален")
    except OSError as e:
        logger.error(f"Ошибка при удалении PID файла: {e}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors in the telegram-python-bot library."""
    logger.error(f"Произошла ошибка при обработке обновления: {context.error}")
    if update and hasattr(update, 'effective_message'):
        await update.effective_message.reply_text(
            ERROR_MESSAGES['general_error'],
            parse_mode=DEFAULT_PARSE_MODE
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    user = update.effective_user
    await update.message.reply_text(
        WELCOME_MESSAGE.format(user.first_name),
        parse_mode=DEFAULT_PARSE_MODE
    )
    logger.info(f"Новый пользователь запустил бота: {user.id}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user messages and interact with the AI."""
    user_id = update.effective_user.id
    message_text = update.message.text

    # Check rate limit
    if rate_limiter.is_rate_limited(user_id):
        await update.message.reply_text(
            ERROR_MESSAGES['rate_limit'],
            parse_mode=DEFAULT_PARSE_MODE
        )
        return

    logger.info(f"Получено сообщение от пользователя {user_id}: {message_text}")

    try:
        # Send typing action
        await update.message.chat.send_action("typing")

        # Get AI response
        completion = client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "user", "content": message_text}]
        )

        if not completion.choices:
            raise ValueError("Пустой ответ от ИИ")

        # Process AI response
        ai_response = completion.choices[0].message.content
        cleaned_response = re.sub(r'<.*?>', '', ai_response).strip()

        if not cleaned_response:
            await update.message.reply_text(
                ERROR_MESSAGES['empty_response'],
                parse_mode=DEFAULT_PARSE_MODE
            )
            return

        # Format and split response if necessary
        formatted_response = format_ai_response(cleaned_response)
        response_chunks = split_message(formatted_response)

        # Send response chunks
        for chunk in response_chunks:
            await update.message.reply_text(
                chunk,
                parse_mode=DEFAULT_PARSE_MODE
            )

        logger.info(f"Успешно отправлен ответ пользователю {user_id}")

    except Exception as e:
        error_message = f"Ошибка обработки сообщения: {str(e)}"
        logger.error(error_message)
        await update.message.reply_text(
            ERROR_MESSAGES['general_error'],
            parse_mode=DEFAULT_PARSE_MODE
        )

def signal_handler(signum, frame):
    """Handle termination signals."""
    logger.info("Получен сигнал завершения, выключаю бота...")
    cleanup()
    sys.exit(0)

def main() -> None:
    """Initialize and run the bot."""
    try:
        # Check for other instances
        check_single_instance()

        # Set up signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Initialize application
        application = Application.builder().token(TELEGRAM_TOKEN).build()

        # Add error handler
        application.add_error_handler(error_handler)

        # Add command handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        ))

        # Start the bot
        logger.info("Запуск бота...")
        application.run_polling()

    except Exception as e:
        logger.error(f"Фатальная ошибка: {str(e)}")
        cleanup()
        raise

if __name__ == '__main__':
    main()