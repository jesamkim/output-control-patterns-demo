# Output Control Patterns Demo

LLM 출력 제어 디자인 패턴 데모 — Bedrock Claude Sonnet 4.5 (Global Inference)

## 패턴
1. **Style Transfer** — 톤/문체 변환 (격식체, 기술보고서, 고객응대)
2. **Reverse Neutralization** — 도메인 전문가 페르소나 (AWS SA, 스타트업 CTO)
3. **Content Optimization** — Self-Refine 루프 (생성 → 평가 → 재생성)

## 실행
```bash
python3 demo.py 1     # Style Transfer
python3 demo.py 2     # Reverse Neutralization
python3 demo.py 3     # Content Optimization
python3 demo.py all   # 전체
```

## 배포 위치
- **개발**: `/home/ec2-user/clawd/projects/output-control-patterns-demo/`
- **실행 서버**: `2026-poc:/Workshop/yan/output-control-patterns-demo/`

## 싱크
```bash
rsync -avz projects/output-control-patterns-demo/ 2026-poc:/Workshop/yan/output-control-patterns-demo/
```
