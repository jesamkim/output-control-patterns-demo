"""Pattern 2: Reverse Neutralization — Domain Expert Personas.

Override RLHF-induced neutrality by assigning domain-expert personas
that provide opinionated, experience-backed answers.
"""

import time

from patterns.bedrock import call_bedrock
from patterns.display import (
    collector,
    print_header,
    print_result,
    print_scenario,
    print_table,
)
from patterns.metrics import avg_sentence_len, count_chars

# ---------------------------------------------------------------------------
# Persona definitions
# ---------------------------------------------------------------------------
BASIC_PERSONAS = {
    "aws-sa": {
        "name": "AWS Solutions Architect",
        "system": (
            "You are an AWS Solutions Architect with 10 years of experience. "
            "You have completed 50+ migration projects. "
            "Provide answers based on real-world experience, not theory. "
            "Include specific AWS service names and architecture patterns. "
            "Instead of hedging with 'it depends' or 'generally speaking', "
            "give clear opinions with supporting evidence. "
            "Include lessons learned from failure cases."
        ),
    },
    "startup-cto": {
        "name": "Startup CTO",
        "system": (
            "You are a Series B startup CTO leading 15 engineers. "
            "You work in an environment with limited budget and headcount. "
            "Prioritize 'what's possible right now' over 'perfect solutions'. "
            "Evaluate decisions through cost efficiency, operational complexity, "
            "and team capability. Bold opinions are welcome."
        ),
    },
}

ADVANCED_PERSONAS = {
    "ciso": {
        "name": "Security Expert (CISO)",
        "system": (
            "You are a CISO (Chief Information Security Officer) at a large enterprise. "
            "15 years of security experience. "
            "Evaluate every technical decision from a security perspective. "
            "Use threat modeling, compliance (ISMS, SOC2, GDPR), and zero-trust as key frameworks. "
            "Strongly oppose 'security can wait' attitudes. "
            "Cite real breach cases. Quantify security risks with probability and impact figures."
        ),
    },
    "data-scientist": {
        "name": "Data Scientist",
        "system": (
            "You are a senior data scientist from FAANG (8 years experience). "
            "Approach every problem through data. Use numbers, not feelings. "
            "Always require A/B tests, statistical significance, and ROI calculations. "
            "Demand 'evidence' instead of 'best practice'. "
            "Evaluate migrations from data pipeline, model serving, and MLOps perspectives."
        ),
    },
    "regulatory-consultant": {
        "name": "Regulatory Consultant",
        "system": (
            "You are a financial/public sector regulatory consultant (12 years experience). "
            "Experience with financial regulators, data protection authorities, and cloud security certification (CSAP) audits. "
            "Evaluate every technical decision from a compliance perspective. "
            "Mention specific penalties (fines, business suspension) for violations. "
            "Clearly identify 'technically possible but regulatory prohibited' cases."
        ),
    },
    "devops-lead": {
        "name": "DevOps Lead",
        "system": (
            "You are a platform engineering lead at a company running 500+ microservices. "
            "You think in terms of CI/CD pipelines, observability, IaC, and developer experience. "
            "Evaluate migrations by operational burden, MTTR, deployment frequency, and change failure rate. "
            "Recommend specific tools (Terraform, ArgoCD, Datadog, etc.) with trade-offs."
        ),
    },
}

# ---------------------------------------------------------------------------
# Questions
# ---------------------------------------------------------------------------
QUESTIONS = {
    "basic": {
        "text": "We're considering cloud migration. What strategy would you recommend?",
        "text_ko": "클라우드 마이그레이션을 고려하고 있는데, 어떤 전략이 좋을까요?",
    },
    "advanced": {
        "text": (
            "Our company (financial sector, 3000 employees) wants to migrate "
            "our on-premise core banking system to the cloud. How should we approach this?"
        ),
        "text_ko": (
            "우리 회사(금융권, 직원 3000명)가 온프레미스 코어 뱅킹 시스템을 "
            "클라우드로 이전하려 합니다. 어떻게 접근해야 할까요?"
        ),
    },
    "microservices": {
        "text": (
            "We're splitting our monolith into microservices. "
            "What should we be careful about?"
        ),
        "text_ko": (
            "모놀리스를 마이크로서비스로 분리하려고 합니다. "
            "무엇을 조심해야 할까요?"
        ),
    },
}


def _get_personas(advanced: bool) -> dict:
    if advanced:
        return {**BASIC_PERSONAS, **ADVANCED_PERSONAS}
    return dict(BASIC_PERSONAS)


# ---------------------------------------------------------------------------
# Main demo function
# ---------------------------------------------------------------------------
def demo_reverse_neutralization(advanced: bool = False, json_mode: bool = False) -> dict:
    """Run Reverse Neutralization demo and return results dict."""
    if not json_mode:
        print_header("Pattern 2: Reverse Neutralization (Domain Expert Personas)", advanced)

    personas = _get_personas(advanced)
    pattern_results = {"pattern": "reverse_neutralization", "scenarios": []}

    collector.start_pattern("reverse_neutralization", advanced)

    question_keys = ["basic"]
    if advanced:
        question_keys = ["advanced", "microservices"]

    for qkey in question_keys:
        q = QUESTIONS[qkey]
        question_ko = q["text_ko"]

        if not json_mode:
            print_scenario(qkey.title(), question_ko)

        scenario_result = {"scenario": qkey, "question": question_ko, "outputs": []}

        # Neutral response first
        start = time.time()
        neutral = call_bedrock(
            "You are an AI assistant. Answer objectively.",
            question_ko,
        )
        neutral_elapsed = time.time() - start

        if not json_mode:
            print_result("Neutral Response (General AI)", neutral, truncate=300)

        scenario_result["outputs"].append({
            "persona": "Neutral AI",
            "output": neutral,
            "elapsed_sec": round(neutral_elapsed, 2),
            "chars": count_chars(neutral),
            "avg_sentence_len": avg_sentence_len(neutral),
        })

        collector.add_result(qkey, "Neutral AI", question_ko, neutral, neutral_elapsed)

        metrics_rows = [("Neutral AI", count_chars(neutral), avg_sentence_len(neutral), f"{neutral_elapsed:.1f}s")]

        for persona_key, persona in personas.items():
            start = time.time()
            result = call_bedrock(persona["system"], question_ko)
            elapsed = time.time() - start

            if not json_mode:
                print_result(f"{persona['name']} Persona", result, truncate=500)

            entry = {
                "persona": persona["name"],
                "output": result,
                "elapsed_sec": round(elapsed, 2),
                "chars": count_chars(result),
                "avg_sentence_len": avg_sentence_len(result),
            }
            scenario_result["outputs"].append(entry)
            collector.add_result(qkey, persona["name"], question_ko, result, elapsed)
            metrics_rows.append((persona["name"][:20], count_chars(result), avg_sentence_len(result), f"{elapsed:.1f}s"))

        if advanced and not json_mode:
            print(f"\n  Reverse Neutralization Metrics ({qkey})")
            print_table(
                ["Persona", "Length(chars)", "AvgSentLen", "Time"],
                metrics_rows,
            )

        pattern_results["scenarios"].append(scenario_result)

    return pattern_results
