# Agentic AI for Environmental Assessment

Hệ thống mẫu theo kế hoạch triển khai gồm 9 tác nhân:
- Data Ingestion Agent
- Retrieval Agent
- Reasoning Agent
- Tool Agent
- Memory Agent
- Evaluation Agent
- Reliability Monitor
- Governance Agent
- Orchestrator

## Kiến trúc
Xem sơ đồ tại `diagrams/architecture.md`.

## Workflow
1. Task framing
2. Data ingestion & validation
3. Knowledge retrieval (mock RAG corpus)
4. Analytical reasoning
5. Tool execution
6. Memory update
7. Evaluation & reliability scoring
8. Governance checks
9. Report generation

## Chạy demo
```bash
PYTHONPATH=src python -m agentic_env_ai.demo
```

Kết quả report được ghi vào `reports/environmental_assessment_report.json`.

## Deliverables có trong repo
- Source code: `src/agentic_env_ai/`
- Architecture diagrams: `diagrams/architecture.md`
- Environmental assessment reports: `reports/`
- Evaluation and monitoring logs: `logs/evaluation_monitoring_log.json`

## Data ingestion (hoàn chỉnh)
- Hỗ trợ alias field (vd: `pm2_5`, `water_ph`, `temp_c`, `no2_ppb`).
- Chuẩn hóa dữ liệu về schema canonical: `pm25`, `pm10`, `no2`, `ph`, `temperature_c`.
- Chuẩn hóa đơn vị NO2 từ `ppb` sang `ug/m3` khi nhận `no2_ppb`.
- Kiểm tra kiểu dữ liệu numeric, kiểm tra ngưỡng vật lý (hard bounds).
- Ghi nhận cảnh báo vượt ngưỡng vận hành và chấm điểm chất lượng (`quality_score`).
- Trả về metadata ingestion trong report (`report["ingestion"]`).
