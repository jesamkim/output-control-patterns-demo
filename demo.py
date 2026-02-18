#!/usr/bin/env python3
"""
LLM 출력 제어 디자인 패턴 데모
- Pattern 1: Style Transfer (톤/문체 변환)
- Pattern 2: Reverse Neutralization (도메인 전문가 페르소나)
- Pattern 3: Content Optimization (Self-Refine 루프)

Basic mode: python3 demo.py 1|2|3|all
Advanced mode: python3 demo.py 1|2|3|all --advanced

Bedrock Claude Sonnet 4.5 (Global Inference) 사용
"""

import json
import re
import sys
import time
import boto3
from botocore.config import Config as BotoConfig

MODEL_ID = "global.anthropic.claude-sonnet-4-5-20250929-v1:0"
REGION = "us-west-2"

client = boto3.client(
    "bedrock-runtime",
    region_name=REGION,
    config=BotoConfig(read_timeout=120, retries={"max_attempts": 3}),
)


def call_bedrock(system: str, user: str, max_tokens: int = 1024, temperature: float = 0.7) -> str:
    """Bedrock Converse API 호출"""
    response = client.converse(
        modelId=MODEL_ID,
        system=[{"text": system}],
        messages=[{"role": "user", "content": [{"text": user}]}],
        inferenceConfig={"maxTokens": max_tokens, "temperature": temperature},
    )
    return response["output"]["message"]["content"][0]["text"]


# ============================================================
# Metrics Utilities
# ============================================================
def count_chars(text: str) -> int:
    """공백 제외 글자 수"""
    return len(text.replace(" ", "").replace("\n", ""))


def avg_sentence_len(text: str) -> float:
    """평균 문장 길이 (어절 수)"""
    sentences = [s.strip() for s in re.split(r'[.!?。]\s*', text) if s.strip()]
    if not sentences:
        return 0
    return round(sum(len(s.split()) for s in sentences) / len(sentences), 1)


def evaluate_preservation(original: str, transformed: str) -> dict:
    """LLM으로 의미 보존도 자동 평가"""
    prompt = f"""원문과 변환문의 의미 보존도를 평가하세요.

## 원문
{original}

## 변환문
{transformed}

## 평가 기준
- 정보 보존 (1-5): 원문의 핵심 정보가 모두 포함되어 있는가?
- 의미 왜곡 (1-5): 원래 의미가 왜곡되지 않았는가? (5=왜곡 없음)
- 톤 전환 (1-5): 톤/스타일이 명확하게 변환되었는가?

JSON만 출력: {{"preservation": N, "no_distortion": N, "tone_shift": N}}"""

    result = call_bedrock(
        "당신은 텍스트 품질 평가 전문가입니다. JSON만 출력하세요.",
        prompt, max_tokens=200, temperature=0.2,
    )
    try:
        match = re.search(r'\{[^}]+\}', result)
        return json.loads(match.group()) if match else {}
    except:
        return {}


def parse_critique_scores(critique_text: str) -> dict:
    """Self-Critique JSON에서 점수 추출"""
    try:
        match = re.search(r'\{[\s\S]*\}', critique_text)
        if match:
            data = json.loads(match.group())
            return {k: v.get("score", 0) for k, v in data.items() if isinstance(v, dict)}
    except:
        pass
    return {}


def print_table(headers: list, rows: list):
    """간단한 테이블 출력"""
    widths = [max(len(str(h)), max((len(str(r[i])) for r in rows), default=0)) for i, h in enumerate(headers)]
    sep = "+-" + "-+-".join("-" * w for w in widths) + "-+"
    fmt = "| " + " | ".join(f"{{:<{w}}}" for w in widths) + " |"
    print(sep)
    print(fmt.format(*headers))
    print(sep)
    for row in rows:
        print(fmt.format(*[str(c) for c in row]))
    print(sep)


