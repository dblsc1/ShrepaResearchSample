"""The five tables: their shapes and the one TSV reader. ppo writes sherpa/policy/ in this format,
plus a last column `pack` (Spec/kernel-policy-contract.zh.md, section 2.2); the kernel reads that.

A table file is tab-separated. Lines starting with '#' and blank lines are
ignored; the first remaining line is the header. A cell holding '-' means
"nothing". A row whose every non-key cell is '-' deletes that key from the
layers below; in the three tables with a `locked` column that includes
writing `locked` as '-' (an output row with no params is otherwise all '-').
"""
from dataclasses import dataclass
from pathlib import Path

from sherpa.result import KernelStop, kernel_red

STEP = "step01_policy_load"
STAGES = ("priority", "general", "builtin")
ACTIONS = ("block", "warn", "log", "off")
KINDS = ("check", "output", "command", "notifier", "launcher", "sampler", "audit_writer")


@dataclass(frozen=True)
class TableShape:
    file: str
    key: tuple
    columns: tuple
    defaults: tuple = ()        # (column, value) pairs a file may leave out


TABLES = {
    "flow": TableShape("flow.tsv", ("command",),
                       ("command", "roles", "actor", "object", "from", "to", "body")),
    "checks": TableShape("checks.tsv", ("command", "check"),
                         ("command", "check", "roles", "stage", "action", "params", "locked"),
                         (("roles", "*"), ("locked", "no"))),
    "outputs": TableShape("outputs.tsv", ("event", "output"),
                          ("event", "output", "roles", "params", "locked"),
                          (("roles", "*"), ("locked", "no"))),
    "roles": TableShape("roles.tsv", ("role",), ("role", "prefix", "superior", "card"),
                        (("superior", "-"), ("card", "-"))),
    "plugins": TableShape("plugins.tsv", ("name",), ("name", "kind", "impl", "locked"),
                          (("locked", "no"),)),
}


def bad_table(path: Path, line: int, why: str) -> KernelStop:
    return KernelStop(kernel_red(STEP, "policy.bad_table", f"{path}:{line}: {why}",
                                 f"fix line {line} of {path}", [f"{path}:{line}"]))


def read_table(path: Path, shape: TableShape) -> list:
    """Rows of one table file as dicts, each carrying '_line'. Missing file = no rows."""
    if not path.is_file():
        return []
    rows, header = [], None
    defaults = dict(shape.defaults)
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        cells = [c.strip() for c in raw.split("\t")]
        if header is None:
            header = cells
            unknown = [c for c in header if c not in shape.columns]
            missing = [c for c in shape.columns if c not in header and c not in defaults]
            if unknown or missing:
                raise bad_table(path, number, f"header unknown={unknown} missing={missing}; "
                                              f"columns are {'  '.join(shape.columns)}")
            continue
        if len(cells) != len(header):
            raise bad_table(path, number, f"{len(cells)} cells, header has {len(header)} "
                                          "(cells are separated by one tab)")
        row = dict(defaults)
        row.update(zip(header, cells))
        if any(not row[c] for c in shape.columns):
            raise bad_table(path, number, "empty cell; write '-' for nothing")
        row["_line"] = number
        rows.append(row)
    return rows


def is_deletion(row: dict, shape: TableShape) -> bool:
    return all(row[c] == "-" for c in shape.columns if c not in shape.key)


def key_of(row: dict, shape: TableShape) -> tuple:
    return tuple(row[c] for c in shape.key)


def split_list(cell: str) -> tuple:
    """'a,b' -> ('a', 'b'); '-' -> ()."""
    return () if cell == "-" else tuple(x for x in cell.split(",") if x)


def role_allowed(row, role: str) -> bool:
    """The `roles` column of flow, checks and outputs rows: 'a,b', '*' for every role, '-' for none."""
    roles = split_list(row["roles"])
    return "*" in roles or role in roles


def parse_params(cell: str) -> dict:
    """'path=docs/a.md;max=3' -> {'path': 'docs/a.md', 'max': '3'}; '-' -> {}."""
    if cell == "-":
        return {}
    out = {}
    for pair in cell.split(";"):
        name, sep, value = pair.partition("=")
        out[name.strip()] = value.strip() if sep else "yes"
    return out
