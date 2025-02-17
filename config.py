import os

# Bot Configuration
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '7935071641:AAE5zL3OwVzS-u0HSqx7w9WoSp9ZN-BZlrY')
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')

# API Configuration
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
AI_MODEL = "deepseek/deepseek-r1:free"

# Rate Limiting
MAX_REQUESTS_PER_MINUTE = 60
REQUEST_WINDOW_SECONDS = 60
MAX_REQUESTS_PER_DAY = 200  # OpenRouter free tier limit

# Message Configuration
MAX_MESSAGE_LENGTH = 4096  # Telegram's limit

# Error Messages
ERROR_MESSAGES = {
    'rate_limit_minute': "*Превышен лимит запросов в минуту. Пожалуйста, подождите немного.*",
    'rate_limit_day': "*Достигнут дневной лимит запросов. Пожалуйста, попробуйте завтра.*",
    'api_error': "*Ошибка API. Пожалуйста, попробуйте позже.*",
    'general_error': "*Произошла ошибка. Пожалуйста, попробуйте еще раз.*",
    'empty_response': "*Извините, я не получил ответ от нейросети. Пожалуйста, попробуйте позже.*"
}

WELCOME_MESSAGE = """
Привет, {}! 👋

Я бот с искусственным интеллектом DeepSeek R1, готовый помочь тебе.
Просто напиши мне сообщение, и я постараюсь ответить.
"""