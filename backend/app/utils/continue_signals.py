CONTINUE_SIGNALS = [
    "okay thanks",
    "ok thanks",
    "got it",
    "continue",
    "let's keep going",
    "lets keep going",
    "thanks",
    "alright",
    "i'm good",
    "im good",
    "next",
    "move on",
    "keep going",
    "go ahead",
    "okay",
    "ok",
    "sure",
    "yes",
    "yep",
    "yeah",
]


def is_continue_signal(text: str) -> bool:
    """Check if the transcribed text is a continue signal."""
    normalized = text.lower().strip()

    # Direct match
    if normalized in CONTINUE_SIGNALS:
        return True

    # Partial match (in case of extra words)
    for signal in CONTINUE_SIGNALS:
        if signal in normalized and len(normalized) < 30:
            return True

    return False


def is_question(text: str) -> bool:
    """Check if the transcribed text appears to be a question."""
    normalized = text.lower().strip()

    # Check for question markers
    if normalized.endswith("?"):
        return True

    question_starters = [
        "what", "why", "how", "when", "where", "who", "which",
        "can you", "could you", "would you", "do you", "does",
        "is there", "are there", "was", "were", "will",
        "explain", "tell me", "clarify"
    ]

    for starter in question_starters:
        if normalized.startswith(starter):
            return True

    return False
