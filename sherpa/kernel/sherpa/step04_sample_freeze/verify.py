"""Sample verification, step 10's first action (under the governance lock, before any write):
re-run the samplers and re-read the object's state, compare. Anything moved -> sample.changed,
nothing is written.
"""
from dataclasses import replace

from sherpa.result import KernelStop, kernel_red
from sherpa.step04_sample_freeze.sample_freeze import failed, state_now, take


def verify(policy, sample):
    _, stamps, errors = take(policy, replace(sample, parts={}, stamps={}, errors={}))
    if errors:
        return failed(errors)
    moved = [n for n, s in stamps.items() if sample.stamps.get(n) != s]
    try:
        if state_now(sample) != sample.state:
            moved.append("state")
    except KernelStop as stop:
        return stop.result
    if not moved:
        return None
    return kernel_red("step10_output_apply", "sample.changed",
                      f"{', '.join(moved)} changed between sampling and writing",
                      "run the command again", moved)
