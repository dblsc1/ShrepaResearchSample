"""Entry: parse argv, find the workspace, call the kernel, render the Result.

Exit code (sherpa.result.exit_code): 0 done; 1 refused by a rule or the command line; 2 the policy is
broken or missing; 3 sherpa could not finish.
"""
import json
import os
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from sherpa import __version__, kernel
from sherpa.result import POLICY_BROKEN, KernelStop, exit_code, kernel_red
from sherpa.render import terminal

FLAGS = {"json", "solo", "dump", "help", "print"}   # options that never take a value


@dataclass(frozen=True)
class Args:
    options: MappingProxyType
    positionals: tuple


@dataclass(frozen=True)
class Workspace:
    home: Path              # the directory holding sherpa/
    dot: Path               # home/sherpa: the workspace folder, which is also the governance repo
    config: MappingProxyType
    governance_repo: Path   # = dot: task cards, states, the audit trail (a git repo of its own)
    cwd: Path


WORKSPACE = "sherpa"


def parse_args(argv) -> Args:
    options, positionals, i = {}, [], 0
    while i < len(argv):
        word = argv[i]
        if word.startswith("--") and len(word) > 2:
            name, eq, value = word[2:].partition("=")
            name = name.replace("-", "_")
            if not eq:
                if name not in FLAGS and i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                    value, i = argv[i + 1], i + 1
                else:
                    value = "yes"
            options[name] = value
        else:
            positionals.append(word)
        i += 1
    return Args(MappingProxyType(options), tuple(positionals))


def inside_governance_repo(folder: Path) -> bool:
    """A folder inside some workspace's sherpa/ (a task's worktree, say, which is a checkout of the
    project) is no project root: walking up from it must pass it by and reach the workspace."""
    return any(p.name == WORKSPACE and (p / "config.toml").is_file() for p in folder.parents)


def workspace_at(folder: Path, cwd: Path, config_file: Path) -> Workspace:
    config = {}
    if config_file.is_file():
        try:
            config = tomllib.loads(config_file.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as err:
            raise KernelStop(kernel_red("main", "policy.bad_config", f"{config_file}: {err}",
                                        f"fix the TOML in {WORKSPACE}/config.toml"))
    dot = folder.resolve() / WORKSPACE
    return Workspace(folder.resolve(), dot, MappingProxyType(config), dot, cwd)


def find_workspace(cwd: Path):
    home = os.environ.get("SHERPA_HOME")
    candidates = [Path(home)] if home else [f for f in (cwd, *cwd.parents) if not inside_governance_repo(f)]
    for folder in candidates:
        config_file = folder / WORKSPACE / "config.toml"
        if config_file.is_file():
            return workspace_at(folder, cwd, config_file)
    return None


def init(args) -> int:
    """`sherpa init --inst <license>`: init through the ten steps, in this folder. The policy must
    already be built into sherpa/policy/ (by ppo, a tool of its own); the kernel installs no packs
    (Spec/kernel-policy-contract.zh.md section 5)."""
    cwd = Path.cwd()
    config_file = cwd.resolve() / WORKSPACE / "config.toml"
    if config_file.is_file():          # human 2026-11-03: a workspace already here exits 3, nothing written
        red = kernel_red("main", "init.workspace_exists", f"{config_file} already exists: this folder is a sherpa workspace",
                         "nothing to do; `sherpa next --inst <your license>` shows what you can run")
        emit(args, f"RED {red.error_code}  {red.reason}\n  -> {red.fix}", {"ok": False, "error_code": red.error_code})
        return exit_code([red.error_code])
    try:
        workspace = workspace_at(cwd, cwd, config_file)
    except KernelStop as stop:
        emit(args, f"RED {stop.result.error_code}  {stop.result.reason}\n  -> {stop.result.fix}",
             {"ok": False, "error_code": stop.result.error_code})
        return exit_code([stop.result.error_code])
    result = kernel.step("init", args, workspace)
    emit(args, terminal.render(result), result.to_json_dict())
    return code_of(result)


def code_of(result) -> int:
    if result.ok:
        return 0
    return exit_code([r.error_code for r in result.verdict.results if r.blocks]) or 1


def emit(args, text: str, data) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=1) if args.options.get("json") else text)


def main(argv) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        argv = ["help", *argv[1:]]
    if argv[0] in ("--version", "version"):
        print(f"sherpa {__version__}")
        return 0
    command, args = argv[0], parse_args(argv[1:])
    if command == "init":
        return init(args)
    try:
        workspace = find_workspace(Path.cwd())
    except KernelStop as stop:
        emit(args, f"RED {stop.result.error_code}  {stop.result.reason}\n  -> {stop.result.fix}",
             {"ok": False, "error_code": stop.result.error_code, "reason": stop.result.reason})
        return exit_code([stop.result.error_code])
    if workspace is None:
        if command == "help":
            print(kernel.USAGE)
            return 0
        emit(args, f"no {WORKSPACE}/ here or above (and SHERPA_HOME unset): run `sherpa init --inst <your license>` first",
             {"ok": False, "error_code": "policy.no_workspace"})
        return POLICY_BROKEN
    if command in kernel.QUERIES:
        code, text, data = kernel.query(command, args, workspace)
        emit(args, text, data)
        return code
    result = kernel.step(command, args, workspace)
    emit(args, terminal.render(result), result.to_json_dict())
    return code_of(result)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
