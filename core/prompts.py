def enhance_prompt(output_type: str, prompt: str) -> str:
    """
    Add lightweight mode-specific instructions to the user's prompt.
    """

    output_type = output_type.strip().lower()
    prompt = prompt.strip()

    if not prompt:
        raise ValueError("Prompt cannot be empty.")

    if output_type == "music":
        return prompt

    if output_type == "instrument":
        return (
            f"{prompt}. "
            "Solo instrument only. No drums, no percussion, no bass, "
            "no vocals, and no additional instruments."
        )

    if output_type == "sfx":
        return (
            f"{prompt}. "
            "Sound effect only. No music, no melody, and no vocals."
        )

    raise ValueError(f"Unknown output type: '{output_type}'")