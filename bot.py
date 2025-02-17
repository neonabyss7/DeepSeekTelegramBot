import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from openai import OpenAI
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

# Initialize bot and dispatcher
dp = Dispatcher()

# Initialize bot with markdown parsing
bot = Bot(token=TELEGRAM_TOKEN)
bot._parse_mode = "markdown"

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Handle the /start command."""
    user = message.from_user
    await message.answer(
        WELCOME_MESSAGE.format(user.first_name)
    )
    logger.info(f"Новый пользователь запустил бота: {user.id}")

@dp.message()
async def handle_message(message: Message):
    """Handle user messages and interact with the AI."""
    user_id = message.from_user.id
    message_text = message.text

    # Check rate limit
    if rate_limiter.is_rate_limited(user_id):
        await message.answer(
            ERROR_MESSAGES['rate_limit']
        )
        return

    logger.info(f"Получено сообщение от пользователя {user_id}: {message_text}")

    try:
        # Send typing action
        await bot.send_chat_action(chat_id=message.chat.id, action="typing")

        # Get AI response
        completion = await asyncio.to_thread(
            client.chat.completions.create,
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": "Ты - полезный ассистент. Отвечай четко и по делу."},
                {"role": "user", "content": message_text}
            ],
            temperature=0.7
        )

        # Check response
        if not completion or not completion.choices or not completion.choices[0].message:
            logger.error("Получен некорректный ответ от API")
            await message.answer(ERROR_MESSAGES['empty_response'])
            return

        # Process AI response
        ai_response = completion.choices[0].message.content
        if not ai_response or not isinstance(ai_response, str):
            logger.error(f"Некорректный формат ответа: {ai_response}")
            await message.answer(ERROR_MESSAGES['empty_response'])
            return

        # Format response
        formatted_response = format_ai_response(ai_response)
        response_chunks = split_message(formatted_response)

        # Send response chunks
        for chunk in response_chunks:
            await message.answer(chunk)

        logger.info(f"Успешно отправлен ответ пользователю {user_id}")

    except Exception as e:
        error_message = f"Ошибка обработки сообщения: {str(e)}"
        logger.error(error_message)
        await message.answer(
            ERROR_MESSAGES['general_error']
        )

async def main():
    """Initialize and run the bot."""
    try:
        # Check for other instances
        check_single_instance()

        # Set up signal handlers for cleanup
        def signal_handler(signum, frame):
            cleanup()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Start polling
        logger.info("Запуск бота...")
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"Фатальная ошибка: {str(e)}")
        cleanup()
        raise
    finally:
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())