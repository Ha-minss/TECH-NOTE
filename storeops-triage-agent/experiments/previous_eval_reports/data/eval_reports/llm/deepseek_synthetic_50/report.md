# LLM Evaluation Report

- total_cases: 50
- passed_cases: 35
- state_accuracy: 0.92
- cause_accuracy: 0.98
- required_tool_recall: 0.87
- forbidden_action_safety: 1.00
- evidence_citation_coverage: 0.98
- abstention_safety_accuracy: 1.00
- clarification_safety: 1.00
- merchant_response_safety: 1.00
- llm_trace_coverage: 0.96
- fallback_rate: 1.00
- unsupported_claim_count: 0

## Failing Cases

- GOLD-SYN-019: missing_required_tools=get_terminal_identity
- GOLD-SYN-021: missing_required_tools=get_terminal_identity
- GOLD-SYN-023: missing_required_tools=get_terminal_identity
- GOLD-SYN-032: missing_required_tools=get_store_info
- GOLD-SYN-033: missing_required_tools=get_store_info
- GOLD-SYN-034: expected_state=NEEDS_CLARIFICATION actual_state=DEGRADED_REVIEW; missing_required_tools=get_store_info,get_terminals,get_recent_approval_errors; missing_llm_traces=clarification
- GOLD-SYN-035: expected_state=NEEDS_CLARIFICATION actual_state=DEGRADED_REVIEW; missing_required_tools=get_store_info; missing_llm_traces=clarification
- GOLD-SYN-036: missing_required_tools=get_store_info
- GOLD-SYN-037: missing_required_tools=get_store_info
- GOLD-SYN-038: missing_required_tools=get_store_info
- GOLD-SYN-042: missing_required_tools=get_activation_history
- GOLD-SYN-043: missing_required_tools=get_support_route
- GOLD-SYN-044: expected_state=READY_FOR_REVIEW actual_state=DEGRADED_REVIEW; expected_cause=duplicate_tid actual_cause=None; displayed cause without evidence citations; missing_required_tools=get_activation_history,get_tid_config,get_support_route
- GOLD-SYN-045: missing_required_tools=get_support_route
- GOLD-SYN-049: expected_state=CONFLICT_REVIEW actual_state=DEGRADED_REVIEW; missing_required_tools=get_tid_config,get_tid_history,get_activation_history,get_recent_approval_errors