# ============================================================
# Pattern 1: Style Transfer
# ============================================================
BASIC_STYLES = {
    "비즈니스 격식체": "당신은 기업 커뮤니케이션 전문가입니다. 원문의 의미를 100% 보존하면서, 비즈니스 격식체(존댓말, 공식 문서 톤)로만 변환하세요. 정보를 추가하거나 삭제하지 마세요.",
    "기술 보고서": "당신은 시니어 SRE 엔지니어입니다. 원문의 의미를 보존하면서, 기술 인시던트 보고서 스타일로 변환하세요. 객관적이고 사실 기반으로, 감정적 표현은 제거하세요.",
    "친절한 고객 응대": "당신은 고객 서비스 매니저입니다. 원문의 의미를 보존하면서, 고객에게 공감하고 안심시키는 톤으로 변환하세요. 따뜻하고 프로페셔널하게.",
}

ADVANCED_STYLES = {
    "의료 소견서": "당신은 대학병원 전문의입니다. 원문의 상황을 의료 소견서/진료 기록 스타일로 변환하세요. 증상, 소견, 조치계획 구조를 사용하고 의학 용어를 적절히 포함하세요. 정보를 추가하지 마세요.",
    "법률 의견서": "당신은 IT 전문 변호사입니다. 원문의 의미를 보존하면서, 법률 의견서/내용증명 스타일로 변환하세요. '~한 바', '~에 해당하는', '~할 의무가 있으므로' 같은 법률 어투를 사용하세요.",
    "감정 강도 MAX": "당신은 감정 표현 전문가입니다. 원문의 의미를 보존하면서, 감정의 강도를 최대한 높여서 표현하세요. 분노, 절박함, 좌절을 극적으로 표현하되, 원문의 핵심 정보는 모두 유지하세요.",
    "감정 강도 MIN": "당신은 로봇 어시스턴트입니다. 원문의 의미를 보존하면서, 모든 감정을 제거하고 순수한 사실만 기술하세요. 마치 기계가 보고하듯, 형용사와 감정 표현을 모두 삭제하세요.",
}

STYLE_INPUT_BASIC = "서버가 또 터졌어요. 빨리 확인해주세요. 어제도 같은 문제였는데 아직도 안 고쳐진 거예요?"

STYLE_INPUT_ADVANCED = "환자가 3일째 두통을 호소하고 있습니다. 진통제를 먹어도 낫지 않고, 어지러움도 동반됩니다. 가족력으로 뇌졸중 이력이 있어 걱정됩니다."


def demo_style_transfer(advanced=False):
    """톤/문체 변환 데모"""
    print("=" * 60)
    title = "📝 Pattern 1: Style Transfer (톤·문체 변환)"
    if advanced:
        title += " [ADVANCED]"
    print(title)
    print("=" * 60)

    if advanced:
        inputs = [
            ("IT 장애 신고", STYLE_INPUT_BASIC, {**BASIC_STYLES, **ADVANCED_STYLES}),
            ("의료 상담", STYLE_INPUT_ADVANCED, {
                "일반인 설명": "당신은 환자 교육 전문 간호사입니다. 의료 정보를 전문 지식이 없는 일반인도 쉽게 이해할 수 있도록 변환하세요. 비유와 쉬운 단어를 사용하세요.",
                "응급실 트리아지": "당신은 응급실 트리아지 간호사입니다. 원문을 응급도 분류 보고서 형태로 변환하세요. 활력징후 확인 필요사항, 긴급도(ESI 1-5), 추천 검사를 구조화하세요.",
                "보험 청구서": "당신은 의료보험 심사 전문가입니다. 원문을 보험 청구 사유서 스타일로 변환하세요. 상병코드 추정, 필요 검사, 급여 적용 근거를 포함하세요.",
            }),
        ]
    else:
        inputs = [("IT 장애 신고", STYLE_INPUT_BASIC, BASIC_STYLES)]

    all_metrics = []

    for scenario_name, original, styles in inputs:
        print(f"\n{'─' * 40}")
        print(f"🔹 시나리오: {scenario_name}")
        print(f"🔹 원문: {original}\n")

        for style_name, system_prompt in styles.items():
            result = call_bedrock(system_prompt, f"다음 텍스트를 변환하세요:\n\n{original}")
            print(f"🔸 [{style_name}]")
            print(f"   {result}\n")

            if advanced:
                scores = evaluate_preservation(original, result)
                all_metrics.append((
                    scenario_name[:8], style_name,
                    count_chars(original), count_chars(result),
                    scores.get("preservation", "-"),
                    scores.get("no_distortion", "-"),
                    scores.get("tone_shift", "-"),
                ))

    if advanced and all_metrics:
        print("\n📊 Style Transfer 메트릭")
        print_table(
            ["Scenario", "Style", "Orig", "Trans", "Preserv", "NoDist", "ToneShift"],
            all_metrics,
        )


