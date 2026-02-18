#!/usr/bin/env python3
"""
LLM 출력 제어 디자인 패턴 데모
- Pattern 1: Style Transfer (톤/문체 변환)
- Pattern 2: Reverse Neutralization (도메인 전문가 페르소나)
- Pattern 3: Content Optimization (Self-Refine 루프)

Bedrock Claude Sonnet 4.5 (Global Inference) 사용
"""

import json
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
# Pattern 1: Style Transfer
# ============================================================
def demo_style_transfer():
    """톤/문체 변환 데모 — 같은 내용을 다른 스타일로"""
    print("=" * 60)
    print("📝 Pattern 1: Style Transfer (톤·문체 변환)")
    print("=" * 60)

    original = "서버가 또 터졌어요. 빨리 확인해주세요. 어제도 같은 문제였는데 아직도 안 고쳐진 거예요?"

    styles = {
        "비즈니스 격식체": "당신은 기업 커뮤니케이션 전문가입니다. 원문의 의미를 100% 보존하면서, 비즈니스 격식체(존댓말, 공식 문서 톤)로만 변환하세요. 정보를 추가하거나 삭제하지 마세요.",
        "기술 보고서": "당신은 시니어 SRE 엔지니어입니다. 원문의 의미를 보존하면서, 기술 인시던트 보고서 스타일로 변환하세요. 객관적이고 사실 기반으로, 감정적 표현은 제거하세요.",
        "친절한 고객 응대": "당신은 고객 서비스 매니저입니다. 원문의 의미를 보존하면서, 고객에게 공감하고 안심시키는 톤으로 변환하세요. 따뜻하고 프로페셔널하게.",
    }

    print(f"\n🔹 원문: {original}\n")

    for style_name, system_prompt in styles.items():
        result = call_bedrock(system_prompt, f"다음 텍스트를 변환하세요:\n\n{original}")
        print(f"🔸 [{style_name}]")
        print(f"   {result}\n")


# ============================================================
# Pattern 2: Reverse Neutralization
# ============================================================
def demo_reverse_neutralization():
    """도메인 전문가 페르소나로 중립 모드 해제"""
    print("=" * 60)
    print("🎭 Pattern 2: Reverse Neutralization (도메인 전문가 페르소나)")
    print("=" * 60)

    question = "클라우드 마이그레이션을 고려하고 있는데, 어떤 전략이 좋을까요?"

    # 1) 중립 응답 (기본)
    print(f"\n🔹 질문: {question}\n")
    neutral = call_bedrock(
        "당신은 AI 어시스턴트입니다. 객관적으로 답하세요.",
        question,
    )
    print(f"🔸 [중립 응답 — 일반 AI]")
    print(f"   {neutral[:300]}...\n")

    # 2) Reverse Neutralization — AWS SA 페르소나
    personas = {
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

    for persona_name, system_prompt in personas.items():
        result = call_bedrock(system_prompt, question)
        print(f"🔸 [{persona_name} 페르소나]")
        print(f"   {result[:400]}...\n")


# ============================================================
# Pattern 3: Content Optimization (Self-Refine)
# ============================================================
def demo_content_optimization():
    """Self-Refine 루프 — 생성 → 평가 → 재생성"""
    print("=" * 60)
    print("🔄 Pattern 3: Content Optimization (Self-Refine 루프)")
    print("=" * 60)

    task = "Amazon Bedrock의 주요 특징을 3문장으로 설명하세요. 대상: 클라우드 경험이 없는 경영진."

    print(f"\n🔹 태스크: {task}\n")

    # Step 1: Initial Generation
    draft = call_bedrock(
        "당신은 AWS 기술 마케팅 전문가입니다.",
        task,
        temperature=0.8,
    )
    print(f"📝 [1차 생성]")
    print(f"   {draft}\n")

    # Step 2: Self-Critique
    critique_prompt = f"""다음 텍스트를 아래 기준으로 평가하세요.

## 평가 기준
1. 명확성 (1-5): 전문 용어 없이 경영진이 바로 이해할 수 있는가?
2. 간결성 (1-5): 3문장 이내, 군더더기 없는가?
3. 설득력 (1-5): 비즈니스 가치가 명확한가?
4. 정확성 (1-5): 기술적으로 정확한가?

## 텍스트
{draft}

## 출력 형식
각 기준 점수와 구체적 개선점을 JSON으로:
{{"명확성": {{"score": N, "feedback": "..."}}, "간결성": {{"score": N, "feedback": "..."}}, "설득력": {{"score": N, "feedback": "..."}}, "정확성": {{"score": N, "feedback": "..."}}}}"""

    critique = call_bedrock(
        "당신은 기술 문서 품질 심사관입니다. 냉정하고 구체적으로 평가하세요.",
        critique_prompt,
        temperature=0.3,
    )
    print(f"🔍 [자기 평가]")
    print(f"   {critique}\n")

    # Step 3: Refinement
    refine_prompt = f"""원본 텍스트와 피드백을 기반으로 개선된 버전을 작성하세요.

## 원본
{draft}

## 피드백
{critique}

## 원래 태스크
{task}

피드백을 모두 반영하여 개선된 최종 버전만 출력하세요."""

    refined = call_bedrock(
        "당신은 AWS 기술 마케팅 전문가입니다. 피드백을 꼼꼼히 반영하세요.",
        refine_prompt,
        temperature=0.5,
    )
    print(f"✅ [개선된 최종 버전]")
    print(f"   {refined}\n")


# ============================================================
# Main
# ============================================================
if __name__ == "__main__":
    import sys

    demos = {
        "1": ("Style Transfer", demo_style_transfer),
        "2": ("Reverse Neutralization", demo_reverse_neutralization),
        "3": ("Content Optimization", demo_content_optimization),
        "all": ("전체 데모", None),
    }

    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        print("\n🎯 LLM 출력 제어 디자인 패턴 데모")
        print(f"   Model: {MODEL_ID}\n")
        for k, (name, _) in demos.items():
            print(f"   [{k}] {name}")
        print()
        choice = input("선택 (1/2/3/all): ").strip()

    if choice == "all":
        demo_style_transfer()
        print("\n")
        demo_reverse_neutralization()
        print("\n")
        demo_content_optimization()
    elif choice in demos:
        demos[choice][1]()
    else:
        print("1, 2, 3, 또는 all을 선택하세요.")
