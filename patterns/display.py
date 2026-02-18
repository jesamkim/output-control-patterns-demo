"""Display and formatting utilities."""

import json
import os
import sys
from datetime import datetime


def print_table(headers: list, rows: list) -> list[str]:
    """Print a formatted table and return lines."""
    widths = [
        max(len(str(h)), max((len(str(r[i])) for r in rows), default=0))
        for i, h in enumerate(headers)
    ]
    sep = "+-" + "-+-".join("-" * w for w in widths) + "-+"
    fmt = "| " + " | ".join(f"{{:<{w}}}" for w in widths) + " |"

    lines = []
    lines.append(sep)
    lines.append(fmt.format(*headers))
    lines.append(sep)
    for row in rows:
        lines.append(fmt.format(*[str(c) for c in row]))
    lines.append(sep)

    for line in lines:
        print(line)
    return lines


def print_header(title: str, advanced: bool = False) -> None:
    """Print a section header."""
    if advanced:
        title += " [ADVANCED]"
    print("=" * 60)
    print(title)
    print("=" * 60)


def print_scenario(name: str, text: str) -> None:
    """Print scenario info."""
    print(f"\n{'~' * 40}")
    print(f"  Scenario: {name}")
    print(f"  Input: {text}\n")


def print_result(label: str, text: str, truncate: int = 0) -> None:
    """Print a result block."""
    display = text[:truncate] + "..." if truncate and len(text) > truncate else text
    print(f"  [{label}]")
    print(f"   {display}\n")


class OutputCollector:
    """Collect results for JSON output and file saving."""

    def __init__(self):
        self.results = []
        self._current_pattern = None

    def start_pattern(self, name: str, advanced: bool = False) -> None:
        self._current_pattern = {
            "pattern": name,
            "advanced": advanced,
            "scenarios": [],
        }
        self.results.append(self._current_pattern)

    def add_result(self, scenario: str, label: str, input_text: str,
                   output_text: str, elapsed: float = 0, metrics: dict = None) -> None:
        if self._current_pattern is None:
            return
        entry = {
            "scenario": scenario,
            "label": label,
            "input": input_text,
            "output": output_text,
            "elapsed_sec": round(elapsed, 2),
        }
        if metrics:
            entry["metrics"] = metrics
        self._current_pattern["scenarios"].append(entry)

    def to_dict(self, model_id: str) -> dict:
        return {
            "model_id": model_id,
            "timestamp": datetime.now().isoformat(),
            "patterns": self.results,
        }

    def save(self, model_id: str, output_dir: str = "results") -> str:
        """Save results to a timestamped JSON file."""
        os.makedirs(output_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(output_dir, f"run_{ts}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(model_id), f, ensure_ascii=False, indent=2)
        return path

    def print_json(self, model_id: str) -> None:
        """Print results as JSON to stdout."""
        print(json.dumps(self.to_dict(model_id), ensure_ascii=False, indent=2))


# Global collector instance
collector = OutputCollector()
