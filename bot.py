import asyncio
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

from config import *
from logger import setup_logger
from utils import RateLimiter, split_message, format_ai_response

# Setup logger
logger = setup_logger()

# Initialize OpenAI client for OpenRouter
client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=OPENROUTER_API_KEY)

# Initialize rate limiter
rate_limiter = RateLimiter(MAX_REQUESTS_PER_MINUTE, REQUEST_WINDOW_SECONDS)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    user = update.effective_user
    welcome_message = (
        f"Привет, {user.first_name}! 👋\n\n"
        "Я бот с искусственным интеллектом, готовый помочь тебе.\n"
        "Просто напиши мне сообщение, и я постараюсь ответить.\n\n"
        "Используй /help для получения списка команд."
    )
    await update.message.reply_text(welcome_message, parse_mode=DEFAULT_PARSE_MODE)
    logger.info(f"New user started the bot: {user.id}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /help command."""
    await update.message.reply_text(HELP_MESSAGE, parse_mode=DEFAULT_PARSE_MODE)

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /about command."""
    await update.message.reply_text(ABOUT_MESSAGE, parse_mode=DEFAULT_PARSE_MODE)

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

    logger.info(f"Received message from user {user_id}: {message_text}")

    try:
        # Send typing action
        await update.message.chat.send_action("typing")

        # Get AI response
        completion = client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "user", "content": message_text}]
        )

        if not completion.choices:
            raise ValueError("Empty response from AI")

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

        logger.info(f"Successfully sent response to user {user_id}")

    except Exception as e:
        error_message = f"Error processing message: {str(e)}"
        logger.error(error_message)
        await update.message.reply_text(
            ERROR_MESSAGES['general_error'],
            parse_mode=DEFAULT_PARSE_MODE
        )

def main() -> None:
    """Initialize and run the bot."""
    try:
        # Initialize application
        application = Application.builder().token(TELEGRAM_TOKEN).build()

        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("about", about_command))
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        ))

        # Start the bot
        logger.info("Starting bot...")
        application.run_polling()

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise

if __name__ == '__main__':
    main()