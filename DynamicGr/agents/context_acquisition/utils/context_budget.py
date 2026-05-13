from typing import Any


TOKEN_TO_CHAR_RATIO = 4


def resolve_max_chars_from_model_profile(
    model: Any,
    default_max_chars: int,
) -> int:
    """Resolve char budget from model profile max_input_tokens when available."""
    if model is None:
        return default_max_chars

    profile = getattr(model, "profile", None)
    if not isinstance(profile, dict):
        return default_max_chars

    model_max_input_tokens = profile.get("max_input_tokens")
    if isinstance(model_max_input_tokens, int) and model_max_input_tokens > 0:
        return model_max_input_tokens * TOKEN_TO_CHAR_RATIO

    return default_max_chars
