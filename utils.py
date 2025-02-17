import time
import re
from functools import wraps
from typing import Dict, List, Optional, Tuple

class RateLimiter:
    def __init__(self, max_requests: int, time_window: int, max_daily_requests: int = 200):
        self.max_requests = max_requests
        self.time_window = time_window
        self.max_daily_requests = max_daily_requests
        self.requests: Dict[int, List[float]] = {}
        self.daily_requests: Dict[int, List[float]] = {}

    def is_rate_limited(self, user_id: int) -> Tuple[bool, str]:
        """Check if a user has exceeded their rate limit."""
        current_time = time.time()
        day_start = current_time - (current_time % 86400)  # Start of current day

        # Initialize user records if not exist
        if user_id not in self.requests:
            self.requests[user_id] = []
        if user_id not in self.daily_requests:
            self.daily_requests[user_id] = []

        # Clean up old requests
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if current_time - req_time < self.time_window
        ]
        self.daily_requests[user_id] = [
            req_time for req_time in self.daily_requests[user_id]
            if req_time >= day_start
        ]

        # Check minute limit
        if len(self.requests[user_id]) >= self.max_requests:
            return True, "minute"

        # Check daily limit
        if len(self.daily_requests[user_id]) >= self.max_daily_requests:
            return True, "day"

        # Add new request
        self.requests[user_id].append(current_time)
        self.daily_requests[user_id].append(current_time)
        return False, ""

    def get_remaining_quota(self, user_id: int) -> Dict[str, int]:
        """Get remaining quota for both minute and daily limits."""
        if user_id not in self.requests:
            return {
                "minute": self.max_requests,
                "day": self.max_daily_requests
            }

        current_time = time.time()
        day_start = current_time - (current_time % 86400)

        minute_requests = len([
            req_time for req_time in self.requests[user_id]
            if current_time - req_time < self.time_window
        ])
        daily_requests = len([
            req_time for req_time in self.daily_requests.get(user_id, [])
            if req_time >= day_start
        ])

        return {
            "minute": max(0, self.max_requests - minute_requests),
            "day": max(0, self.max_daily_requests - daily_requests)
        }

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
    markdown_chars = ['_', '*', '`', '[', ']', '(', ')', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in markdown_chars:
        text = text.replace(char, '\\' + char)
    return text

def clean_ai_response(response: str) -> tuple[str, str]:
    """Extract AI's thought process and final answer."""
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

    # Collect all thoughts
    thoughts = []
    cleaned = response

    for pattern in thought_patterns:
        matches = re.finditer(pattern, cleaned, flags=re.IGNORECASE | re.MULTILINE)
        for match in matches:
            thought = match.group(0)
            thoughts.append(thought)
            cleaned = cleaned.replace(thought, '')

    # Clean remaining text
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
        thoughts_lines = [line for line in thoughts.split('\n') if line.strip()]
        formatted_thoughts = '\n'.join(f">{clean_markdown(line)}" for line in thoughts_lines)
        formatted_response += f"*💭 Размышления:* 🤔\n{formatted_thoughts}\n\n"

    formatted_response += f"*📝 Ответ:* ✅\n{clean_markdown(answer)}"

    return formatted_response