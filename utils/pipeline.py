"""
The assessment pipeline.

Steps (each step is at least one AI call):
 1. Extract facts
 2. Coverage: is the entity / information covered by the NDB scheme?      (RAG)
 3. Element 1: unauthorised access, disclosure or loss                     (RAG)
 4. Element 2: likely serious harm, factor by factor (s 26WG)              (RAG)
 5. Exception: remedial action (s 26WF)                                    (RAG)
 -  Rule-based conclusion (boolean if-then logic, Lab 1 style)
 6. Reflection. If the reviewer finds a fixable error, the affected steps are re-run
    with the reviewer's feedback and the analysis is reviewed again (looping logic,
    Lab 2 style), up to MAX_REVISION_ROUNDS times.
 7. Advice memo
 8. Draft s 26WK statement to the Commissioner (only for eligible data breaches)  (RAG)

A run therefore makes at least 7 AI chat calls (more if revisions or a statement are needed).
"""

import json

from knowledge import ndb_law as L
from utils import prompts as P
from utils.llm import ask
from utils.retrieval import format_context, retrieve

MAX_REVISION_ROUNDS = 2

STEPS = {
    # step name: (label, law, task)
    "entity": ("Coverage: is the entity covered by the NDB scheme?", L.ENTITY_LAW, P.ENTITY_TASK),
    "element_1": ("Element 1: unauthorised access, disclosure or loss", L.ELEMENT_1_LAW, P.ELEMENT_1_TASK),
    "element_2": ("Element 2: likely serious harm (s 26WG)", L.ELEMENT_2_LAW, P.ELEMENT_2_TASK),
    "remedial": ("Exception: remedial action (s 26WF)", L.ELEMENT_3_LAW, P.REMEDIAL_TASK),
}


def _covered(entity_result):
    return entity_result.get("covered") in ("yes", "partly")


def rule_based_conclusion(r):
    """Boolean legal logic: coverage AND element 1 AND element 2 AND NOT remedial exception."""
    if r["entity"].get("covered") == "no":
        return "not covered by the NDB scheme"
    eligible = (
        _covered(r["entity"])
        and bool(r["element_1"].get("satisfied"))
        and bool(r["element_2"].get("satisfied"))
        and not bool(r["remedial"].get("satisfied"))
    )
    if eligible:
        return "eligible data breach"
    if r["entity"].get("covered") == "uncertain":
        return "uncertain - more facts needed"
    return "not an eligible data breach"


def _search_query(step, facts):
    """Builds the retrieval query from the step's task and the key facts."""
    keys = ["entity_type", "annual_turnover", "activities", "information_types", "what_happened",
            "who_accessed_or_received", "security_measures", "remedial_steps_taken"]
    fact_text = "; ".join(f"{k}: {facts.get(k)}" for k in keys if facts.get(k) not in (None, "", []))
    return f"{STEPS[step][0]}. {fact_text}"[:2000]


def _normalise(result):
    """Guards the boolean logic against answers like "false" (a string) instead of false."""
    value = result.get("satisfied")
    if isinstance(value, str):
        result["satisfied"] = value.strip().lower() in ("true", "yes", "1")
    if isinstance(result.get("covered"), str):
        result["covered"] = result["covered"].strip().lower()
    return result


def run_step(client, model, step, facts, feedback=None):
    """Retrieves OAIC guidance for the step, then makes one AI call."""
    label, law, task = STEPS[step]
    passages, method = retrieve(client, step, _search_query(step, facts))
    system = P._GROUNDING.format(
        law=law,
        guidance=format_context(passages),
        feedback=P.FEEDBACK_BLOCK.format(feedback=feedback) if feedback else "",
        task=task,
    )
    result = _normalise(ask(client, system, json.dumps(facts), as_json=True, model=model))
    result["_passages"] = passages
    result["_retrieval"] = method
    return result


def _public(r):
    """Strips internal keys before sending results back to the AI."""
    return {k: {kk: vv for kk, vv in v.items() if not kk.startswith("_")} for k, v in r.items()}


def run_assessment(client, incident, model, progress=lambda msg: None):
    out = {"model": model, "revisions": [], "reviews": []}

    progress("Step 1: extracting facts")
    facts = ask(client, P.EXTRACT_FACTS, incident, as_json=True, model=model)
    out["facts"] = facts

    results = {}
    for n, step in enumerate(STEPS, start=2):
        progress(f"Step {n}: {STEPS[step][0]}")
        results[step] = run_step(client, model, step, facts)

    # Reflection loop
    for round_no in range(1, MAX_REVISION_ROUNDS + 2):
        preliminary = rule_based_conclusion(results)
        progress(f"Review round {round_no}: senior reviewer checks the analysis")
        review = ask(client, P.REFLECTION, json.dumps({
            "facts": facts,
            "analysis": _public(results),
            "rule_based_conclusion": preliminary,
        }), as_json=True, model=model)
        review["_round"] = round_no
        review["_rule_based"] = preliminary
        out["reviews"].append(review)

        to_fix = [s for s in review.get("steps_to_revisit") or []
                  if isinstance(s, dict) and s.get("step") in STEPS]
        if not to_fix or round_no > MAX_REVISION_ROUNDS:
            break
        for item in to_fix:
            step = item["step"]
            progress(f"Revising {STEPS[step][0]} (reviewer feedback)")
            before = results[step]
            results[step] = run_step(client, model, step, facts, feedback=item.get("feedback", ""))
            out["revisions"].append({
                "round": round_no,
                "step": step,
                "label": STEPS[step][0],
                "feedback": item.get("feedback", ""),
                "before": {k: before.get(k) for k in ("satisfied", "covered", "confidence")},
                "after": {k: results[step].get(k) for k in ("satisfied", "covered", "confidence")},
            })

    final_review = out["reviews"][-1]
    rule_based = rule_based_conclusion(results)
    final = final_review.get("revised_conclusion")
    if final not in P.CONCLUSIONS:
        final = rule_based
    out.update(results=results, rule_based=rule_based, conclusion=final)

    progress("Drafting the advice memo")
    out["memo"] = ask(client, P.MEMO, json.dumps({
        "facts": facts,
        "analysis": _public(results),
        "review": {k: v for k, v in final_review.items() if not k.startswith("_")},
        "conclusion": final,
    }), model=model)

    out["statement"] = None
    if final == "eligible data breach":
        progress("Drafting the s 26WK statement to the Commissioner")
        passages, _ = retrieve(client, "statement", "contents of eligible data breach statement " + facts.get("what_happened", ""))
        system = P._GROUNDING.format(
            law="Privacy Act 1988 (Cth) s 26WK(3): the statement must set out (a) the identity and contact "
                "details of the entity; (b) a description of the eligible data breach; (c) the kind or kinds "
                "of information concerned; and (d) recommendations about the steps individuals should take.",
            guidance=format_context(passages),
            feedback="",
            task=P.STATEMENT_TASK,
        )
        out["statement"] = ask(client, system, json.dumps({"facts": facts, "analysis": _public(results)}), model=model)
        out["statement_passages"] = passages

    return out
