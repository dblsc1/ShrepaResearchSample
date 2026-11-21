"""The phone book: plugins.tsv names a plugin, its kind and where its code is.

impl forms (as ppo built them):
  <pack>/<file>.py       a file in an installed pack, under sherpa/policypack/; the pack folder is
                         loaded as one Python package, so a file may `from .helper import x`
  <dotted.module>        importable, e.g. pip-installed
  exec:<pack>/<path>     any executable; checks only; tri-state JSON over stdin/stdout
The function called is fixed by kind (FUNCTIONS). Modules load on first use only.
"""
import hashlib
import importlib
import importlib.util
import sys
import types
from pathlib import Path

from sherpa.result import KernelStop, kernel_red

FUNCTIONS = {"check": "run", "sampler": "sample", "output": "apply", "command": "run",
             "audit_writer": "write", "notifier": "send", "launcher": "launch"}
_modules = {}


def stop(code, reason, fix, objects=()):
    return KernelStop(kernel_red("registry", code, reason, fix, objects))


def find_file(policy, name: str, relative: str) -> Path:
    path = Path(relative) if relative.startswith("/") else Path(policy.pack_root) / relative
    if not path.is_file():
        raise stop("policy.plugin_missing", f"{name} -> {path} is not there",
                   "reinstall the pack, then rebuild the policy with ppo", [relative])
    return path


def pack_package(folder: Path) -> str:
    """The pack folder as a package in sys.modules (once), so its files can import each other.
    Named after the folder's full path: two workspaces in one process never share a package."""
    name = f"sherpa_pack_{folder.name}_{hashlib.sha256(str(folder).encode()).hexdigest()[:8]}"
    if name not in sys.modules:
        package = types.ModuleType(name)
        package.__path__ = [str(folder)]
        sys.modules[name] = package
    return name


def module_of(policy, name: str):
    impl = policy.plugins[name]["impl"]
    if impl.endswith(".py"):
        path = find_file(policy, name, impl)
        if path not in _modules:
            package = pack_package(path.parent)
            spec = importlib.util.spec_from_file_location(f"{package}.{path.stem}", path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            try:
                spec.loader.exec_module(module)
            except Exception as err:
                del sys.modules[spec.name]
                raise stop("policy.plugin_missing", f"{name} -> {path} does not load: {type(err).__name__}: {err}",
                           "fix the module", [str(path)])
            _modules[path] = module
        return _modules[path]
    try:
        return importlib.import_module(impl)
    except Exception as err:
        raise stop("policy.plugin_missing", f"{policy.plugins[name]['_from']}/plugins.tsv: {name} -> {impl}: {err}",
                   "install the package or fix the impl column", [impl])


def load(policy, name: str, kind: str, command: str = ""):
    """What the kernel calls for plugin `name`: the kind's function, or the module for
    audit_writer (it has two: write and commit). For checks, also enforce COMMANDS."""
    impl = policy.plugins[name]["impl"]
    if impl.startswith("exec:"):
        if kind != "check":
            raise stop("policy.bad_table", f"{name}: exec: impl is for checks only", "use a Python module")
        from sherpa.registry.exec_check import exec_check
        return exec_check(find_file(policy, name, impl[len("exec:"):]))
    module = module_of(policy, name)
    if kind == "check" and command:
        supported = getattr(module, "COMMANDS", ("*",))
        if "*" not in supported and command not in supported:
            raise stop("policy.check_not_for_command",
                       f"check {name} supports {', '.join(supported)}, not {command}",
                       f"remove the '{command}  {name}' row from the pack's checks.tsv", [name])
    if kind != "audit_writer" and not callable(getattr(module, FUNCTIONS[kind], None)):
        raise stop("policy.plugin_missing", f"{name} ({kind}) has no function {FUNCTIONS[kind]}()",
                   f"define {FUNCTIONS[kind]}() in the module", [name])
    return module if kind == "audit_writer" else getattr(module, FUNCTIONS[kind])


def names_of_kind(policy, kind: str) -> list:
    return [n for n, r in policy.plugins.items() if r["kind"] == kind]
