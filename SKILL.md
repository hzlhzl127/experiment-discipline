---
name: experiment-discipline
description: Load before claiming any experimental improvement, or when results are flat, many variants have been tried, a direction will not converge, or experiment design is being delegated to a model. Protocol for noise floors, sign symmetry, selection/multiplicity, protocol expressiveness, stop-loss and negative-result ledgers.
---

# Experiment discipline

`coding-discipline` covers changes that must compile and pass tests. This skill covers
the other half: an experiment that **runs fine and still proves nothing**.

It decides *whether a number is a result at all*. It does not decide which claims a result
supports (`research-result-to-claim`), whether a manuscript's arithmetic holds
(`paper-audit`), or what statistical test to run (`statistical-analysis`). Chain:
**this → result-to-claim → paper-audit.**

The observed failure this skill exists for: six ablations of one pipeline, all within
±2 AP of the do-nothing baseline, two of them **below** it by 2--3.5. The author reported
the one arm that was +0.4 above baseline as the result. Every individual number was
measured correctly. The **inference** was the bug, and it cost two weeks of GPU.

(Values are deliberately not reproduced here. A rule belongs to whoever paid for it; the
data belongs to whoever ran it.)

## 0. The claim contract

Never write a claim of the form "A is better than B" until you can fill all six lines:

```
effect:    Δ = +1.83 AP, arm_alloc vs arm_uniform
spread:    σ = 0.41 AP from 3 seeds; σ(Δ) = 0.58  (or: unknown)
selection: k = 1 (pre-registered)          |  k = 6 (best of six variants)
verdict:   null  (Δ/short 1.83 < 2σ = 1.16 ... recompute, do not eyeball)
contrary:  arm_size −0.9, arm_random +0.2, arm_wide −2.4 (all null at this σ)
ledger:    EXPERIMENT_LEDGER.md §8 row 7  (or: NOT YET — that is a bug)
```

- **`spread: unknown` forces `verdict: null`.** An unmeasured denominator cannot support a
  measured numerator. "Gain, but we have not measured the noise" is a hypothesis with a
  number attached, not a claim.
- **`selection: k > 1` raises the bar** (§3). A "+0.4" found after trying six things is
  competing against the best of six, not against zero.
- **`contrary:` may not be empty** when the experiment produced more than one arm. If you
  cannot list the other deltas, you did not run one experiment, you ran a search for a
  positive sign.

## 1. The noise floor

Measure it before you need it, and store it where the next session will find it.

| Method | Cost | When |
|---|---|---|
| Two seeds of the **same** config | 2× the run | Default. Report the spread, not just the mean. |
| Paired runs — same seed index in both arms | same as above | Best. The shared data order partly cancels, so σ(Δ) < √2·σ(AP) and often much less. |
| Epoch-to-epoch spread of one run | free | **Not** a noise floor. It measures trajectory jitter, not run-to-run variance. |
| Literature spread from the same protocol | free | Only if the protocol matches exactly; state it as borrowed. |

**What counts as an independent replicate.** Two runs are replicates only if every source
of randomness that can move the metric differs or is controlled: initialisation (or the
data order, if you are fine-tuning a fixed checkpoint), augmentation RNG, loader worker
order, and framework autotuning. Two runs that differ **only in the loader shuffle**
measure the loader, not the method.

**Units.** σ carries the metric's units. Never move a σ between metrics (AP → mm →
mAP-OKS), between datasets, or between protocols; a borrowed floor is valid only for the
exact recipe it came from.

Report σ on the quantity you are claiming. If the claim is "arm A beats arm B", the
relevant σ is of the **difference**: σ(Δ) = √2·σ(AP) for independent seeds.

Before trusting any seed replication, kill the hidden randomness sources: cuDNN
autotuning (`torch.backends.cudnn.benchmark = True` picks algorithms by timing),
nondeterministic kernels, unseeded augmentation, and dataloader worker order. A seed
study on top of autotuning measures the autotuner.

### How many seeds

```
n_pairs ≥ ( threshold · σ(Δ) / Δ )²          threshold = 2 for a pre-registered comparison
```

Worked example, and a warning: with σ(AP) = 0.16 the difference floor is σ(Δ) = 0.226, so a
0.26 effect needs **n = 3.03 → 4 seed pairs (8 runs)** — cheap. With σ(AP) = 0.5 the same
effect needs **n = 29.6 → 30 pairs (60 runs)** — not worth buying. **The same sentence must
never mix two different σ.** (The first version of this skill claimed 30 pairs from
σ = 0.16 — it had silently borrowed the σ = 0.5 answer. That is the class of error the
whole file is about; `--power` and selftest case C now pin these two numbers so the prose
cannot drift from the arithmetic again.)

