"""ppo's command line. The workspace is <project>/sherpa/; ppo looks for it from the current folder
upward (sherpa/policypack/load_order.toml), or takes --home <project>.

  ppo init [--packs a,b,...]          install packs into sherpa/policypack/, write load_order.toml, build
  ppo build | ppo check               build sherpa/policy/ | only check, write nothing
  ppo list | ppo order                what is on, and in what order (and why)
  ppo enable <pack> | ppo disable <pack> | ppo packorderchange <pack> <position>
                                      change load_order.toml and build; on a problem, change it back
  ppo new <pack>                      a new pack's skeleton in sherpa/policypack/<pack>/ (not enabled yet)

Exit code: 0 done, 2 a problem with the packs (nothing was written).
Every command that changes sherpa/policypack/ or sherpa/policy/ holds the governance lock throughout:
the kernel reads both under a shared lock, so it never sees a pack half-installed.
"""
import argparse
import shutil
import sys
from pathlib import Path

from ppo import PpoError, Problem
from ppo.governance_lock import governance_lock
from ppo.pack_library import (LOAD_ORDER, NAME, declarations, install, library_folders, read_load_order,
                              write_load_order)
from ppo.pack_skeleton import write_skeleton
from ppo.policy_build import plan, write

WORKSPACE = "sherpa"


def default_packs() -> list:
    """base, the classic unit, every classic pack, and the first workflow."""
    names = list(library_folders())
    custom = [n for n in names if (library_folders()[n].parent.name == "custom_lifecycle")]
    return [n for n in names if n not in custom] + custom[:1]


def find_repo(home) -> Path:
    if home:
        return Path(home).resolve() / WORKSPACE
    for folder in (Path.cwd(), *Path.cwd().parents):
        if (folder / WORKSPACE / "policypack" / LOAD_ORDER).is_file():
            return folder / WORKSPACE
    raise PpoError(Problem("policy.not_built", f"no {WORKSPACE}/policypack/{LOAD_ORDER} here or above {Path.cwd()}",
                           "run `ppo init` in the project's root, or pass --home <project>"))


def show(the_plan, out):
    for note in the_plan.stacked.notes if the_plan.stacked else ():
        print(f"note {note}", file=out)
    for table, key, winner, loser in the_plan.stacked.overrides if the_plan.stacked else ():
        print(f"override {table} {key}: {winner} replaces {loser}", file=out)
    for w in the_plan.stacked.warnings if the_plan.stacked else ():
        print(f"WARN {w.code}  {w.reason}\n  -> {w.fix}", file=out)


def build(repo: Path, check_only=False) -> str:
    the_plan = plan(repo / "policypack")
    if the_plan.problems:
        raise PpoError(*the_plan.problems)
    show(the_plan, sys.stdout)
    if check_only:
        return f"check passed: {len(the_plan.order.names)} packs, {', '.join(the_plan.order.names)}"
    name, written = write(repo, the_plan)
    return f"built {repo / 'policy' / name}.lock" if written else f"up to date: {name}.lock"


def with_order(repo: Path, packs, installed=()):
    """Write the new load order and build; on any problem put the old order back."""
    policypack = repo / "policypack"
    old = read_load_order(policypack)
    write_load_order(policypack, packs)
    try:
        return build(repo)
    except Exception:
        write_load_order(policypack, old)
        for name in installed:
            shutil.rmtree(policypack / name, ignore_errors=True)
        raise


def cmd_init(args):
    repo = Path(args.home or Path.cwd()).resolve() / WORKSPACE
    policypack = repo / "policypack"
    if (policypack / LOAD_ORDER).is_file():
        raise PpoError(Problem("policy.already_installed", f"{policypack / LOAD_ORDER} exists",
                               "use `ppo enable` / `ppo disable` / `ppo build`"))
    packs = [p for p in args.packs.split(",") if p] if args.packs else default_packs()
    with governance_lock(repo):
        policypack.mkdir(parents=True, exist_ok=True)
        installed = [n for n in packs if install(policypack, n)]
        write_load_order(policypack, packs)
        try:
            return build(repo)
        except Exception:
            (policypack / LOAD_ORDER).unlink(missing_ok=True)
            for name in installed:
                shutil.rmtree(policypack / name, ignore_errors=True)
            raise


def cmd_enable(args):
    repo = find_repo(args.home)
    with governance_lock(repo):
        return enable(repo, args)


