"""Pattern 3: Content Optimization — Self-Refine Loop.

Generate -> Self-Critique -> Refine cycle to systematically improve output quality.
"""

import time

from patterns.bedrock import call_bedrock
from patterns.display import (
    collector,
    print_header,
    print_result,
    print_table,
)
from patterns.metrics import parse_critique_scores

# ---------------------------------------------------------------------------
# Task definitions
# ---------------------------------------------------------------------------
TASKS = {
    "basic": {
        "name": "Bedrock Overview for Executives",
        "task": (
            "Explain the key features of Amazon Bedrock in 3 sentences. "
            "Target audience: executives with no cloud experience."
        ),
        "task_ko": (
            "Amazon Bedrock의 주요 특징을 3문장으로 설명하세요. "
            "대상: 클라우드 경험이 없는 경영진."
        ),
        "role": "You are an AWS technical marketing specialist.",
        "role_ko": "당신은 AWS 기술 마케팅 전문가입니다.",
        "criteria": (
            "1. Clarity (1-5): Understandable by executives without jargon?\n"
            "2. Conciseness (1-5): Within 3 sentences, no filler?\n"
            "3. Persuasiveness (1-5): Clear business value?\n"
            "4. Accuracy (1-5): Technically accurate?"
        ),
        "criteria_ko": (
            "1. 명확성 (1-5): 전문 용어 없이 경영진이 바로 이해할 수 있는가?\n"
            "2. 간결성 (1-5): 3문장 이내, 군더더기 없는가?\n"
            "3. 설득력 (1-5): 비즈니스 가치가 명확한가?\n"
            "4. 정확성 (1-5): 기술적으로 정확한가?"
        ),
        "criteria_keys": ["명확성", "간결성", "설득력", "정확성"],
        "rounds": 1,
    },
    "advanced": {
        "name": "Financial CIO Proposal Summary",
        "task": (
            "Write a 5-sentence executive summary for a proposal to introduce "
            "customer service automation using Amazon Bedrock. "
            "Target: Financial sector CIO. Emphasize ROI and security."
        ),
        "task_ko": (
            "Amazon Bedrock을 활용한 고객 서비스 자동화 도입 제안서의 핵심 요약을 "
            "5문장으로 작성하세요. 대상: 금융권 CIO. ROI와 보안을 강조하세요."
        ),
        "role": "You are a financial-sector specialized AWS consultant.",
        "role_ko": "당신은 금융권 전문 AWS 컨설턴트입니다.",
        "criteria": (
            "1. 명확성 (1-5): CIO가 바로 의사결정할 수 있을 정도로 명확한가?\n"
            "2. 간결성 (1-5): 5문장 이내, 불필요한 수식어 없는가?\n"
            "3. 설득력 (1-5): ROI와 비즈니스 임팩트가 구체적인가?\n"
            "4. 정확성 (1-5): 기술적으로 정확하고 과장이 없는가?\n"
            "5. 보안/규제 (1-5): 금융권 규제(전자금융감독규정 등) 관점을 반영했는가?\n"
            "6. 실행가능성 (1-5): 구체적인 다음 단계(PoC 등)가 제시되었는가?"
        ),
        "criteria_keys": ["명확성", "간결성", "설득력", "정확성", "보안/규제", "실행가능성"],
        "rounds": 3,
    },
    "advanced-blog": {
        "name": "Tech Blog Introduction",
        "task_ko": (
            "Amazon Bedrock을 소개하는 기술 블로그의 도입부를 300자 이내로 작성하세요. "
            "대상: 백엔드 개발자. Hook + 핵심 가치 + 읽어야 할 이유를 포함하세요."
        ),
        "role_ko": "당신은 기술 블로그 전문 작가입니다. 개발자 커뮤니티에서 인기 있는 글을 쓰는 것이 특기입니다.",
        "criteria": (
            "1. 명확성 (1-5): 개발자가 바로 이해할 수 있는가?\n"
            "2. 간결성 (1-5): 300자 이내인가?\n"
            "3. 설득력 (1-5): 계속 읽고 싶어지는가?\n"
            "4. 정확성 (1-5): 기술적으로 정확한가?\n"
            "5. 톤 (1-5): 개발자 친화적이고 자연스러운가?"
        ),
        "criteria_keys": ["명확성", "간결성", "설득력", "정확성", "톤"],
        "rounds": 2,
    },
}