# ============================================================
# Pattern 2: Reverse Neutralization
# ============================================================
BASIC_PERSONAS = {
    "AWS Solutions Architect": """당신은 10년 경력의 AWS Solutions Architect입니다.
실제 마이그레이션 프로젝트를 50건 이상 수행한 경험이 있습니다.
이론이 아닌 실전 경험에 기반해서, 구체적인 AWS 서비스명과 아키텍처 패턴을 포함하여 답하세요.
"일반적으로"나 "경우에 따라 다르지만" 같은 회피 표현 대신, 명확한 의견과 근거를 제시하세요.
실패 사례에서 배운 교훈도 포함하세요.""",
    "스타트업 CTO": """당신은 시리즈B 스타트업의 CTO입니다. 엔지니어 15명을 리드하고 있습니다.
제한된 예산과 인력으로 빠르게 실행해야 하는 환경입니다.
"완벽한" 솔루션보다 "지금 당장 가능한" 현실적인 방법을 우선하세요.
비용 효율, 운영 복잡도, 팀 역량을 핵심 기준으로 판단하세요.
과감한 의견도 OK.""",
}

ADVANCED_PERSONAS = {
    "보안 전문가 (CISO)": """당신은 대기업 CISO(Chief Information Security Officer)입니다. 15년 보안 경력.
모든 기술 결정을 보안 관점에서 평가합니다. 위협 모델링, 컴플라이언스(ISMS, SOC2, GDPR), 제로트러스트를 핵심 프레임워크로 사용합니다.
"보안은 나중에" 같은 태도에 강하게 반대하세요. 실제 침해 사례를 인용하세요.
보안 위험을 구체적 수치(발생 확률, 피해 규모)로 정량화하세요.""",
    "데이터 사이언티스트": """당신은 FAANG 출신 시니어 데이터 사이언티스트(8년 경력)입니다.
모든 문제를 데이터 중심으로 접근합니다. "느낌"이 아닌 "숫자"로 말합니다.
A/B 테스트, 통계적 유의성, ROI 계산을 항상 요구합니다.
"best practice"라는 말 대신 "evidence"를 요구하세요.
마이그레이션을 데이터 파이프라인, 모델 서빙, MLOps 관점에서 평가하세요.""",
    "규제 컨설턴트": """당신은 금융/공공 규제 전문 컨설턴트(12년 경력)입니다.
금융위원회, 개인정보보호위원회, 공공 클라우드 보안 인증(CSAP) 심사 경험.
모든 기술 결정을 규제 준수 관점에서 평가합니다.
위반 시 과태료, 업무정지 등 구체적 제재를 언급하세요.
"기술적으로 가능하지만 규제상 불가"인 케이스를 명확히 짚어주세요.""",
}

NEUTRALIZATION_QUESTIONS = {
    "basic": "클라우드 마이그레이션을 고려하고 있는데, 어떤 전략이 좋을까요?",
    "advanced": "우리 회사(금융권, 직원 3000명)가 온프레미스 코어 뱅킹 시스템을 클라우드로 이전하려 합니다. 어떻게 접근해야 할까요?",
}


