def generate_report(text: str, task_type: str) -> dict:
    """
    Orchestrator that routes the parsed document text to the appropriate AI pipeline
    and generates a final report.
    """
    from backend.pipelines.summarizer import run_summarization, analyze_contract
    from backend.pipelines.contract_analyzer import run_contract_analysis
    from backend.services.explainability import generate_explanation

    report = {
        "task_type": task_type,
        "metadata": {"doc_length_chars": len(text)}
    }

    if task_type == "summarize_case":
        # ── Summarization only ─────────────────────────────────────────────
        report["summary_data"] = run_summarization(text)

    elif task_type == "analyze_contract":
        # ── Full contract analysis + summarization ─────────────────────────

        # 1. Run clause classifier
        analysis = run_contract_analysis(text)

        # 2. Pass each clause through explainability layer
        analyzed_clauses = analysis.get("analyzed_clauses", [])
        for i, clause in enumerate(analyzed_clauses):
            analyzed_clauses[i] = generate_explanation(clause)

        report["contract_analysis"] = analysis

        # 3. Build labeled_clauses dict from analyzed clauses
        #    contract_analyzer stores label in "type" key  e.g. "Termination", "Payment"
        labeled_clauses = {}
        for clause in analyzed_clauses:
            label       = clause.get("type", "General")   # ← "type" not "label"
            clause_text = clause.get("clause_text", "")
            if clause_text:
                labeled_clauses.setdefault(label, []).append(clause_text)

        # 4. Run summarizer — full contract + per label
        report["summary_data"] = analyze_contract(text, labeled_clauses)

    elif task_type == "deep_research":
        # ── Deep research ──────────────────────────────────────────────────
        report["research_data"] = generate_explanation({
            "clause_text": text,
            "risk_level":  "RESEARCH",
            "risk_reason": "Deep inquiry"
        })

    else:
        raise ValueError(f"Unknown task type: {task_type}")

    return report


def route_document(text: str, task_type: str = "analyze_contract") -> dict:
    return generate_report(text, task_type)
