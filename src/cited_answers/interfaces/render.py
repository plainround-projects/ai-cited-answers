"""Plain-text rendering of the retrieval and answer reports."""

from __future__ import annotations

from cited_answers.application.evaluate import AnswerReport, RetrievalReport
from cited_answers.application.retrieve import IngestReport, Mode
from cited_answers.domain.evaluation import Rate, Stage


def render_ingest(report: IngestReport) -> str:
    """One line: pages and chunks indexed, retired pages skipped by id."""
    skipped = ", ".join(report.skipped_retired) or "none"
    return (
        f"indexed {report.pages_indexed} current pages as {report.chunks} chunks; "
        f"skipped {len(report.skipped_retired)} retired pages: {skipped}"
    )


def render_retrieval(report: RetrievalReport) -> str:
    """Hit rate at five per question type and retrieval mode, each with its Wilson interval."""
    lines = ["--- hit rate at 5: a chunk of the gold page is among the top five ---"]
    types = sorted({kind for kind, _ in report.rates})
    for kind in types:
        for mode in Mode:
            rate = report.rates[(kind, mode.value)]
            missed = report.misses.get((kind, mode.value), [])
            tail = f"   missed: {', '.join(missed)}" if missed else ""
            lines.append(f"{kind:<10} {mode.value:<8} {rate}{tail}")
    return "\n".join(lines)


def _rate(label: str, rate: Rate) -> str:
    return f"{label:<34} {rate}"


def render_answers(title: str, report: AnswerReport, threshold: float, agreement: tuple[int, int] | None) -> str:
    """The answer report: retrieval and answer correctness as two numbers, refusals, the stage table and the cost."""
    lines = [
        f"== {title} (refusal threshold {threshold}) ==",
        _rate("retrieval hit rate (answerable+exact)", report.retrieval_hit),
        _rate("answer correct (judge)", report.answer_correct),
        _rate("unanswerable refused", report.unanswerable_refused),
        _rate("answerable wrongly refused", report.false_refusals),
    ]
    slips = report.unanswered_slips
    lines.append(
        "every unanswerable question was refused."
        if not slips
        else f"NOT every unanswerable question was refused; answered: {', '.join(slips)}"
    )
    lines += [
        "misses by stage:",
        f"  retrieval misses:  {report.misses_by_stage[Stage.RETRIEVAL]}",
        f"  generation misses: {report.misses_by_stage[Stage.GENERATION]}",
    ]
    if agreement is not None:
        lines.append(
            f"judge agreement with hand grades: {agreement[0]}/{agreement[1]} = {agreement[0] / agreement[1]:.0%}"
        )
    lines.append(f"tokens: {report.input_tokens} in, {report.output_tokens} out")
    return "\n".join(lines)
