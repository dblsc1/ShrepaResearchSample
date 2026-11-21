"""Flow control: step 3 and the only reader of the flow table and reader/writer of object state.

F1 lookup (step 3) · F2 transition_check (step 6) · F3 advance (step 10) · F4 runnable (`next`) ·
F5 validate (step 1).
"""
