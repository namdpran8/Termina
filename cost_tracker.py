class SessionTracker:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SessionTracker, cls).__new__(cls)
            cls._instance.prompt_tokens = 0
            cls._instance.completion_tokens = 0
        return cls._instance
        
    def add_usage(self, prompt_tokens: int, completion_tokens: int):
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        
    def get_summary(self) -> str:
        total = self.prompt_tokens + self.completion_tokens
        # Rough estimation: $0.15 per 1M tokens (Llama 3.1 70B pricing roughly)
        # We can make this dynamic later based on the actual model.
        cost = (total / 1_000_000) * 0.15
        return f"Session Usage: {total:,} tokens (Prompt: {self.prompt_tokens:,} | Completion: {self.completion_tokens:,}) - Estimated Cost: ${cost:.5f}"

tracker = SessionTracker()
