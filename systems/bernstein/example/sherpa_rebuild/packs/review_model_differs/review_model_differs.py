"""Check review_model_differs (dispatch): the reviewer model of a review task (--reviews) differs from the
model of every task it reviews.

params: reviewer_model=<model>;models=<seat>:<model>,<seat>:<model>
  models          the model each seat works with (Bernstein's role_model_policy)
  reviewer_model  the configured reviewer model (Bernstein's cross_model_verify.reviewer_model)
No reviewer_model: skipped (Bernstein picks a different model itself, nothing to refuse).
A reviewed task whose seat has no model in the table is not compared."""
import re

from sherpa.result import passed, red, skipped

COMMANDS = ("dispatch",)


def seat_models(text: str) -> dict[str, str]:
    """License prefix (as ppo makes it: BACKEND for backend) -> model."""
    pairs = (p.split(":", 1) for p in text.split(",") if ":" in p)
    return {re.sub(r"[^A-Z0-9]", "", seat.upper()): model.strip() for seat, model in pairs}


def run(sample, params):
    reviewer = params.get("reviewer_model", "").strip()
    reviewed = [t for t in (sample.options.get("reviews") or "").split(",") if t and t != "yes"]
    if not reviewer or not reviewed:
        return skipped("no reviewer_model set" if not reviewer else "not a review task (no --reviews)")
    models = seat_models(params.get("models", ""))
    tasks = (sample.parts.get("archive") or {}).get("tasks", {})
    same = [t for t in reviewed if t in tasks
            and models.get(str(tasks[t].get("assignee", "")).rsplit("-", 1)[0], "").lower() == reviewer.lower()]
    if same:
        return red("review_model_differs.same_model", f"reviewer model {reviewer} also wrote {', '.join(same)}",
                   "configure a different reviewer_model in the workflow file", same)
    return passed(*reviewed)
