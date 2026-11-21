"""Floor rule, in the kernel: the caller was identified. A fuse behind step 2."""
from sherpa.result import passed, red


def caller_identified(sample):
    caller = sample.caller
    if caller is None or not caller.inst or not caller.role:
        return red("builtin.identified", "the sample carries no identified caller",
                   "pass --inst <license id>; if you did, report a kernel bug")
    return passed(caller.inst)
