"""The five tables: their shapes and the one TSV reader, written from the contract (sections 2.2, 2.3),
not imported from the kernel.

A table file is tab-separated. Blank lines and lines starting with '#' are skipped; the first line
left is the header. A cell holding '-' means "nothing"; no cell may be empty. Columns may come in any
order; a column the contract marks optional may be left out and gets its default. A row whose every
non-key cell is '-' deletes that key from the packs stacked below it (never in a built table).
"""
from dataclasses import dataclass
from pathlib import Path

from ppo import PpoError, Problem

STAGES = ("priority", "general", "builtin")
ACTIONS = ("block", "warn", "log", "off")
KINDS = ("check", "output", "command", "notifier", "launcher", "sampler", "audit_writer")


@dataclass(frozen=True)
class TableShape:
    file: str
    key: tuple
    columns: tuple
    defaults: tuple = ()        # (column, value) for the columns a file may leave out


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


def bad_table(path: Path, line: int, why: str) -> PpoError:
    return PpoError(Problem("policy.bad_table", f"{path}:{line}: {why}", f"fix line {line} of {path}",
                            (f"{path}:{line}",)))


def read_table(path: Path, shape: TableShape) -> list:
    """Rows of one table file as dicts, each with '_line'. No file = no rows."""
    if not path.is_file():
        return []
    rows, header, defaults = [], None, dict(shape.defaults)
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        cells = [c.strip() for c in raw.split("\t")]
        if header is None:
            unknown = [c for c in cells if c not in shape.columns]
            missing = [c for c in shape.columns if c not in cells and c not in defaults]
            if unknown or missing or len(set(cells)) != len(cells):
                raise bad_table(path, number, f"header unknown={unknown} missing={missing}; "
                                              f"columns are {'  '.join(shape.columns)}")
            header = cells
            continue
        if len(cells) != len(header):
            raise bad_table(path, number, f"{len(cells)} cells, the header has {len(header)} "
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