Do not buy seeds for an effect that is 1σ at any plausible n. Change the question (§8).

## 2. Sign symmetry

The failure is not that people hide negatives. It is that they **explain negatives away**
and **explain positives up**.

| Observation | Motivated reading | Symmetric reading |
|---|---|---|
| arm −1.5 AP vs baseline | "that config was not tuned" | a real negative excursion that needs an explanation |
| arm +0.4 AP vs baseline | "our method works" | inside whatever produced the −1.5 |

**Rule:** the same threshold decides both directions. Every delta in one table gets the
same `gain | null | harm` label using the same σ. You may then interpret — but the label
column is printed first, in full, before any sentence that praises or dismisses.

**Rule:** if the largest negative delta in a table is bigger than the claimed positive
delta, the negative is the headline. Explain it before the positive.

**Caveat that keeps this honest:** if the negative arm is a *broken* protocol (undertrained,
misconfigured, crashed run), say so explicitly and exclude it from the table with the reason
— do not let it silently lend credibility to the positive, and do not let it drive the
conclusion either. The asymmetry test is a prompt to explain, not a proof of nullity.

## 3. Selection is not noise — it is worse

Multiplicity is the failure mode of any loop that generates variants (a human forking every
two days; an agent forking every two hours). It is **not** fixed by measuring σ.

Under a null model of k independent Gaussian tries, the expected best is

```
E[max of k nulls] ≈ σ · √(2 ln k)          k = 6 → 1.9σ    k = 10 → 2.1σ    k = 20 → 2.5σ
```

**State the model, do not present the number as a theorem** — this is an approximation under
i.i.d. Gaussian nulls, and §5 forbids dressing a model up as a measurement. Bonferroni gives
the same order (k = 10 at family-wise 0.05 → about 2.8σ) and is conservative. Use either as
a *bar*, not as a verdict.

Two consequences:

1. **A comparison that survived selection needs a higher threshold.** Report `k` (§0) and
   use threshold ≈ √(2 ln k) (floor 2). "The best of my ten forks gained +2 AP" is exactly
   what a null pipeline produces.
2. **Confirm on new seeds, not on the same ones.** A candidate that clears the raised
   threshold after selection is still a hypothesis. Re-run on fresh seeds (or a held-out
   split, or a fresh data order) and treat *that* as the result. A win found in the search
   and confirmed outside it is real; a win that exists only inside the search is the
   definition of the maximum of k nulls.

**The quieter second selector: the evaluation set.** Choosing the best epoch, the label
width, the bin edges, the smoothing constant, or the seed with the best eval score is the
same multiplicity applied to the *protocol* rather than to the module. Either freeze those
choices before the confirmatory run, or report them explicitly as tuned-on-eval — the second
is honest, silently dropping them is not.

Pre-registration is the cheap version of all of the above: write the comparison down before
running it, and `k = 1`.

## 4. Protocol expressiveness

A module cannot show an effect that the training recipe is incapable of expressing.
Comparing arms under a protocol that cannot express the effect is measuring the
initialisation.

Red flags, in order of how often they are the actual cause:

1. **All arms sit within ±2 of the baseline.** That is a protocol symptom, not a set of
   null modules. Check this before designing the next module.
2. **Fine-tuning hyper-parameters on a from-scratch run** — typically a learning rate ≤ 1e-4
   with < 20 epochs on a randomly initialised backbone does not train it.
3. **Best epoch is the last epoch.** It was still improving; nothing has converged.
4. **Loss is still falling at the end** of every arm.
5. **The new module is zero-initialised and the schedule is too short to leave that state**
   — then the arm is the baseline by construction for its first N epochs.

State the recipe's expressive range explicitly: "this protocol resolves differences of
about X and cannot resolve Y".

## 5. Observation before mechanism

Write the observation; do not write the cause until an arm has isolated it.

- Allowed: "the gain is smaller for the smallest stratum (+3.0 vs +8.6)."
- Not allowed until a run isolates it: "because background occupies more of the crop."
- The test: the sentence "because …" must name a **completed arm**, not a plausible story.

This applies to your own reasoning about statistics too: a formula that assumes i.i.d.
Gaussian nulls is a model, and saying so costs one clause (§3).

A mechanism that was never tested is worse than no mechanism, because it propagates: it
gets copied into a second paper, then into a rebuttal, then it has to be retracted from
three places.

