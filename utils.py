import time
import re
from functools import wraps
from typing import Dict, List, Optional

class RateLimiter:
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[int, List[float]] = {}

    def is_rate_limited(self, user_id: int) -> bool:
        """Check if a user has exceeded their rate limit."""
        current_time = time.time()
        
        if user_id not in self.requests:
            self.requests[user_id] = []
        
        # Remove old requests
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if current_time - req_time < self.time_window
        ]
        
        # Check if user has exceeded rate limit
        if len(self.requests[user_id]) >= self.max_requests:
            return True
        
        self.requests[user_id].append(current_time)
        return False

def split_message(message: str, max_length: int = 4096) -> List[str]:
    """Split a message into chunks that respect Telegram's message length limit."""
    if len(message) <= max_length:
        return [message]
    
    chunks = []
    while message:
        if len(message) <= max_length:
            chunks.append(message)
            break
        
        # Find the last space within the limit
        split_index = message.rfind(' ', 0, max_length)
        if split_index == -1:
            split_index = max_length
        
        chunks.append(message[:split_index])
        message = message[split_index:].lstrip()
    
    return chunks

def clean_markdown(text: str) -> str:
    """Clean text to prevent markdown parsing errors."""
    markdown_chars = ['_', '*', '`', '[']
    for char in markdown_chars:
        text = text.replace(char, '\\' + char)
    return text

def clean_ai_response(response: str) -> tuple[str, str]:
    """Extract AI's thought process and final answer."""
    # Паттерны для поиска "мыслей" ИИ
    thought_patterns = [
        r'Let me think about.*?\n',
        r'I think.*?\n',
        r'думаю.*?\n',
        r'Thinking:.*?\n',
        r'Here\'s what.*?\n',
        r'First,.*?\n',
        r'позвольте подумать.*?\n',
        r'давайте.*?\n',
        r'хорошо.*?\n',
        r'я постараюсь.*?\n',
        r'начнём с.*?\n',
        r'рассмотрим.*?\n',
        r'разберём.*?\n',
        r'проанализируем.*?\n',
        r'To answer.*?\n',
        r'Let\'s.*?\n',
        r'First of all.*?\n',
        r'То есть.*?\n',
        r'Итак.*?\n',
        r'Сначала.*?\n',
        r'Во-первых.*?\n',
        r'Давайте разберем.*?\n',
        r'Analyzing.*?\n',
        r'Looking at.*?\n'
    ]

    # Собираем все мысли
    thoughts = []
    cleaned = response

    for pattern in thought_patterns:
        matches = re.finditer(pattern, cleaned, flags=re.IGNORECASE | re.MULTILINE)
        for match in matches:
            thought = match.group(0)
            thoughts.append(thought)
            cleaned = cleaned.replace(thought, '')

    # Очищаем оставшийся текст
    cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
    cleaned = re.sub(r'^\s+', '', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'\s+$', '', cleaned, flags=re.MULTILINE)

    thoughts_text = ''.join(thoughts).strip()
    final_answer = cleaned.strip()

    return thoughts_text, final_answer

def format_ai_response(response: str) -> str:
    """Format AI response for Telegram message with thoughts as quotes."""
    thoughts, answer = clean_ai_response(response)

    formatted_response = "*Ответ от DeepSeek R1:* 🤖\n\n"

    if thoughts:
        # Форматируем мысли как цитату, добавляя '>' перед каждой строкой
        formatted_thoughts = '\n'.join(f">{line}" for line in thoughts.split('\n') if line.strip())
        formatted_response += f"*💭 Размышления:* 🤔\n{formatted_thoughts}\n\n"

    formatted_response += f"*📝 Ответ:* ✅\n{clean_markdown(answer)}"

    return formatted_response