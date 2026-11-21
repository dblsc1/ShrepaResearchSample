"""F5 · called by step 1: the flow table may only name known roles, object folders the kernel may
keep state in, and actor paths that start at a sampler; it yields the state set."""
from sherpa.result import KernelStop, kernel_red
from sherpa.step01_policy_load.tables import split_list
from sherpa.step02_identity_read.identity_read import ID

STEP = "step01_policy_load"
PPO_FOLDERS = ("policy", "policypack")      # ppo's: no object state goes there


def stop(code, reason, fix):
    return KernelStop(kernel_red(STEP, code, reason, fix))


def validate(flow, roles, plugins) -> frozenset:
    for row in flow.values():
        where = f"{row['_from']}/flow.tsv:{row['_line']}"
        for role in split_list(row["roles"]):
            if role != "*" and role not in roles:
                raise stop("policy.unknown_role", f"{where} names role '{role}', roles.tsv has no such role",
                           "add the role to roles.tsv or fix the roles column")
        if row["object"] != "-" and (not ID.fullmatch(row["object"]) or row["object"] in PPO_FOLDERS):
            raise stop("policy.bad_table", f"{where} object '{row['object']}'",
                       "object is a folder name in the governance repo (e.g. tasks), not policy or policypack; or '-'")
        sampler = row["actor"].split(".", 1)[0]
        if row["actor"] != "-" and ("." not in row["actor"] or plugins.get(sampler, {}).get("kind") != "sampler"):
            raise stop("policy.bad_table", f"{where} actor '{row['actor']}'",
                       "actor is a path into the sample's parts that starts at a sampler "
                       "(e.g. task_card.card.assignee); or '-'")
        if row["object"] == "-" and (row["from"] != "-" or row["to"] != "-"):
            raise stop("policy.bad_table", f"{where} has from/to but no object",
                       "set the object column, or write '-' in from and to")
    for row in roles.values():
        if row["superior"] != "-" and row["superior"] not in roles:
            raise stop("policy.unknown_role",
                       f"{row['_from']}/roles.tsv:{row['_line']} superior '{row['superior']}' is not a role",
                       "add that role or fix the superior column")
    return frozenset(s for row in flow.values() for col in ("from", "to") for s in split_list(row[col]))