## 6. Decision rights

Convergence requires memory. Whoever decides "what next" must be able to see every earlier
result, including the failures.

- **Never hand a whole codebase to a generator, get a variant back, and let it decide the
  next step.** A generator that cannot see the results — and has no memory of last week's
  failure — will produce the same idea with a new name, forever. Ten forks in twelve days
  is the signature. It is also a multiplicity factory (§3).
- **Before any handoff** (a zip, a spec, a "please implement this"): write the previous
  round's outcome — Δ, σ, k, verdict, and why the direction continues or stops — into the
  ledger. If that line does not exist, the handoff is premature.
- A model may propose mechanisms. A model may **not** decide whether a mechanism worked.

## 7. Stopping

A direction is dead when **two independent mechanisms both land `null`** — not one, and not
"it has not worked yet". Until then it is unfinished; after that, more variants are sunk
cost. Note that "two mechanisms" also means k ≥ 2, so each must clear the raised threshold
of §3.

Write a three-line stop note whenever a directory of work is abandoned:

```
stopped:  <one clause: what was tried>
reason:   <the measurement that killed it, with numbers and σ>
salvage:  <what remains reusable, incl. the negative result itself>
```

Cadence rule: if three consecutive days produce no verifiable artifact (a frozen number, a
passing check, a compiled document), day four is a stop note, not a new module.

## 8. When the honest answer is "we cannot resolve it"

Do not write "no effect". Write the equivalence bound.

> At σ = <your measured floor> <unit>, an effect smaller than 2σ <unit> is not resolvable
> by this protocol.

That sentence is a result. It tells the next person whether to spend a week on 0.1 AP
(no) or to change the question (yes). It also protects you: a reviewer cannot ask for
significance on an effect you have already declared below your resolution.

Then change the question. Options, in order of cost: coarser measurement (a bigger
contrast, a harder split), a paired design, a different intervention with a larger expected
effect, or a different claim about the same data.

## 9. The negative-result ledger

Negative results are the most expensive thing you will ever own and the only thing that
prevents re-running them. Record every closed direction:

| field | content |
|---|---|
| arm | the exact config/experiment name, copy-pasteable |
| result | the number, with σ if it exists |
| verdict | `harm` / `null` / `invalid protocol` (be explicit — "undertrained" is not "no effect") |
| why closed | one clause |
| reusable | what survives (a finding, a tool, a bound) |

**Not in the ledger = not done.** An unrecorded failure will be re-run by you or by the
next person within a month — and it also inflates `k` invisibly for whoever comes next.

## 10. Anti-patterns

| Pattern | Looks like | Actually is |
|---|---|---|
| Ablation ladder with no seeds | six configs, all within ±2 | one measurement of the protocol |
| Best-of-k harvesting | "the best of these variants gains 2 AP" | the expected max of k nulls (§3) |
| Tuning the protocol on eval | "we used the best epoch/label width" | multiplicity one level up (§3) |
| Positive-delta harvesting | "we report the best configuration" | sign asymmetry (§2) |
| Undertrained arm in a table | a 39 AP row among 75s | an invalid protocol, not a weak method |
| Whole-codebase round trips | ten forks in twelve days | a loop with no memory (§6), and a k of 10 (§3) |
| Mechanism-first prose | a tidy causal story in the intro | an untested hypothesis in three places (§5) |
| "It improved by 0.4" | a number with four decimals | a claim with no denominator and no k (§0) |

## 11. The five-minute check

```bash
python <this-skill>/scripts/sigma_gate.py results.tsv --sigma <your floor>
# results.tsv: arm<TAB>seed<TAB>ap   (one row per arm-seed)
# omit --sigma to pool the within-arm spread when arms have >=2 seeds
# --k 10                       raise the threshold to sqrt(2 ln k): the bar after a search
# --power 0.26 --sigma 0.16    required seed pairs for a given effect
```

It prints per-arm verdicts at the stated threshold, the contrary-delta block that must
appear in your write-up, and `FLAT-RESULT ALARM` when no arm clears the bar — the single
most useful alarm in this file. Exit codes: `0` at least one delta resolved, `2` σ unknown
(everything null), `1` bad input.

`--selftest` runs four cases: **A** a synthetic six-arm ladder with σ unknown (must refuse to
resolve, and must flag the negative excursion as the headline), **B** a real two-seed 2×2
from the author's own project (must resolve), **C** the power arithmetic quoted in §1, so the
prose cannot drift from the code, and **D** degenerate inputs — zero σ, zero effect —
refused rather than divided by.