def enable(repo, args):
    packs = list(read_load_order(repo / "policypack"))
    if args.pack in packs:
        return f"{args.pack} is on already"
    installed = [args.pack] if install(repo / "policypack", args.pack) else []
    try:
        group = declarations(repo / "policypack", [args.pack])[args.pack].group
    except PpoError:
        for name in installed:
            shutil.rmtree(repo / "policypack" / name, ignore_errors=True)
        raise
    if group == "custom_lifecycle":             # one workflow at a time: the new one takes the old one's place
        packs = [p for p in packs if declarations(repo / "policypack", [p])[p].group != "custom_lifecycle"]
    return with_order(repo, packs + [args.pack], installed)


def cmd_disable(args):
    repo = find_repo(args.home)
    with governance_lock(repo):
        packs = list(read_load_order(repo / "policypack"))
        if args.pack not in packs:
            return f"{args.pack} is off already"
        return with_order(repo, [p for p in packs if p != args.pack])


def cmd_packorderchange(args):
    repo = find_repo(args.home)
    with governance_lock(repo):
        packs = list(read_load_order(repo / "policypack"))
        if args.pack not in packs:
            raise PpoError(Problem("policy.unknown_pack", f"{args.pack} is not on", f"`ppo enable {args.pack}` first"))
        packs.remove(args.pack)
        packs.insert(max(0, args.position - 1), args.pack)
        return with_order(repo, packs)


def cmd_build(args):
    repo = find_repo(args.home)
    with governance_lock(repo):
        return build(repo)


def cmd_list(args):
    repo = find_repo(args.home)
    policypack = repo / "policypack"
    on = read_load_order(policypack)
    decls = declarations(policypack, on)
    lines = [f"on   {n:28} {decls[n].group:24} v{decls[n].version}" for n in on]
    off = sorted(p.name for p in policypack.iterdir() if p.is_dir() and p.name not in on and p.name != "__pycache__")
    lines += [f"off  {n}" for n in off]
    return "\n".join(lines)


def cmd_order(args):
    the_plan = plan(find_repo(args.home) / "policypack")
    lines = []
    for i, name in enumerate(the_plan.order.names, 1):
        why = "; ".join(f"after {e} ({w})" for e, w in sorted(the_plan.order.before.get(name, {}).items()))
        lines.append(f"{i:3} {name}" + (f"   {why}" if why else ""))
    lines += [f"    dropped soft rule {a} before {b}: it would close a loop" for a, b in the_plan.order.dropped]
    if the_plan.problems:
        raise PpoError(*the_plan.problems)
    return "\n".join(lines)


def cmd_new(args):
    repo = find_repo(args.home)
    folder = repo / "policypack" / args.pack
    if not NAME.fullmatch(args.pack) or folder.exists() or args.pack in library_folders():
        raise PpoError(Problem("policy.bad_manifest", f"{args.pack!r}: taken, or not letters, digits and _",
                               "pick another name (it is the folder's name and the pack's)"))
    with governance_lock(repo):
        write_skeleton(folder, args.pack)
    return (f"new pack {folder}: edit {args.pack}_check.py, checks.tsv and the two cases in cases/, "
            f"then `ppo enable {args.pack}`")


def parser():
    top = argparse.ArgumentParser(prog="ppo", description="policy pack organizer: builds sherpa/policy/")
    top.add_argument("--home", help="the project's root (default: found from the current folder up)")
    sub = top.add_subparsers(dest="command", required=True)
    p = sub.add_parser("init")
    p.add_argument("--packs", help="comma-separated pack names (default: the whole library, first workflow)")
    p.set_defaults(run=cmd_init)
    sub.add_parser("build").set_defaults(run=cmd_build)
    sub.add_parser("check").set_defaults(run=lambda a: build(find_repo(a.home), check_only=True))
    sub.add_parser("list").set_defaults(run=cmd_list)
    sub.add_parser("order").set_defaults(run=cmd_order)
    for name, run in (("enable", cmd_enable), ("disable", cmd_disable)):
        p = sub.add_parser(name)
        p.add_argument("pack")
        p.set_defaults(run=run)
    p = sub.add_parser("new")
    p.add_argument("pack")
    p.set_defaults(run=cmd_new)
    p = sub.add_parser("packorderchange")
    p.add_argument("pack")
    p.add_argument("position", type=int, help="1 = first in load_order.toml")
    p.set_defaults(run=cmd_packorderchange)
    return top


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        print(args.run(args))
        return 0
    except PpoError as err:
        for problem in err.problems:
            print(problem.text(), file=sys.stderr)
        return 2
    except (OSError, ValueError, TypeError, KeyError) as err:    # ponytail: a bug or a broken file, said plainly
        print(f"RED ppo.crashed  {type(err).__name__}: {err}\n  -> nothing was kept; report it with the command you ran",
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
