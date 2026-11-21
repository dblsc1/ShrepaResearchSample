"""Check lower_seat_pairing (dispatch): an upper dispatches only to its own lower seat.

ppo writes the params from the workflow file: pairs=<upper role>><lower license prefix>,...
one pair per [[instance]]. The caller's role and the --to license's prefix must make one of them."""
from sherpa.result import passed, red

COMMANDS = ("dispatch",)


def run(sample, params):
    pairs = {p for p in params.get("pairs", "").split(",") if p}
    to = sample.options.get("to") or ""
    if not to or to == "yes":
        return passed()                      # task_card_complete reds a missing --to
    pair = f"{sample.caller.role}>{to.split('-', 1)[0]}"
    if pair in pairs:
        return passed(to)
    yours = sorted(p.split(">", 1)[1] for p in pairs if p.startswith(f"{sample.caller.role}>"))
    return red("classic_lifecycle.not_your_lower", f"{sample.caller.role} may not dispatch to {to}",
               f"dispatch to a license of your lower seat ({', '.join(yours) or 'you have none'}-<n>)", [to])
