# LLM Output Control Design Patterns Demo

LLM 출력 제어 디자인 패턴을 **Amazon Bedrock Claude Sonnet 4.5 (Global Inference)**로 구현한 데모입니다.

> 📖 Reference: [Generative AI Design Patterns](https://www.oreilly.com/library/view/generative-ai-design/9798341622654/) — Lakshmanan & Hapke, O'Reilly 2025
>
> 📝 Blog: [LLM 출력 제어 디자인 패턴 1편](https://jesamkim.github.io/ai-tech-blog/posts/2026-02-18-llm-%EC%B6%9C%EB%A0%A5-%EC%A0%9C%EC%96%B4-%EB%94%94%EC%9E%90%EC%9D%B8-%ED%8C%A8%ED%84%B4-logits-masking%EB%B6%80%ED%84%B0-grammar-constraint-style-t/) | [2편](https://jesamkim.github.io/ai-tech-blog/posts/2026-02-18-llm-%EC%B6%9C%EB%A0%A5-%EC%A0%9C%EC%96%B4-%EB%94%94%EC%9E%90%EC%9D%B8-%ED%8C%A8%ED%84%B4-2%ED%8E%B8-reverse-neutralization%EA%B3%BC-content-optimiza/)

![Architecture](images/architecture.png)

## Quick Start

```bash
pip install boto3

# Basic mode
python3 demo.py 1          # Style Transfer
python3 demo.py 2          # Reverse Neutralization
python3 demo.py 3          # Content Optimization
python3 demo.py all        # Run all

# Advanced mode (more scenarios + metrics)
python3 demo.py 1 --advanced
python3 demo.py 2 --advanced
python3 demo.py 3 --advanced
python3 demo.py all --advanced
```

## Patterns

### Pattern 1: Style Transfer — 톤·문체 변환

같은 입력에 System Prompt만 바꿔서 다른 톤으로 변환합니다. 콘텐츠(의미)는 보존하고 스타일만 변경합니다.

**Basic mode** — 3가지 스타일:

| Style | Output (요약) |
|-------|--------------|
| 비즈니스 격식체 | 서버에 장애가 발생하였습니다. 조속한 확인을 요청드립니다. |
| 기술 보고서 | Incident Report — 서버 장애 재발, 근본 원인 분석 필요 |
| 친절한 고객 응대 | 고객님께서 겪고 계신 불편함을 진심으로 공감하며... |

**Advanced mode** — 7가지 스타일 + 의료 도메인 시나리오 + 메트릭:
- 🆕 의료 소견서, 법률 의견서, 감정 강도 MAX/MIN
- 🆕 의료 상담 → 일반인 설명 / 응급실 트리아지 / 보험 청구서
- 📊 의미 보존도 자동 평가 (LLM-as-Judge, 1-5점)

```
📊 Style Transfer 메트릭
+----------+-----------+------+-------+---------+--------+-----------+
| Scenario | Style     | Orig | Trans | Preserv | NoDist | ToneShift |
+----------+-----------+------+-------+---------+--------+-----------+
| IT 장애    | 비즈니스 격식체  | 39   | 61    | 5       | 5      | 5         |
| IT 장애    | 기술 보고서    | 39   | 173   | 5       | 5      | 5         |
| IT 장애    | 법률 의견서    | 39   | 455   | 5       | 4      | 5         |
| IT 장애    | 감정 MAX    | 39   | 333   | 5       | 4      | 5         |
| IT 장애    | 감정 MIN    | 39   | 151   | 5       | 5      | 5         |
| 의료 상담    | 응급실 트리아지  | 60   | 615   | 4       | 4      | 5         |
| 의료 상담    | 보험 청구서    | 60   | 782   | 5       | 5      | 5         |
+----------+-----------+------+-------+---------+--------+-----------+
```

### Pattern 2: Reverse Neutralization — 도메인 전문가 페르소나

RLHF 정렬로 인해 중립적인 답변만 하는 LLM을, 도메인 전문가의 관점으로 전환합니다.

**Basic mode** — 2가지 페르소나:
| Persona | 특징 |
|---------|------|
| 🏗️ AWS SA (10년) | 실전 경험 기반, 구체적 서비스명, 실패 사례 포함 |
| 🚀 스타트업 CTO | 현실적 비용/인력 분석, "지금 당장" 실행 가능한 방법 |

**Advanced mode** — 5가지 페르소나 + 금융권 심화 질문:
- 🆕 🔒 보안 전문가 (CISO) — 위협 모델링, 제로트러스트, 침해 사례
- 🆕 📊 데이터 사이언티스트 — A/B 테스트, 통계, MLOps 관점
- 🆕 ⚖️ 규제 컨설턴트 — 금융위원회, CSAP, 과태료 정량화
- 📊 페르소나별 응답 길이/문장 복잡도 비교

### Pattern 3: Content Optimization — Self-Refine 루프

생성 → 자기 평가 → 피드백 반영 재생성의 반복 루프로 품질을 체계적으로 개선합니다.

![Self-Refine Loop](images/self-refine-loop.png)

**Basic mode** — 1 round:
- 4개 기준 평가 (명확성, 간결성, 설득력, 정확성)
- 생성 → 평가 → 개선 1회

**Advanced mode** — 3 rounds + 6개 기준:
- 🆕 보안/규제, 실행가능성 기준 추가
- 🆕 금융권 CIO 대상 제안서 요약 태스크
- 🆕 3라운드 반복 → 라운드별 점수 추이 테이블
- 📊 개선도 자동 산출 (예: 3.8 → 4.5, +0.7)

```
📊 라운드별 점수 추이
+-------+------+------+------+------+--------+--------+-----+
| Round | 명확성 | 간결성 | 설득력 | 정확성 | 보안/규제 | 실행가능성 | AVG |
+-------+------+------+------+------+--------+--------+-----+
| R1    | 4    | 3    | 4    | 4    | 3      | 3      | 3.5 |
| R2    | 4    | 4    | 5    | 5    | 4      | 4      | 4.3 |
| R3    | 5    | 5    | 5    | 5    | 4      | 5      | 4.8 |
| Final | 5    | 5    | 5    | 5    | 5      | 5      | 5.0 |
+-------+------+------+------+------+--------+--------+-----+
📈 개선: 3.5 → 5.0 (+1.5)
```

## Model

| | |
|---|---|
| **Model** | Claude Sonnet 4.5 |
| **Model ID** | `global.anthropic.claude-sonnet-4-5-20250929-v1:0` |
| **API** | Amazon Bedrock Converse API |

## Project Structure

```
output-control-patterns-demo/
├── demo.py              # 메인 데모 스크립트 (basic + advanced)
├── README.md
└── images/
    ├── architecture.png       # 전체 아키텍처
    └── self-refine-loop.png   # Self-Refine 루프 다이어그램
```

## Metrics

Advanced 모드에서 자동 산출되는 메트릭:

| Pattern | Metric | Method |
|---------|--------|--------|
| Style Transfer | 의미 보존도 (1-5) | LLM-as-Judge |
| Style Transfer | 텍스트 길이 변화 | 글자 수 비교 |
| Reverse Neutralization | 응답 길이/복잡도 | 글자 수 + 평균 문장 길이 |
| Content Optimization | 라운드별 점수 추이 | JSON 자동 파싱 |
| Content Optimization | 개선도 | 첫 라운드 vs 최종 평균 점수 차이 |

## References

1. Lakshmanan, V. & Hapke, H. (2025). *Generative AI Design Patterns.* O'Reilly Media.
2. Madaan, A., et al. (2023). *Self-Refine: Iterative Refinement with Self-Feedback.* [arXiv:2303.17651](https://arxiv.org/abs/2303.17651)
3. Ouyang, L., et al. (2022). *Training language models to follow instructions with human feedback.* [arXiv:2203.02155](https://arxiv.org/abs/2203.02155)
4. Reif, E., et al. (2022). *A Recipe for Arbitrary Text Style Transfer with Large Language Models.* ACL 2022.
5. Zheng, L., et al. (2023). *Judging LLM-as-a-Judge.* [arXiv:2306.05685](https://arxiv.org/abs/2306.05685)
