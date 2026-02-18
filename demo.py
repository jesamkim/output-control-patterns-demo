#!/usr/bin/env python3
"""
LLM Output Control Design Patterns Demo

Patterns:
  1. Style Transfer       - Tone/style transformation
  2. Reverse Neutralization - Domain expert personas
  3. Content Optimization  - Self-Refine loop

Usage:
  python3 demo.py 1|2|3|all [--advanced] [--output json] [--save]
  python3 demo.py all --advanced --save
  python3 demo.py 1 --output json

Environment variables:
  BEDROCK_MODEL_ID  - Override model (default: global.anthropic.claude-sonnet-4-5-20250929-v1:0)
  BEDROCK_REGION    - Override region (default: us-west-2)
  COMPARE_MODELS    - Comma-separated model IDs for comparison mode

Bedrock Claude Sonnet 4.5 (Global Inference)
"""

import argparse
import json
import sys
import time

from patterns.bedrock import get_model_id, set_model_id
from patterns.display import collector
from patterns.style_transfer import demo_style_transfer
from patterns.reverse_neutralization import demo_reverse_neutralization
from patterns.content_optimization import demo_content_optimization


DEMOS = {
    "1": ("Style Transfer", demo_style_transfer),
    "2": ("Reverse Neutralization", demo_reverse_neutralization),
    "3": ("Content Optimization", demo_content_optimization),
}


def run_demo(choice: str, advanced: bool, json_mode: bool) -> dict:
    """Run selected demo(s) and return combined results."""
    results = {}

    if choice == "all":
        keys = ["1", "2", "3"]
    elif choice in DEMOS:
        keys = [choice]
    else:
        print("Select 1, 2, 3, or all.", file=sys.stderr)
        sys.exit(1)

    for key in keys:
        name, func = DEMOS[key]
        if not json_mode and key != keys[0]:
            print("\n")
        result = func(advanced=advanced, json_mode=json_mode)
        results[name] = result

    return results


def run_comparison(choice: str, advanced: bool, model_ids: list[str], json_mode: bool) -> dict:
    """Run the same demo across multiple models for comparison."""
    comparison = {"models": {}}

    for model_id in model_ids:
        set_model_id(model_id)
        if not json_mode:
            print(f"\n{'#' * 60}")
            print(f"  Model: {model_id}")
            print(f"{'#' * 60}\n")

        result = run_demo(choice, advanced, json_mode)
        comparison["models"][model_id] = result

    return comparison


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="LLM Output Control Design Patterns Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
examples:
  python3 demo.py 1                    # Style Transfer (basic)
  python3 demo.py all --advanced       # All patterns (advanced)
  python3 demo.py 2 --output json      # JSON output
  python3 demo.py 1 --save             # Save results to results/
  COMPARE_MODELS=model-a,model-b python3 demo.py 1 --advanced
""",
    )
    parser.add_argument(
        "pattern",
        nargs="?",
        choices=["1", "2", "3", "all"],
        help="Pattern to run: 1=Style Transfer, 2=Reverse Neutralization, 3=Content Optimization, all=Run all",
    )
    parser.add_argument(
        "--advanced",
        action="store_true",
        help="Enable advanced mode with more scenarios and metrics",
    )
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save results to results/ directory as timestamped JSON",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Override Bedrock model ID",
    )
    return parser


def interactive_menu(advanced: bool) -> str:
    """Show interactive menu and get user choice."""
    mode = "ADVANCED" if advanced else "BASIC"
    print(f"\n  LLM Output Control Design Patterns Demo [{mode}]")
    print(f"   Model: {get_model_id()}\n")
    for k, (name, _) in DEMOS.items():
        print(f"   [{k}] {name}")
    print("   [all] Run all patterns")
    print(f"\n   --advanced flag for advanced mode")
    print()
    return input("Select (1/2/3/all): ").strip()


def main():
    parser = build_parser()
    args = parser.parse_args()

    json_mode = args.output == "json"

    if args.model:
        set_model_id(args.model)

    # Interactive mode if no pattern specified
    choice = args.pattern
    if not choice:
        choice = interactive_menu(args.advanced)

    # Check for comparison mode
    import os
    compare_models = os.environ.get("COMPARE_MODELS", "")
    if compare_models:
        model_ids = [m.strip() for m in compare_models.split(",") if m.strip()]
        results = run_comparison(choice, args.advanced, model_ids, json_mode)
    else:
        total_start = time.time()
        results = run_demo(choice, args.advanced, json_mode)
        total_elapsed = time.time() - total_start

        if not json_mode:
            print(f"\n{'=' * 60}")
            print(f"  Total elapsed: {total_elapsed:.1f}s")
            print(f"  Model: {get_model_id()}")
            print(f"{'=' * 60}")

    # JSON output
    if json_mode:
        collector.print_json(get_model_id())

    # Save results
    if args.save:
        path = collector.save(get_model_id())
        if not json_mode:
            print(f"\n  Results saved: {path}")


if __name__ == "__main__":
    main()
