"""The read-only commands. Each returns (exit code, text, data for --json)."""

from sherpa.result import KernelStop, exit_code, kernel_red
from sherpa.step01_policy_load import policy_load
from sherpa.step01_policy_load.tables import TABLES, role_allowed
from sherpa.step02_identity_read import identity_read
from sherpa.step02_identity_read.identity_read import ID
from sherpa.step03_flow_control.lookup import lookup
from sherpa.step03_flow_control.runnable import runnable
from sherpa.step03_flow_control.transition_check import actor_value
from sherpa.step04_sample_freeze import sample_freeze
from sherpa.step05_checks_run.runner import run_rows
from sherpa.step07_audit_trace import audit_trace
from sherpa.registry import registry
from sherpa.render.terminal import result_line



def failed(stop: KernelStop):
    r = stop.result
    return exit_code([r.error_code]), f"RED {r.error_code}  {r.reason}\n  -> {r.fix}", \
        {"ok": False, "error_code": r.error_code, "reason": r.reason, "fix": r.fix}


def table_text(rows, columns) -> str:
    rows = [columns] + [[str(r.get(c, "")) for c in columns] for r in rows]
    widths = [max(len(r[i]) for r in rows) for i in range(len(columns))]
    return "\n".join("  ".join(cell.ljust(w) for cell, w in zip(r, widths)).rstrip() for r in rows)


def config(args, ws):
    policy = policy_load.run(ws)
    only = args.options.get("for")
    out, data, problems = [], {}, []
    for table, shape in TABLES.items():
        rows = {"flow": policy.flow.values(), "checks": policy.checks, "outputs": policy.outputs,
                "roles": policy.roles.values(), "plugins": policy.plugins.values()}[table]
        if only:
            rows = [r for r in rows if r.get("command") in (only, "*")
                    or r.get("event", "").rpartition(".")[0] in (only, "any")] if table in ("flow", "checks", "outputs") else rows
        rows = [dict(r, pack=r["_from"]) for r in rows]
        if table == "plugins":
            for r in rows:
                r["resolved"] = resolved(policy, r)
        if table == "checks":
            for r in rows:
                if r["command"] != "*":
                    try:
                        registry.load(policy, r["check"], "check", r["command"])
                    except KernelStop as stop:
                        problems.append(f"{stop.result.error_code}: {stop.result.reason}")
        columns = list(shape.columns) + ["pack"] + (["resolved"] if table == "plugins" else [])
        out.append(f"# {shape.file}\n{table_text(rows, columns)}")
        data[table] = [{c: r[c] for c in columns} for r in rows]
    head = (f"policy {policy.policy_pack}  (packs: {' -> '.join(policy.packs)})  hash {policy.policy_pack_hash}\n"
            "kernel floor, always run in step 6: caller_identified, transition_is_in_flow_table")
    tail = [f"warn {w.error_code}  {w.reason}" for w in policy.warnings] + [f"RED {p}" for p in problems]
    data.update(policy_pack=policy.policy_pack, packs=list(policy.packs), states=sorted(policy.states),
                warnings=[w.error_code for w in policy.warnings], problems=problems)
    return (1 if problems else 0), "\n\n".join([head, *out, *tail]), data


def resolved(policy, row) -> str:
    impl = row["impl"]
    try:
        if impl.startswith("exec:"):
            return str(registry.find_file(policy, row["name"], impl[5:]))
        if impl.endswith(".py"):
            return str(registry.find_file(policy, row["name"], impl))
        return getattr(registry.module_of(policy, row["name"]), "__file__", impl)
    except KernelStop as stop:
        return f"MISSING ({stop.result.error_code})"


def whoami(args, ws):
    policy = policy_load.run(ws)
    caller = identity_read.run(args, policy)
    return 0, f"{caller.inst}  role {caller.role}", {"inst": caller.inst, "role": caller.role}


def on_object(policy, ws, caller, args, folder: str, ident: str) -> tuple:
    """(state, commands the caller can run now, is the caller a party) for one object: the state
    from the kernel's own file, the parties from the samplers its rows' actor paths name."""
    rows = [r for r in policy.flow.values() if r["object"] == folder]
    request = sample_freeze.request_of(ws, caller, rows[0], args, ident)
    actors = {r["actor"] for r in rows if r["actor"] != "-"}
    parts, _, _ = sample_freeze.take(policy, request, {a.split(".", 1)[0] for a in actors})
    who = {a: actor_value(a, parts) for a in actors}
    commands = [c for c in runnable(policy, caller.role, request.state)
                if policy.flow[c]["object"] in ("-", folder)
                and who.get(policy.flow[c]["actor"], caller.inst) == caller.inst]
    return request.state, commands, caller.inst in who.values()