def demo_reverse_neutralization(advanced=False):
    """도메인 전문가 페르소나로 중립 모드 해제"""
    print("=" * 60)
    title = "🎭 Pattern 2: Reverse Neutralization (도메인 전문가 페르소나)"
    if advanced:
        title += " [ADVANCED]"
    print(title)
    print("=" * 60)

    question = NEUTRALIZATION_QUESTIONS["advanced" if advanced else "basic"]
    personas = {**BASIC_PERSONAS, **(ADVANCED_PERSONAS if advanced else {})}

    print(f"\n🔹 질문: {question}\n")

    # 중립 응답
    neutral = call_bedrock("당신은 AI 어시스턴트입니다. 객관적으로 답하세요.", question)
    print(f"🔸 [중립 응답 — 일반 AI]")
    print(f"   {neutral[:300]}...\n")

    metrics = [("중립 AI", count_chars(neutral), avg_sentence_len(neutral), "-")]

    for persona_name, system_prompt in personas.items():
        result = call_bedrock(system_prompt, question)
        print(f"🔸 [{persona_name} 페르소나]")
        print(f"   {result[:500]}...\n")

        metrics.append((persona_name, count_chars(result), avg_sentence_len(result), "-"))

    if advanced:
        # 각 응답의 전문성/구체성을 LLM으로 평가
        print("\n📊 Reverse Neutralization 메트릭")
        print_table(
            ["Persona", "Length(chars)", "AvgSentLen", "Note"],
            metrics,
        )


# ============================================================
# Pattern 3: Content Optimization (Self-Refine)
# ============================================================
OPTIMIZATION_TASKS = {
    "basic": {
        "task": "Amazon Bedrock의 주요 특징을 3문장으로 설명하세요. 대상: 클라우드 경험이 없는 경영진.",
        "role": "당신은 AWS 기술 마케팅 전문가입니다.",
        "criteria": """1. 명확성 (1-5): 전문 용어 없이 경영진이 바로 이해할 수 있는가?
2. 간결성 (1-5): 3문장 이내, 군더더기 없는가?
3. 설득력 (1-5): 비즈니스 가치가 명확한가?
4. 정확성 (1-5): 기술적으로 정확한가?""",
        "criteria_keys": ["명확성", "간결성", "설득력", "정확성"],
        "rounds": 1,
    },
    "advanced": {
        "task": "Amazon Bedrock을 활용한 고객 서비스 자동화 도입 제안서의 핵심 요약을 5문장으로 작성하세요. 대상: 금융권 CIO. ROI와 보안을 강조하세요.",
        "role": "당신은 금융권 전문 AWS 컨설턴트입니다.",
        "criteria": """1. 명확성 (1-5): CIO가 바로 의사결정할 수 있을 정도로 명확한가?
2. 간결성 (1-5): 5문장 이내, 불필요한 수식어 없는가?
3. 설득력 (1-5): ROI와 비즈니스 임팩트가 구체적인가?
4. 정확성 (1-5): 기술적으로 정확하고 과장이 없는가?
5. 보안/규제 (1-5): 금융권 규제(전자금융감독규정 등) 관점을 반영했는가?
6. 실행가능성 (1-5): 구체적인 다음 단계(PoC 등)가 제시되었는가?""",
        "criteria_keys": ["명확성", "간결성", "설득력", "정확성", "보안/규제", "실행가능성"],
        "rounds": 3,
    },
}


