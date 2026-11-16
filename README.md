# experiment-discipline

A skill for the failure mode that is not a crash: **an experiment that runs fine and still
proves nothing.**

Most research tooling helps you run experiments. This one decides whether a number you have
is a result at all — and it refuses to let you claim one when it isn't.

## What it is for

Six ablations of one pipeline, all within ±2 of the do-nothing baseline, two of them 2–3.5
**below** it. The author reported the one arm that was +0.4 above baseline as the finding.
Every individual number was measured correctly. The inference was the bug, and it cost two
weeks of GPU.

This skill is the protocol that would have caught it, turned into something executable.

## Install

```powershell
# Windows, from this directory
powershell -ExecutionPolicy Bypass -File install.ps1
```

```bash
# any OS: it is just a folder
cp -r . ~/.dsh/skills/experiment-discipline
```

It is discovered automatically by DeepSeek Harness; the name is `experiment-discipline`.
Nothing else is needed — `SKILL.md` is the whole interface.

## Use

```bash
# the gate: one row per arm-seed
python scripts/sigma_gate.py results.tsv --sigma 0.16

# after a search over k variants, the bar rises to sqrt(2 ln k)
python scripts/sigma_gate.py results.tsv --sigma 0.16 --k 10

# how many seeds would this effect need?
python scripts/sigma_gate.py --power 0.26 --sigma 0.16
#   sigma(delta)    = 0.2263
#   required pairs  = 3.03  -> round up to 4 seed pairs (8 runs)

python scripts/sigma_gate.py --selftest     # 4 cases, must print SELFTEST: PASS
```

`results.tsv`:

```
arm	seed	ap
cell_a	8888	72.7276
cell_a	1	72.5658
cell_b	8888	79.1181
cell_b	1	79.0131
```

Exit codes: `0` at least one delta resolved, `2` σ unknown (everything is null), `1` bad input.

## What it enforces

| Section | Rule |
|---|---|
| §0 | a claim needs six lines: effect, σ, **selection k**, verdict, contrary deltas, ledger row |
| §1 | measure the floor first; define what counts as an independent seed; σ has units |
| §2 | the same threshold labels negatives and positives — negatives are explained, not dropped |
| §3 | **selection is not noise**: the best of k nulls is ≈ σ√(2 ln k), so k > 1 raises the bar, and a survivor must be confirmed on fresh seeds |
| §4 | a module cannot show an effect the training recipe cannot express |
| §5 | no mechanism before the arm that isolates it — including mechanisms about your own statistics |
| §6 | decision rights: a generator with no memory of the failures will loop forever |
| §7 | stopping rule and the three-line stop note |
| §8 | write the equivalence bound, not "no effect" |
| §9 | every closed direction goes in the ledger, or it will be re-run |
| §10 | eight anti-patterns, each with what it actually is |

## Evidence it works

`--selftest` pins four cases, including one that is easy to get wrong and was in fact wrong
in the first version: the sample-size arithmetic (σ = 0.16 → 4 pairs; σ = 0.5 → 30 pairs).
Case C exists so the prose cannot drift from the code again.

## Limits, stated on purpose

- **It cannot measure σ for you.** It can only refuse to conclude before you do.
- `√(2 ln k)` is an approximation under i.i.d. Gaussian nulls, not a theorem; Bonferroni is
  the conservative alternative. Both are bars, not verdicts.
- **It cannot see `k`.** An agent may honestly write `k = 1` after trying six times. That is
  the largest remaining hole, and it is a honesty problem, not a software one.
- It says nothing about whether a direction is *worth* trying. Rules prevent self-deception;
  they do not supply taste.
- It is a companion to `coding-discipline` (does it build), `research-result-to-claim` (what
  does it support) and `paper-audit` (does the arithmetic hold). It is the gate before all
  three.

## Licence

MIT. See `LICENSE`.