def next_(args, ws):
    policy = policy_load.run(ws)
    caller = identity_read.run(args, policy)
    task = sample_freeze.task_id(args)
    repo = ws.governance_repo
    folders = sorted({r["object"] for r in policy.flow.values() if r["object"] != "-"})
    if task:
        found = [f for f in folders if (repo / f / task).is_dir()]
        state, commands, _ = on_object(policy, ws, caller, args, found[0], task) if found else ("-", [])
        return 0, f"{task} is {state}; {caller.inst} can run: {', '.join(commands) or 'nothing now'}", \
            {"task": task, "state": state, "commands": commands}
    fresh = [c for c in runnable(policy, caller.role, "-") if policy.flow[c]["from"] == "-"]
    mine = {}
    for folder in folders:
        for state_file in sorted((repo / folder).glob("*/state.json")):
            state, commands, party = on_object(policy, ws, caller, args, folder, state_file.parent.name)
            if party:
                mine[state_file.parent.name] = {"state": state, "commands": commands}
    lines = [f"{caller.inst} ({caller.role})"]
    lines += [f"  {t}  {m['state']:10s} {', '.join(m['commands']) or '(nothing for you now)'}"
              f"   e.g. sherpa {m['commands'][0]} --task {t}" if m["commands"] else
              f"  {t}  {m['state']:10s} (nothing for you now)" for t, m in mine.items()]
    if fresh:
        lines.append(f"  new: {', '.join(fresh)}")
    return 0, "\n".join(lines), {"inst": caller.inst, "role": caller.role, "tasks": mine, "new": fresh}


def sample_(args, ws):
    if not args.positionals:
        return 1, "usage: sherpa sample <command> [--inst ..] [--task ..]", {"ok": False}
    policy = policy_load.run(ws)
    caller = identity_read.run(args, policy)
    row = lookup(policy, args.positionals[0])
    plain = sample_freeze.to_plain(sample_freeze.run(ws, policy, caller, row, args))
    import json
    return 0, json.dumps(plain, ensure_ascii=False, indent=1), plain


def check(args, ws):
    if len(args.positionals) < 2:
        return 1, "usage: sherpa check <check> <command> [--inst ..] [--task ..]", {"ok": False}
    name, command = args.positionals[:2]
    policy = policy_load.run(ws)
    caller = identity_read.run(args, policy)
    flow_row = lookup(policy, command)
    sample = sample_freeze.run(ws, policy, caller, flow_row, args)
    if name not in policy.plugins:
        return 1, f"no plugin named {name} in plugins.tsv", {"ok": False}
    rows = [r for r in policy.checks if r["check"] == name and r["command"] in (command, "*")] or \
        [{"command": command, "check": name, "roles": "*", "stage": "general", "action": "block", "params": "-"}]
    result = run_rows(policy, rows[:1], sample)[0]
    text = result_line(result).strip()
    if not role_allowed(rows[0], caller.role):
        text += (f"\n  (this row is for roles {rows[0]['roles']}; {caller.role} is not one of them, "
                 f"so {command} would not run it)")
    return (1 if result.blocks else 0), text, sample_freeze.to_plain(result)


def audit(args, ws):
    for name in ("inst", "task"):
        value = args.options.get(name, "")
        if value and not ID.fullmatch(value):
            return 1, f"--{name} {value!r} is not an id", {"ok": False}
    policy = policy_load.run(ws)
    writer = audit_trace.audit_writer(policy)
    if writer is None or not hasattr(writer, "read"):
        return 1, "this policy pack's audit_writer cannot be read back", {"ok": False}
    rows = writer.read(str(ws.governance_repo), args.options.get("inst", ""), args.options.get("task", ""))
    text = "\n".join(f"{r['ts']}  {r['inst']:8s} {r['command']:9s} {r['task'] or '-':12s} "
                     f"{r['status']:4s} {r['check']:22s} {r['error_code']}" for r in rows)
    return 0, text or "(no audit rows)", rows


def help_(args, ws):
    from sherpa.kernel import USAGE
    try:
        policy = policy_load.run(ws)
    except KernelStop as stop:
        return 0, USAGE + f"\n(policy pack failed to load: {stop.result.error_code})", {"usage": USAGE}
    rows = [dict(r) for r in policy.flow.values()]
    text = USAGE + f"\nflow commands of policy pack {policy.policy_pack}:\n" + \
        table_text(rows, ["command", "roles", "actor", "from", "to", "body"])
    return 0, text, {"usage": USAGE, "flow": [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]}


HANDLERS = {"help": help_, "config": config, "next": next_, "whoami": whoami, "sample": sample_,
            "check": check, "audit": audit}


def run(name, args, ws):
    try:
        return HANDLERS[name](args, ws)
    except KernelStop as stop:
        return failed(stop)
    except Exception as err:
        return failed(KernelStop(kernel_red("query", "kernel.crashed", f"{type(err).__name__}: {err}",
                                            "report this as a kernel bug")))