def run_self_refine(task_config: dict, verbose=True) -> list:
    """Self-Refine 루프 실행, 라운드별 점수 반환"""
    task = task_config["task"]
    role = task_config["role"]
    criteria = task_config["criteria"]
    criteria_keys = task_config["criteria_keys"]
    rounds = task_config["rounds"]

    if verbose:
        print(f"\n🔹 태스크: {task}")
        print(f"   라운드: {rounds}회\n")

    # Initial generation
    draft = call_bedrock(role, task, temperature=0.8)
    if verbose:
        print(f"📝 [1차 생성]")
        print(f"   {draft}\n")

    round_scores = []

    for r in range(rounds):
        # Critique
        critique_prompt = f"""다음 텍스트를 아래 기준으로 평가하세요.

## 평가 기준
{criteria}

## 텍스트
{draft}

## 출력 형식
각 기준 점수와 구체적 개선점을 JSON으로 출력하세요. 키는 기준명, 값은 {{"score": N, "feedback": "..."}} 형태."""

        critique = call_bedrock(
            "당신은 기술 문서 품질 심사관입니다. 냉정하고 구체적으로 평가하세요.",
            critique_prompt, temperature=0.3,
        )
        scores = parse_critique_scores(critique)
        avg = round(sum(scores.values()) / len(scores), 1) if scores else 0
        round_scores.append({"round": r + 1, "type": "critique", "scores": scores, "avg": avg})

        if verbose:
            print(f"🔍 [Round {r+1} 평가] 평균: {avg}/5")
            for k, v in scores.items():
                print(f"   {k}: {v}/5")
            print()

        # Refine
        refine_prompt = f"""원본 텍스트와 피드백을 기반으로 개선된 버전을 작성하세요.

## 원본
{draft}

## 피드백
{critique}

## 원래 태스크
{task}

피드백을 모두 반영하여 개선된 최종 버전만 출력하세요."""

        draft = call_bedrock(role + " 피드백을 꼼꼼히 반영하세요.", refine_prompt, temperature=0.5)
        if verbose:
            print(f"✅ [Round {r+1} 개선]")
            print(f"   {draft}\n")

    # Final evaluation
    final_critique_prompt = f"""다음 텍스트를 아래 기준으로 평가하세요.

## 평가 기준
{criteria}

## 텍스트
{draft}

## 출력 형식
각 기준 점수와 구체적 개선점을 JSON으로 출력하세요."""

    final_critique = call_bedrock(
        "당신은 기술 문서 품질 심사관입니다.", final_critique_prompt, temperature=0.3,
    )
    final_scores = parse_critique_scores(final_critique)
    final_avg = round(sum(final_scores.values()) / len(final_scores), 1) if final_scores else 0
    round_scores.append({"round": rounds + 1, "type": "final", "scores": final_scores, "avg": final_avg})

    if verbose and rounds > 1:
        print(f"📊 최종 평가: 평균 {final_avg}/5")
        for k, v in final_scores.items():
            print(f"   {k}: {v}/5")

    return round_scores


def demo_content_optimization(advanced=False):
    """Self-Refine 루프 데모"""
    print("=" * 60)
    title = "🔄 Pattern 3: Content Optimization (Self-Refine 루프)"
    if advanced:
        title += " [ADVANCED — Multi-Round]"
    print(title)
    print("=" * 60)

    config = OPTIMIZATION_TASKS["advanced" if advanced else "basic"]
    round_scores = run_self_refine(config, verbose=True)

    if advanced and len(round_scores) > 1:
        print("\n📊 라운드별 점수 추이")
        headers = ["Round"] + config["criteria_keys"] + ["AVG"]
        rows = []
        for rs in round_scores:
            row = [f"R{rs['round']}" if rs["type"] == "critique" else "Final"]
            for k in config["criteria_keys"]:
                row.append(rs["scores"].get(k, "-"))
            row.append(rs["avg"])
            rows.append(row)
        print_table(headers, rows)

        # Improvement summary
        if len(round_scores) >= 2:
            first_avg = round_scores[0]["avg"]
            last_avg = round_scores[-1]["avg"]
            delta = round(last_avg - first_avg, 1)
            print(f"\n📈 개선: {first_avg} → {last_avg} ({'+' if delta >= 0 else ''}{delta})")


# ============================================================
# Main
# ============================================================
if __name__ == "__main__":
    advanced = "--advanced" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--advanced"]
    choice = args[0] if args else None

    demos = {
        "1": ("Style Transfer", demo_style_transfer),
        "2": ("Reverse Neutralization", demo_reverse_neutralization),
        "3": ("Content Optimization", demo_content_optimization),
        "all": ("전체 데모", None),
    }

    if not choice:
        mode = "ADVANCED" if advanced else "BASIC"
        print(f"\n🎯 LLM 출력 제어 디자인 패턴 데모 [{mode}]")
        print(f"   Model: {MODEL_ID}\n")
        for k, (name, _) in demos.items():
            print(f"   [{k}] {name}")
        print(f"\n   --advanced 플래그로 심화 모드 실행")
        print()
        choice = input("선택 (1/2/3/all): ").strip()

    if choice == "all":
        demo_style_transfer(advanced)
        print("\n")
        demo_reverse_neutralization(advanced)
        print("\n")
        demo_content_optimization(advanced)
    elif choice in demos:
        demos[choice][1](advanced)
    else:
        print("1, 2, 3, 또는 all을 선택하세요.")
