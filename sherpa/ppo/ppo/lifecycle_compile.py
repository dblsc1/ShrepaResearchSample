"""Compile the one custom lifecycle (the workflow file) into flat table rows (spec section 5).

  [[instance]] id, lifecycle, upper, lower    one use of a lifecycle unit: upper dispatches to lower
  [seat.<seat>] card, class                    the seat's role card, relative to the workflow's folder; class is a
                                               name several seats share (placeholder key name, for the human to name)
  [policy.<pack>] only | except, params        whom a pack's checks and outputs run for; a class name there stands
                                               for every seat of the class

What comes out:
  roles.tsv    one row per seat: role = seat, prefix made from the seat's name (a role a lower pack
               already has, like base's human, keeps its prefix), superior = the upper of the instance
               the seat is the lower of, card = <workflow>/<card> (built cards, like impl, are made relative to policypack/)
  roles column '@upper' / '@lower' in any table become every seat that is an upper / a lower;
               a [policy.<pack>] fills the roles column of that pack's checks and outputs rows
  pairing      one checks row: dispatch may only go from an instance's upper to its lower
               (params pairs=<upper role>><lower prefix>,...; the check is classic_lifecycle's)

A seat class is resolved here and nowhere else: in only / except a class becomes its seats, and a params item
keyed by a class becomes one item per seat (an item keyed by the seat itself wins). The tables that come out name
seats only, so the kernel and the packs see no classes; a workflow without classes compiles to the same bytes.

A seat is the lower of at most one instance, so who answers to whom is a tree.
No counts anywhere: a seat holds any number of agents.
"""
import re
import tomllib

from ppo import Problem
from ppo.policy_tables import split_list

CODE = "policy.bad_custom_lifecycle"     # ponytail: placeholder code name, for the human to name
PAIRING_CHECK = "lower_seat_pairing"     # placeholder name, registered by classic_lifecycle
LIFECYCLE_GROUP = "classic_lifecycle"
SEAT = re.compile(r"[a-z][a-z0-9_]*")


def bad(name, why, fix):
    return Problem(CODE, f"custom lifecycle {name}: {why}", fix, (name,))


def make_prefix(seat: str) -> str:
    """worker -> WORKER, general1_worker1 -> GENERAL1WORKER1: the license id is <prefix>-<n>."""
    return re.sub(r"[^A-Z0-9]", "", seat.upper())


def class_params(params: str, classes: dict) -> str:
    """A params item keyed by a class stands for one item per seat of the class; a seat's own item wins."""
    items = [p for p in params.split(";") if p]
    own = {p.split("=", 1)[0] for p in items}
    out = []
    for item in items:
        key, eq, value = item.partition("=")
        out += [f"{seat}{eq}{value}" for seat in classes[key] if seat not in own] if key in classes else [item]
    return ";".join(out)


def read_workflow(decl) -> tuple:
    path = decl.folder / f"{decl.name}.toml"
    if not path.is_file():
        return None, [bad(decl.name, f"{path.name} is missing", f"write {path} (the workflow file has the folder's name)")]
    try:
        return tomllib.loads(path.read_text(encoding="utf-8")), []
    except tomllib.TOMLDecodeError as err:
        return None, [bad(decl.name, f"{path.name}: {err}", f"fix {path}")]


def shape_problems(name, data) -> list:
    """The workflow file's value types, before anything reads them."""
    out = []
    strings = lambda v: isinstance(v, list) and all(isinstance(x, str) for x in v)
    if not isinstance(data.get("instance", []), list) or not all(isinstance(i, dict) for i in data.get("instance", [])):
        out.append(bad(name, "instance is not a list of tables", "write each one as [[instance]]"))
    for key in ("seat", "policy"):
        if not isinstance(data.get(key, {}), dict) or not all(isinstance(v, dict) for v in data.get(key, {}).values()):
            out.append(bad(name, f"{key} is not a set of [{key}.<name>] tables", f"write [{key}.<name>] sections"))
    if out:
        return out
    for seat, cfg in data.get("seat", {}).items():
        if not isinstance(cfg.get("card", ""), str):
            out.append(bad(name, f"[seat.{seat}] card is not a string", 'card = "cards/<seat>.md"'))
        if not isinstance(cfg.get("class", ""), str):
            out.append(bad(name, f"[seat.{seat}] class is not a string", 'class = "<name several seats share>"'))
    for pack, cfg in data.get("policy", {}).items():
        for key in ("only", "except"):
            if key in cfg and not strings(cfg[key]):
                out.append(bad(name, f"[policy.{pack}] {key} is not a list of seat names", f'{key} = ["seat", ...]'))
        if not isinstance(cfg.get("params", ""), str):
            out.append(bad(name, f"[policy.{pack}] params is not a string", 'params = "n=1;x=y"'))
    return out


