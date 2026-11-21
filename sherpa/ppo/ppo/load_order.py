"""The order packs stack in, as LOOT sorts plugins.

  1 hard rules: requires (the required pack first), after (a listed pack that is on goes first).
    A missing or wrong-version requirement, a declared conflict or a hard cycle is a problem.
  2 soft rules: layer order base -> classic_lifecycle -> classic_lifecycle_pack -> custom_lifecycle.
    A soft rule that would close a cycle with the rules already in is dropped (and reported).
  3 tie-break: among packs free to go next, the one listed first in load_order.toml.
Also: exactly one custom lifecycle is on (human ruling 2026-11-03: "只允许一个"); none only when
nothing but base packs is on.

Same input, same order: the order decides which row wins, so it may never wobble.
"""
from dataclasses import dataclass, field

from ppo import Problem
from ppo.pack_library import GROUPS


@dataclass
class Order:
    names: list                                   # base first
    before: dict = field(default_factory=dict)    # pack -> {earlier pack: why}
    dropped: list = field(default_factory=list)   # soft rules left out to avoid a cycle
    problems: list = field(default_factory=list)


def reaches(edges: dict, start: str, goal: str) -> bool:
    seen, todo = set(), [start]
    while todo:
        node = todo.pop()
        if node == goal:
            return True
        if node not in seen:
            seen.add(node)
            todo += list(edges.get(node, ()))
    return False


def hard_rules(decls: dict) -> tuple:
    """(edges earlier -> {later: why}, problems)."""
    edges, problems = {n: {} for n in decls}, []
    for name, decl in decls.items():
        for req in decl.requires:
            if req.name not in decls:
                problems.append(Problem("policy.missing_requirement", f"{name} requires {req}, which is not on",
                                        f"`ppo enable {req.name}`, or disable {name}", (name, req.name)))
            elif not req.met_by(decls[req.name].version):
                problems.append(Problem("policy.missing_requirement",
                                        f"{name} requires {req}; {req.name} {decls[req.name].version} is installed",
                                        f"install a {req.name} that meets it, or disable {name}", (name, req.name)))
            else:
                edges[req.name][name] = "requires"
        for other in decl.after:
            if other in decls:
                edges[other].setdefault(name, "after")
        for req in decl.conflicts:
            if req.name in decls and req.met_by(decls[req.name].version):
                problems.append(Problem("policy.declared_conflict", f"{name} declares it conflicts with {req}",
                                        f"disable {name} or {req.name}", (name, req.name)))
    return edges, problems


def one_custom_lifecycle(decls: dict) -> list:
    """Exactly one workflow; none only when nothing but base packs is on (contract 2.6, no_guarantees)."""
    on = sorted(n for n, d in decls.items() if d.group == "custom_lifecycle")
    if len(on) == 1 or not on and all(d.group == "base" for d in decls.values()):
        return []
    # ponytail: placeholder code name, to be named by the human with the other ppo codes
    return [Problem("policy.custom_lifecycle_count",
                    f"{len(on)} custom lifecycles are on ({', '.join(on) or 'none'}); exactly one may be",
                    "`ppo enable <workflow>` (it takes the place of the one that is on)", tuple(on))]


def resolve(decls: dict, preferred) -> Order:
    position = {n: i for i, n in enumerate(preferred)}
    ranked = sorted(decls, key=lambda n: (position.get(n, len(position)), n))
    edges, problems = hard_rules(decls)
    problems += one_custom_lifecycle(decls)
    looped = sorted(n for n in edges if any(reaches(edges, later, n) for later in edges[n]))
    if looped:
        problems.append(Problem("policy.requirement_cycle", f"requires / after loop through: {', '.join(looped)}",
                                "break the loop in one of their policy_pack.toml", tuple(looped)))
    order = Order([], problems=problems)
    if looped:
        return order
    rank = {n: GROUPS.index(decls[n].group) for n in decls}
    for later in ranked:
        for earlier in ranked:
            if rank[earlier] < rank[later] and later not in edges[earlier]:
                if reaches(edges, later, earlier):
                    order.dropped.append((earlier, later))
                else:
                    edges[earlier][later] = f"layer {decls[earlier].group} before {decls[later].group}"
    waiting = {n: {e for e in edges if n in edges[e]} for n in decls}
    order.before = {n: {e: edges[e][n] for e in waiting[n]} for n in decls}
    while waiting:
        nxt = next(n for n in ranked if n in waiting and not waiting[n])
        order.names.append(nxt)
        del waiting[nxt]
        for rest in waiting.values():
            rest.discard(nxt)
    return order
