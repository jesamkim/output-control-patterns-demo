"""Pattern 1: Style Transfer — Tone/Style Transformation.

Same input, different system prompts to transform tone while preserving content (meaning).
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
from patterns.metrics import count_chars, evaluate_preservation

# ---------------------------------------------------------------------------
# Style definitions
# ---------------------------------------------------------------------------
BASIC_STYLES = {
    "business-formal": {
        "name": "Business Formal",
        "system": (
            "You are a corporate communications specialist. "
            "Transform the text into formal business style (honorifics, official document tone) "
            "while preserving 100% of the original meaning. Do not add or remove information."
        ),
    },
    "tech-report": {
        "name": "Technical Incident Report",
        "system": (
            "You are a senior SRE engineer. "
            "Transform the text into a technical incident report style. "
            "Be objective and fact-based, remove all emotional expressions."
        ),
    },
    "customer-service": {
        "name": "Friendly Customer Service",
        "system": (
            "You are a customer service manager. "
            "Transform the text to empathize with and reassure the customer. "
            "Be warm and professional."
        ),
    },
}

ADVANCED_STYLES = {
    "medical-opinion": {
        "name": "Medical Opinion",
        "system": (
            "You are a university hospital specialist. "
            "Transform the situation into a medical opinion/clinical record style. "
            "Use symptom, findings, and action plan structure with appropriate medical terminology. "
            "Do not add information not present in the original."
        ),
    },
    "legal-opinion": {
        "name": "Legal Opinion",
        "system": (
            "You are an IT-specialized attorney. "
            "Transform the text into a legal opinion/formal notice style. "
            "Use legal phrasing such as 'whereas', 'hereby', 'is obligated to'. "
            "Preserve the original meaning."
        ),
    },
    "emotion-max": {
        "name": "Emotion Intensity MAX",
        "system": (
            "You are an emotion expression specialist. "
            "Amplify the emotional intensity to the maximum. "
            "Express anger, urgency, and frustration dramatically, "
            "but keep all core information from the original."
        ),
    },
    "emotion-min": {
        "name": "Emotion Intensity MIN",
        "system": (
            "You are a robot assistant. "
            "Remove all emotion and describe only facts. "
            "Report as if a machine is giving a status update. "
            "Remove all adjectives and emotional expressions."
        ),
    },
    "executive-summary": {
        "name": "Executive Summary",
        "system": (
            "You are a management consulting partner. "
            "Transform the text into a C-level executive briefing: "
            "lead with impact/risk, quantify where possible, "
            "end with a clear recommended action. Max 3 bullet points."
        ),
    },
}

# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------
SCENARIOS = {
    "it-incident": {
        "name": "IT Incident Report",
        "input": (
            "The server crashed again. Please check it immediately. "
            "It was the same issue yesterday and it's still not fixed."
        ),
        "input_ko": "Server ga tto teojyeosseoyo. Ppalli hwaginhae juseyo. Eojedo gateun munjeeyeonnneunde ajikdo an gochyeojin geoyeyo?",
        "styles_basic": list(BASIC_STYLES.keys()),
        "styles_advanced": list(BASIC_STYLES.keys()) + list(ADVANCED_STYLES.keys()),
    },
    "medical-consult": {
        "name": "Medical Consultation",
        "input": (
            "The patient has been complaining of headaches for 3 days. "
            "Pain medication isn't helping and they also have dizziness. "
            "There's family history of stroke, which is concerning."
        ),
        "styles_basic": [],
        "styles_advanced": ["medical-opinion", "customer-service", "executive-summary"],
    },
    "security-breach": {
        "name": "Security Incident",
        "input": (
            "Unauthorized access was detected on the internal admin panel last night. "
            "About 200 user records may have been exposed. "
            "We've shut down the affected server but haven't identified the attack vector yet."
        ),
        "styles_basic": [],
        "styles_advanced": ["tech-report", "legal-opinion", "executive-summary", "emotion-max"],
    },
}

# Korean scenario inputs for actual demo runs
SCENARIOS_KO = {
    "it-incident": "서버가 또 터졌어요. 빨리 확인해주세요. 어제도 같은 문제였는데 아직도 안 고쳐진 거예요?",
    "medical-consult": (
        "환자가 3일째 두통을 호소하고 있습니다. 진통제를 먹어도 낫지 않고, "
        "어지러움도 동반됩니다. 가족력으로 뇌졸중 이력이 있어 걱정됩니다."
    ),
    "security-breach": (
        "어젯밤 내부 관리자 페이지에 비인가 접근이 감지되었습니다. "
        "약 200건의 사용자 레코드가 노출되었을 가능성이 있습니다. "
        "해당 서버는 차단했지만 공격 경로는 아직 파악되지 않았습니다."
    ),
}


def _all_styles() -> dict:
    return {**BASIC_STYLES, **ADVANCED_STYLES}


# ---------------------------------------------------------------------------
# Main demo function
# ---------------------------------------------------------------------------
def demo_style_transfer(advanced: bool = False, json_mode: bool = False) -> dict:
    """Run Style Transfer demo and return results dict."""
    if not json_mode:
        print_header("Pattern 1: Style Transfer (Tone/Style Transformation)", advanced)

    all_styles = _all_styles()
    all_metrics = []
    pattern_results = {"pattern": "style_transfer", "scenarios": []}

    collector.start_pattern("style_transfer", advanced)

    active_scenarios = ["it-incident"]
    if advanced:
        active_scenarios += ["medical-consult", "security-breach"]

    for scenario_key in active_scenarios:
        scenario = SCENARIOS[scenario_key]
        original = SCENARIOS_KO.get(scenario_key, scenario["input"])
        style_keys = scenario["styles_advanced" if advanced else "styles_basic"]

        if not style_keys:
            continue

        if not json_mode:
            print_scenario(scenario["name"], original)

        scenario_result = {"scenario": scenario["name"], "input": original, "outputs": []}

        for style_key in style_keys:
            style = all_styles[style_key]
            start = time.time()
            result = call_bedrock(
                style["system"],
                f"Transform the following text:\n\n{original}",
            )
            elapsed = time.time() - start

            if not json_mode:
                print_result(style["name"], result)

            entry = {
                "style": style["name"],
                "output": result,
                "elapsed_sec": round(elapsed, 2),
                "chars_original": count_chars(original),
                "chars_transformed": count_chars(result),
            }

            if advanced:
                scores = evaluate_preservation(original, result)
                entry["preservation_scores"] = scores
                all_metrics.append((
                    scenario["name"][:12],
                    style["name"][:16],
                    count_chars(original),
                    count_chars(result),
                    scores.get("preservation", "-"),
                    scores.get("no_distortion", "-"),
                    scores.get("tone_shift", "-"),
                    f"{elapsed:.1f}s",
                ))

            collector.add_result(
                scenario["name"], style["name"], original, result,
                elapsed, entry.get("preservation_scores"),
            )
            scenario_result["outputs"].append(entry)

        pattern_results["scenarios"].append(scenario_result)

    if advanced and all_metrics and not json_mode:
        print("\n  Style Transfer Metrics")
        print_table(
            ["Scenario", "Style", "Orig", "Trans", "Preserv", "NoDist", "ToneShift", "Time"],
            all_metrics,
        )

    return pattern_results
