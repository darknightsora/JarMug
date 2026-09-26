VALID_OUTPUT_TYPES = ("music", "instrument", "sfx")


def choose_model(output_type: str) -> str:
    """
    Choose the Stable Audio 3 model based on the requested output type.
    """

    output_type = output_type.strip().lower()

    if output_type in ("music", "instrument"):
        return "small-music"

    if output_type == "sfx":
        return "small-sfx"

    raise ValueError(
        f"Unknown output type: '{output_type}'. "
        f"Choose from: {', '.join(VALID_OUTPUT_TYPES)}"
    )