# ---------------------------------------------------------------------------
# Self-Refine engine
# ---------------------------------------------------------------------------
def run_self_refine(task_config: dict, verbose: bool = True) -> tuple[list, str]:
    """Run Self-Refine loop. Return (round_scores, final_draft)."""
    task = task_config.get("task_ko", task_config.get("task", ""))
    role = task_config.get("role_ko", task_config.get("role", ""))
    criteria = task_config.get("criteria_ko", task_config.get("criteria", ""))
    criteria_keys = task_config["criteria_keys"]
    rounds = task_config["rounds"]

    if verbose:
        print(f"\n  Task: {task}")
        print(f"   Rounds: {rounds}\n")

    # Initial generation
    start = time.time()
    draft = call_bedrock(role, task, temperature=0.8)
    gen_elapsed = time.time() - start

    if verbose:
        print(f"  [Initial Draft] ({gen_elapsed:.1f}s)")
        print(f"   {draft}\n")

    round_scores = []

    for r in range(rounds):
        # Critique
        critique_prompt = f"""Evaluate the following text against these criteria.

## Criteria
{criteria}

## Text
{draft}

## Output format
Output JSON with each criterion name as key and {{"score": N, "feedback": "..."}} as value."""

        start = time.time()
        critique = call_bedrock(
            "You are a technical document quality auditor. Be strict and specific.",
            critique_prompt,
            max_tokens=2048,
            temperature=0.3,
        )
        critique_elapsed = time.time() - start

        scores = parse_critique_scores(critique)
        avg = round(sum(scores.values()) / len(scores), 1) if scores else 0
        round_scores.append({
            "round": r + 1,
            "type": "critique",
            "scores": scores,
            "avg": avg,
            "elapsed_sec": round(critique_elapsed, 2),
        })

        if verbose:
            print(f"  [Round {r + 1} Critique] avg: {avg}/5  ({critique_elapsed:.1f}s)")
            for k, v in scores.items():
                print(f"   {k}: {v}/5")
            print()

        # Refine
        refine_prompt = f"""Improve the text based on the feedback.

## Original
{draft}

## Feedback
{critique}

## Original Task
{task}

Reflect ALL feedback and output only the improved final version."""

        start = time.time()
        draft = call_bedrock(
            role + " Carefully incorporate all feedback.",
            refine_prompt,
            temperature=0.5,
        )
        refine_elapsed = time.time() - start

        if verbose:
            print(f"  [Round {r + 1} Refined] ({refine_elapsed:.1f}s)")
            print(f"   {draft}\n")

    # Final evaluation
    final_prompt = f"""Evaluate the following text against these criteria.

## Criteria
{criteria}

## Text
{draft}

## Output format
Output JSON with scores and feedback."""

    start = time.time()
    final_critique = call_bedrock(
        "You are a technical document quality auditor.",
        final_prompt,
        max_tokens=2048,
        temperature=0.3,
    )
    final_elapsed = time.time() - start

    final_scores = parse_critique_scores(final_critique)
    final_avg = round(sum(final_scores.values()) / len(final_scores), 1) if final_scores else 0
    round_scores.append({
        "round": rounds + 1,
        "type": "final",
        "scores": final_scores,
        "avg": final_avg,
        "elapsed_sec": round(final_elapsed, 2),
    })

    if verbose and rounds > 1:
        print(f"  [Final Evaluation] avg: {final_avg}/5  ({final_elapsed:.1f}s)")
        for k, v in final_scores.items():
            print(f"   {k}: {v}/5")

    return round_scores, draft


# ---------------------------------------------------------------------------
# Main demo function
# ---------------------------------------------------------------------------
def demo_content_optimization(advanced: bool = False, json_mode: bool = False) -> dict:
    """Run Content Optimization demo and return results dict."""
    if not json_mode:
        print_header("Pattern 3: Content Optimization (Self-Refine Loop)", advanced)

    collector.start_pattern("content_optimization", advanced)
    pattern_results = {"pattern": "content_optimization", "tasks": []}

    task_keys = ["basic"]
    if advanced:
        task_keys = ["advanced", "advanced-blog"]

    for tkey in task_keys:
        config = TASKS[tkey]

        if not json_mode:
            print(f"\n{'~' * 40}")
            print(f"  Scenario: {config['name']}")

        round_scores, final_draft = run_self_refine(config, verbose=not json_mode)

        task_result = {
            "task": config["name"],
            "rounds": config["rounds"],
            "round_scores": round_scores,
            "final_draft": final_draft,
        }

        # Collect for output
        task_ko = config.get("task_ko", config.get("task", ""))
        total_elapsed = sum(rs.get("elapsed_sec", 0) for rs in round_scores)
        collector.add_result(
            config["name"], "self-refine", task_ko, final_draft,
            total_elapsed, {"round_scores": round_scores},
        )

        if not json_mode and len(round_scores) > 1:
            print(f"\n  Score Progression ({config['name']})")
            headers = ["Round"] + config["criteria_keys"] + ["AVG"]
            rows = []
            for rs in round_scores:
                row = [f"R{rs['round']}" if rs["type"] == "critique" else "Final"]
                for k in config["criteria_keys"]:
                    row.append(rs["scores"].get(k, "-"))
                row.append(rs["avg"])
                rows.append(row)
            print_table(headers, rows)

            if len(round_scores) >= 2:
                first_avg = round_scores[0]["avg"]
                last_avg = round_scores[-1]["avg"]
                delta = round(last_avg - first_avg, 1)
                sign = "+" if delta >= 0 else ""
                print(f"\n  Improvement: {first_avg} -> {last_avg} ({sign}{delta})")

        pattern_results["tasks"].append(task_result)

    return pattern_results
