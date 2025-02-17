import os
from aiogram.enums import ParseMode

# Bot Configuration
TELEGRAM_TOKEN = '7935071641:AAE5zL3OwVzS-u0HSqx7w9WoSp9ZN-BZlrY'
OPENROUTER_API_KEY = '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'

# API Configuration
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
AI_MODEL = "deepseek/deepseek-r1:free"

# Rate Limiting
MAX_REQUESTS_PER_MINUTE = 60
REQUEST_WINDOW_SECONDS = 60

# Message Configuration
MAX_MESSAGE_LENGTH = 4096  # Telegram's limit

# Error Messages
ERROR_MESSAGES = {
    'rate_limit': "*Превышен лимит запросов. Пожалуйста, подождите немного.*",
    'api_error': "*Ошибка API. Пожалуйста, попробуйте позже.*",
    'general_error': "*Произошла ошибка. Пожалуйста, попробуйте еще раз.*",
    'empty_response': "*Извините, я не получил ответ от нейросети. Пожалуйста, попробуйте позже.*"
}

WELCOME_MESSAGE = """
Привет, {}! 👋

Я бот с искусственным интеллектом DeepSeek R1, готовый помочь тебе.
Просто напиши мне сообщение, и я постараюсь ответить.
"""