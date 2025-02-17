import time
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

def format_ai_response(response: str) -> str:
    """Format AI response for Telegram message."""
    response = clean_markdown(response)
    return f"*Ответ от нейросети:*\n\n{response}"
