"""takeoff: a clean checkout and a parent branch to fork from.
landing: committing on the task's own branch.  receipt: the task branch is merged into its parent."""
from sherpa.result import passed, red, skipped

COMMANDS = ("takeoff", "landing", "receipt")


def run(sample, params):
    git = sample.parts.get("git") or {}
    card = (sample.parts.get("task_card") or {}).get("card")
    if not git.get("repo"):
        return red("git.no_repo", f"{sample.cwd} is not inside a git checkout", "cd into the project checkout")
    if not card:
        return skipped("no task card")
    branch, parent = card.get("branch"), card.get("parent_branch")
    if sample.command == "takeoff":
        if git["dirty"]:
            return red("git.dirty_tree", f"{git['repo']} has uncommitted changes to tracked files",
                       "commit or stash them, then take off again", [git["repo"]])
        if not git.get("task_branch_exists") and not git.get("parent_branch_exists"):
            return red("git.branch_missing", f"neither {branch} nor its parent {parent} exists",
                       f"create {parent} or fix parent_branch on the card", [parent])
        return passed(branch)
    if sample.command == "landing":
        if git["branch"] != branch:
            return red("git.branch_mismatch", f'current branch "{git["branch"]}" is not the task branch "{branch}"',
                       f"git switch {branch}, then commit there", [git["branch"], branch])
        return passed(branch)
    if not git.get("task_branch_merged"):
        return red("git.not_merged", f"{branch} is not merged into {parent}",
                   f"git switch {parent} && git merge {branch}, then run receipt again", [branch, parent])
    return passed(branch)
