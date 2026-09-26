"""JarMug command-line entry point. The shared engine lives in core.generation."""

# Re-export the existing public helpers for callers of the original CLI module.
from core.generation import (
    JARMUG_ROOT, OUTPUT_DIR, STABLE_AUDIO_CLI, MODEL_CACHE,
    MIN_DURATION, MAX_DURATION, create_output_path, validate_duration,
    generate_audio, describe_error,
)


def main():
    print("\n================================")
    print("           JarMug ☕")
    print("  Just a Rather Music Generator")
    print("================================\n")
    print("Available modes:\n  music\n  instrument\n  sfx\n")
    try:
        output_type = input("Type: ").strip().lower()
        prompt = input("Prompt: ").strip()
        duration_text = input("Duration in seconds [10]: ").strip()
        duration = int(duration_text) if duration_text else 10
        path = generate_audio(output_type, prompt, duration, on_status=print)
        print(f"\n☕ Generation complete!\nSaved to: {path}")
    except (KeyboardInterrupt, EOFError):
        print("\n\nGeneration cancelled.")
    except Exception as error:
        print(f"\nGeneration failed: {describe_error(error)}")


if __name__ == "__main__":
    main()
