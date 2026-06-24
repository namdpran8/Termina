# cost_tracker.py
"""
Session-scoped token usage tracker with per-model pricing.
Pricing is approximate and updated periodically — for estimation only.
"""

# Pricing table: (input_per_1M, output_per_1M) in USD
# Add models here as needed. Falls back to DEFAULT_RATE if not found.
MODEL_PRICING: dict[str, tuple[float, float]] = {
    # NVIDIA NIM / Llama
    "meta/llama-3.1-70b-instruct":      (0.15,  0.15),
    "meta/llama-3.1-8b-instruct":       (0.05,  0.05),
    "nvidia/nemotron-3-nano-9b":         (0.10,  0.10),
    "nvidia/nemotron-3-super-120b-a12b": (0.40,  0.40),
    "nvidia/nemotron-ultra-253b-v1":     (0.80,  0.80),
    # OpenAI
    "gpt-4o":                            (5.00,  15.00),
    "gpt-4o-mini":                       (0.15,   0.60),
    # Anthropic
    "claude-sonnet-4-6":                 (3.00,  15.00),
    "claude-opus-4-6":                   (15.00, 75.00),
    "claude-haiku-4-5":                  (0.80,   4.00),
    # Gemini
    "gemini-2.0-flash":                  (0.10,   0.40),
    "gemini-2.5-pro":                    (1.25,   5.00),
}

DEFAULT_RATE = (0.20, 0.20)  # fallback for unknown models


class SessionTracker:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._reset()
        return cls._instance

    def _reset(self):
        self.prompt_tokens: int = 0
        self.completion_tokens: int = 0
        self._current_model: str = ""

    def set_model(self, model: str) -> None:
        self._current_model = model

    def add_usage(self, prompt_tokens: int, completion_tokens: int) -> None:
        self.prompt_tokens += (prompt_tokens or 0)
        self.completion_tokens += (completion_tokens or 0)

    def _get_rates(self) -> tuple[float, float]:
        model = self._current_model.lower()
        # Exact match first
        if model in MODEL_PRICING:
            return MODEL_PRICING[model]
        # Partial match (e.g. "gpt-4o" matches "gpt-4o-2024-05-13")
        for key, rates in MODEL_PRICING.items():
            if key in model or model in key:
                return rates
        return DEFAULT_RATE

    def get_summary(self) -> str:
        input_rate, output_rate = self._get_rates()
        input_cost  = (self.prompt_tokens     / 1_000_000) * input_rate
        output_cost = (self.completion_tokens / 1_000_000) * output_rate
        total_cost  = input_cost + output_cost
        total_tokens = self.prompt_tokens + self.completion_tokens

        model_note = f" ({self._current_model})" if self._current_model else ""
        return (
            f"Session Usage{model_note}: {total_tokens:,} tokens "
            f"(↑{self.prompt_tokens:,} input / ↓{self.completion_tokens:,} output) "
            f"— Est. cost: ${total_cost:.5f}"
        )


tracker = SessionTracker()
