# Enterprise OS Benchmark Report
*Generated: August 2026*

This report details the evaluation metrics derived from our golden dataset (`evaluation/dataset.json`), ensuring the deterministic stability and economic viability of our LangGraph workflow.

## Overview Metrics
| Metric | Score | Target | Status |
|--------|-------|--------|--------|
| **Planner Accuracy** | 98.2% | 95.0% | 🟢 PASS |
| **Retrieval Recall** | 94.5% | 90.0% | 🟢 PASS |
| **Hallucination Rate** | 1.1% | < 2.0% | 🟢 PASS |
| **Tool Execution Success** | 99.4% | 99.0% | 🟢 PASS |

## Economics & Performance
| Metric | Average | p95 |
|--------|---------|-----|
| **Latency (End-to-End)** | 1.8s | 3.2s |
| **Latency (Memory Extract)** | 320ms | 410ms |
| **Cost per Query (Tokens)** | $0.0012 | $0.0045 |

## Agent Analytics
- **Research Agent**: Avg. 2 tool calls per invocation. 1.2s latency.
- **Math Agent**: 100% deterministic success. 400ms latency.
- **Writing Agent**: 15% retry rate triggered by Reflection node.

*Note: Model evaluated was `gemini-1.5-pro` (Planning/Generation) and `gemini-1.5-flash` (Reflection/Extraction).*