def compile_lifecycle(stacked, decls: dict) -> list:
    """Adds the workflow's rows to stacked.tables in place; returns the problems (nothing added then)."""
    custom = [d for d in decls.values() if d.group == "custom_lifecycle"]
    if len(custom) != 1:
        return []                                   # load_order already reported the count
    decl = custom[0]
    data, problems = read_workflow(decl)
    if data is None:
        return problems
    name = decl.name
    problems = shape_problems(name, data)
    if problems:
        return problems
    instances = data.get("instance", [])
    seats_cfg, policies = data.get("seat", {}), data.get("policy", {})
    if not instances:
        problems.append(bad(name, "no [[instance]]", "add one: id, lifecycle, upper, lower"))
    upper_of, uppers, lowers, ids, pairs = {}, [], [], set(), []
    for n, inst in enumerate(instances, 1):
        where = f"instance {inst.get('id', n)}"
        missing = [k for k in ("id", "lifecycle", "upper", "lower") if not isinstance(inst.get(k), str)]
        if missing:
            problems.append(bad(name, f"{where} lacks {', '.join(missing)}", "write id, lifecycle, upper, lower"))
            continue
        if inst["id"] in ids:
            problems.append(bad(name, f"two instances have id {inst['id']}", "give each instance its own id"))
        ids.add(inst["id"])
        lifecycle = decls.get(inst["lifecycle"])
        if lifecycle is None or lifecycle.group != LIFECYCLE_GROUP:
            problems.append(bad(name, f"{where}: lifecycle {inst['lifecycle']!r} is not an enabled lifecycle pack",
                                f"`ppo enable {inst['lifecycle']}`, or name an enabled {LIFECYCLE_GROUP} pack"))
        for seat in (inst["upper"], inst["lower"]):
            if not SEAT.fullmatch(seat):
                problems.append(bad(name, f"{where}: seat {seat!r}", "a seat name is lowercase letters, digits and _"))
        if inst["upper"] == inst["lower"]:
            problems.append(bad(name, f"{where}: {inst['upper']} is its own upper", "upper and lower are two seats"))
        if inst["lower"] in upper_of:
            problems.append(bad(name, f"{where}: {inst['lower']} is already the lower of {upper_of[inst['lower']]}",
                                "a seat is the lower of one instance at most (who answers to whom is a tree)"))
        upper_of[inst["lower"]] = inst["upper"]
        uppers += [inst["upper"]] if inst["upper"] not in uppers else []
        lowers += [inst["lower"]] if inst["lower"] not in lowers else []
        pairs.append((inst["upper"], inst["lower"]))
    seats = uppers + [s for s in lowers if s not in uppers]
    for seat in seats:                              # a superior loop would be no tree either
        seen, up = {seat}, upper_of.get(seat)
        while up is not None and up not in seen:
            seen.add(up)
            up = upper_of.get(up)
        if up is not None:
            problems.append(bad(name, f"seat {seat} answers to itself through {', '.join(sorted(seen))}",
                                "break the loop: some seat must have no upper"))
            break
    for seat, cfg in seats_cfg.items():
        if seat not in seats:
            problems.append(bad(name, f"[seat.{seat}] is in no instance", f"add {seat} to an instance, or drop it"))
        elif cfg.get("card") and not (decl.folder / cfg["card"]).is_file():
            problems.append(bad(name, f"[seat.{seat}] card {cfg['card']} is not in {decl.folder.name}/",
                                "put the card there, or fix the path"))
    roles_table = stacked.tables["roles"]
    rows = {}
    for seat in seats:
        old = roles_table.get((seat,))
        card = seats_cfg.get(seat, {}).get("card")
        rows[seat] = {"role": seat, "prefix": old["prefix"] if old else make_prefix(seat),
                      "superior": upper_of.get(seat, "-"), "card": card or "-",
                      "_from": name, "_line": 0}
        if not card and old and old["card"] != "-":     # a role restated without a card keeps its own
            rows[seat].update(card=old["card"], _card_from=old.get("_card_from", old["_from"]))
    taken = {}
    for role, row in {**{k[0]: r for k, r in roles_table.items()}, **rows}.items():
        if row["prefix"] in taken:
            problems.append(bad(name, f"seats {taken[row['prefix']]} and {role} both get license prefix {row['prefix']}",
                                "rename one seat (the prefix is made from the seat's name)"))
        taken[row["prefix"]] = role
    all_roles = list(dict.fromkeys([k[0] for k in roles_table] + seats))
    classes = {}                                    # class -> its seats, in the order the [seat.*] sections stand
    for seat, cfg in seats_cfg.items():
        if cfg.get("class"):
            classes.setdefault(cfg["class"], []).append(seat)
    for cls in classes:
        if not SEAT.fullmatch(cls):
            problems.append(bad(name, f"seat class {cls!r}", "a class name is lowercase letters, digits and _"))
        if cls in all_roles:
            problems.append(bad(name, f"class {cls} has the name of a seat", "give the class a name no seat has"))
    with_seats = lambda names: [s for n in names for s in classes.get(n, [n])]
    for pack, cfg in policies.items():
        if pack not in decls:
            problems.append(bad(name, f"[policy.{pack}]: {pack} is not enabled", f"`ppo enable {pack}`, or drop the section"))
        if "only" in cfg and "except" in cfg:
            problems.append(bad(name, f"[policy.{pack}] has both only and except", "keep one"))
        unknown = [s for s in with_seats(cfg.get("only", []) + cfg.get("except", [])) if s not in all_roles]
        if unknown:
            problems.append(bad(name, f"[policy.{pack}] names {', '.join(unknown)}, which are no seats",
                                f"seats are {', '.join(all_roles)}"))
    if problems:
        return problems

    for seat, row in rows.items():
        roles_table[(seat,)] = row
    filled = {"@upper": uppers, "@lower": lowers}
    for table in ("flow", "checks", "outputs"):
        for row in stacked.tables[table].values():
            names = split_list(row["roles"])
            if any(n in filled for n in names):
                out = [s for n in names for s in (filled.get(n) or [n])]
                row["roles"] = ",".join(dict.fromkeys(out)) or "-"
    for pack, cfg in policies.items():
        for table in ("checks", "outputs"):
            for row in stacked.tables[table].values():
                if row["_from"] != pack:
                    continue
                if "only" in cfg:                   # locked rows too: locked only stops another pack replacing a row
                                                     # (human 11-03: every policy is (time points) x (seats))
                    chosen = with_seats(cfg["only"])
                elif "except" in cfg:
                    chosen = [r for r in all_roles if r not in with_seats(cfg["except"])]
                else:
                    chosen = None
                if chosen is not None:
                    had = split_list(row["roles"])
                    keep = chosen if "*" in had else [r for r in chosen if r in had]
                    row["roles"] = ",".join(keep) or "-"
                if cfg.get("params"):
                    merged = dict(p.split("=", 1) if "=" in p else (p, "yes")
                                  for p in (row["params"].split(";") if row["params"] != "-" else []))
                    given = class_params(cfg["params"], classes) if classes else cfg["params"]
                    merged.update(p.split("=", 1) if "=" in p else (p, "yes") for p in given.split(";") if p)
                    row["params"] = ";".join(f"{k}={v}" for k, v in merged.items())
    if any(k[0] == "dispatch" for k in stacked.tables["flow"]):
        stacked.tables["checks"][("dispatch", PAIRING_CHECK)] = {
            "command": "dispatch", "check": PAIRING_CHECK, "roles": "*", "stage": "general", "action": "block",
            "params": "pairs=" + ",".join(f"{u}>{rows[l]['prefix']}" for u, l in pairs), "locked": "yes",
            "_from": name, "_line": 0}
    return []
