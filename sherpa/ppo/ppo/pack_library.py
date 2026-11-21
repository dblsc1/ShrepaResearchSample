"""Where packs live and what a pack declares.

The library is ../policypack/: base/, classic_lifecycle/, every folder under classic_lifecycle_pack/ and
custom_lifecycle/. A workspace holds its packs flat in sherpa/policypack/<pack>/ (the contract's plugin
paths are <pack>/<file>), and load_order.toml lists the packs that are on. A pack's layer is its
`group`, which must be the library folder it sits in.
"""
import re
import shutil
import tomllib
from dataclasses import dataclass
from pathlib import Path

from ppo import PpoError, Problem

LIBRARY = Path(__file__).resolve().parents[2] / "policypack"
GROUPS = ("base", "classic_lifecycle", "classic_lifecycle_pack", "custom_lifecycle")   # stacking order
DECLARATION = "policy_pack.toml"
LOAD_ORDER = "load_order.toml"
NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_]*")       # custom lifecycles are named by people: PPOtest1Solo
VERSION = re.compile(r"\d+(\.\d+)*")
REQUIREMENT = re.compile(r"\s*([A-Za-z0-9][A-Za-z0-9_]*)\s*(?:(>=|<|==)\s*(\d+(?:\.\d+)*))?\s*")


@dataclass(frozen=True)
class Requirement:
    name: str
    op: str = ""            # "", ">=", "<", "=="
    version: str = ""

    def met_by(self, version: str) -> bool:
        if not self.op:
            return True
        have, want = numbers(version), numbers(self.version)
        return {">=": have >= want, "<": have < want, "==": have == want}[self.op]

    def __str__(self):
        return f"{self.name} {self.op} {self.version}" if self.op else self.name


@dataclass(frozen=True)
class Declaration:
    name: str
    version: str
    requires: tuple
    after: tuple
    conflicts: tuple
    group: str
    writes: tuple
    folder: Path
    provides: tuple = ()     # facts this pack puts in: a sampler's name, or '<command> --<option>'
    reads: tuple = ()        # facts it reads that another pack (or itself) provides


def numbers(version: str) -> tuple:
    return tuple(int(x) for x in version.split("."))


def bad(folder: Path, why: str) -> PpoError:
    return PpoError(Problem("policy.bad_manifest", f"{folder / DECLARATION}: {why}",
                            f"fix {DECLARATION} of pack {folder.name}", (str(folder),)))


def requirements(folder: Path, data: dict, key: str) -> tuple:
    out = []
    for text in data.get(key, []):
        found = REQUIREMENT.fullmatch(text) if isinstance(text, str) else None
        if not found:
            raise bad(folder, f"{key} entry {text!r} is not '<pack>' or '<pack> >= 1.2' (also < and ==)")
        out.append(Requirement(found[1], found[2] or "", found[3] or ""))
    return tuple(out)


def read_declaration(folder: Path) -> Declaration:
    path = folder / DECLARATION
    if not path.is_file():
        raise bad(folder, "missing")
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as err:
        raise bad(folder, str(err))
    name, version, group = data.get("name"), str(data.get("version", "")), data.get("group")
    if name != folder.name or not NAME.fullmatch(name or ""):
        raise bad(folder, f"name {name!r} must be the folder's name {folder.name!r} (letters, digits, _)")
    if not VERSION.fullmatch(version):
        raise bad(folder, f"version {version!r} is not like 1 or 1.2")
    if group not in GROUPS:
        raise bad(folder, f"group {group!r} is not one of {', '.join(GROUPS)}")
    for key in ("requires", "after", "conflicts", "writes", "provides", "reads"):
        if not isinstance(data.get(key, []), list):
            raise bad(folder, f"{key} must be a list")
    writes = tuple(w.strip("/") + ("/" if w.endswith("/") else "") for w in data.get("writes", []))
    if any(not w or w.startswith("..") or "/../" in w for w in writes):
        raise bad(folder, f"writes {list(writes)} must be paths inside the governance repo")
    return Declaration(name, version, requirements(folder, data, "requires"), tuple(data.get("after", [])),
                       requirements(folder, data, "conflicts"), group, writes, folder,
                       tuple(data.get("provides", [])), tuple(data.get("reads", [])))


def library_folders(root: Path = LIBRARY) -> dict:
    """pack name -> its folder in the library."""
    out = {}
    for folder in (root / "base", root / "classic_lifecycle"):
        if (folder / DECLARATION).is_file():
            out[folder.name] = folder
    for layer in ("classic_lifecycle_pack", "custom_lifecycle"):
        for folder in sorted((root / layer).iterdir()) if (root / layer).is_dir() else ():
            if (folder / DECLARATION).is_file():
                out[folder.name] = folder
    return out


def read_load_order(policypack: Path) -> tuple:
    """The enabled packs, in the person's preferred order."""
    path = policypack / LOAD_ORDER
    if not path.is_file():
        raise PpoError(Problem("policy.not_built", f"{path} is missing", "run `ppo init`"))
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as err:
        raise PpoError(Problem("policy.bad_manifest", f"{path}: {err}", f"fix {LOAD_ORDER}"))
    return tuple(data.get("packs", []))


def write_load_order(policypack: Path, packs):
    lines = ["# ppo: which packs are on, in your preferred order (earlier loads first where no rule says otherwise).",
             "# ppo writes this file (enable, disable, packorderchange); you may edit it, then run `ppo build`.",
             f"packs = [{', '.join(quote(p) for p in packs)}]"]
    (policypack / LOAD_ORDER).write_text("\n".join(lines) + "\n", encoding="utf-8")


def quote(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def install(policypack: Path, name: str, root: Path = LIBRARY) -> bool:
    """Copy a pack from the library into the workspace, flat. False when it is there already."""
    if (policypack / name).is_dir():
        return False
    known = library_folders(root)
    if name not in known:
        raise PpoError(Problem("policy.unknown_pack", f"no pack {name!r} installed or in the library",
                               f"use one of: {', '.join(sorted(known))}; or put your own pack in "
                               f"{policypack / name}/", (name,)))
    shutil.copytree(known[name], policypack / name, ignore=shutil.ignore_patterns("__pycache__"))
    return True


def declarations(policypack: Path, names) -> dict:
    """name -> Declaration for the given installed packs; every problem at once."""
    out, problems = {}, []
    for name in names:
        folder = policypack / name
        if not folder.is_dir():
            problems.append(Problem("policy.unknown_pack", f"{name} is in {LOAD_ORDER} but not installed",
                                    f"`ppo enable {name}` installs it, or take it out of {LOAD_ORDER}", (name,)))
            continue
        try:
            out[name] = read_declaration(folder)
        except PpoError as err:
            problems += err.problems
    if problems:
        raise PpoError(*problems)
    return out
