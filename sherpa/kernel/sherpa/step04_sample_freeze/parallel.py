"""Run callables side by side on daemon threads, with one deadline: a hung sampler cannot keep
the command (or the interpreter at exit) waiting past it."""
import threading
import time


def run_parallel(calls: dict, seconds: float) -> dict:
    """{name: fn} -> {name: ("ok", value) | ("error", text)}; unfinished at the deadline -> error."""
    results = {}

    def work(name, fn):
        try:
            results[name] = ("ok", fn())
        except Exception as err:
            results[name] = ("error", f"{type(err).__name__}: {err}")

    threads = [threading.Thread(target=work, args=(n, f), daemon=True) for n, f in calls.items()]
    for t in threads:
        t.start()
    deadline = time.monotonic() + seconds
    for t in threads:
        t.join(max(0.0, deadline - time.monotonic()))
    return {n: results.get(n, ("error", f"took over {seconds}s")) for n in calls}
