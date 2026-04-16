"""
Interactive CLI for testing the Poli-Tutor ask() pipeline.

Usage (from the rag/ folder):
    python src/chat.py --course ed
"""

import argparse
import logging

logging.disable(logging.CRITICAL)

from .retrieval import ask

def run_chat(course: str) -> None:
    print(f"\nPoli-Tutor — UC: {course.upper()}")
    print("Type your question, or 'exit' to quit.\n")

    while True:
        try:
            query = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSession ended.")
            break

        if not query:
            continue

        if query.lower() in {"exit", "quit", "sair"}:
            print("Session ended.")
            break

        response = ask(course=course, query=query)

        print(f"\nTutor: {response.answer}")

        if not response.is_fallback and response.sources:
            print("\nSources:")
            seen = set()
            for src in response.sources:
                key = (src.filename, tuple(src.pages))
                if key in seen:
                    continue
                seen.add(key)
                pages_str = ", ".join(str(p) for p in src.pages)
                print(f"  • {src.filename} — p.{pages_str}")

        print()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Poli-Tutor interactive chat")
    parser.add_argument(
        "--course",
        type=str,
        required=True,
        help="Course unit identifier (e.g. 'ed', 'pp')",
    )
    args = parser.parse_args()
    run_chat(args.course)
