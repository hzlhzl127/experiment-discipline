# Changelog

Every entry names what was wrong, not what was added. The rule this file exists for is in
`SKILL.md` section 6 of the project rules: *a rule that cannot be followed must be rewritten,
and a revision that leaves no trace is not a revision.*

## 0.3 -- 2026-11-16, second review (same day, before release)

**Fixes**

| # | Defect | Fix |
|---|---|---|
| 6 | Description was 95 words. It is pasted into the skill catalogue on **every turn**, while the body is paid only when loaded -- the most expensive real estate in the file, spent worst. | Cut to 48 words, all triggers kept, trailing clause dropped. |
| 7 | `sigma = 0` reached `delta / sigma` and raised `ZeroDivisionError`; `--power 0` did the same. A floor of zero is a degenerate table, not an exception. | `_require_positive()` refuses it with a message and exit 1. Selftest case **D**. |
| 8 | Never defined what makes two runs independent replicates. Two runs differing only in the loader shuffle are not two experiments. | New §1 paragraph: init / data order / aug RNG / worker order / autotuning. |
| 9 | No units rule. An AP floor was free to migrate onto mm or mAP-OKS. | §1: sigma carries the metric's units; a borrowed floor is valid only for its own recipe. |
| 10 | Missed the **second selector**: best epoch, label width, bin edges and threshold chosen on the evaluation set are the same multiplicity as trying many modules. | §3 new paragraph, plus an anti-pattern row. This one applies to the author's own project. |
| 11 | §3's `sqrt(2 ln k)` was written as a fact while §5 forbids dressing a model up as a measurement. | §3 now states the null model; §5 notes it applies to your own statistics too. |

**Added**

- §0 now carries a filled six-line example instead of an unlabelled template.
- Selftest grew from 2 cases to 4 (A false-result ladder, B real two-seed grid, C the power
  arithmetic, D degenerate inputs).

## 0.2 -- 2026-11-16, first review

**Fixes**

| # | Defect | Fix |
|---|---|---|
| 1 | **Arithmetic error, 10x.** Claimed "sigma 0.16, effect +0.26 needs ~30 seed pairs". Correct: `(2*0.226/0.26)^2 = 3.03`. The 30 was the answer *at sigma 0.5*; the sentence had silently mixed two floors -- the exact class of error the file is about. | Added `n >= (threshold * sigma(delta) / delta)^2`, both worked examples, `--power`, and **selftest case C** to pin the numbers so the prose cannot drift again. |
| 2 | **Missing the most important section:** selection / multiplicity. The diagnosis "no sigma" was only half the disease; "report the best of six" is the other half, and no amount of sigma fixes it. | New §3: `E[max of k nulls] ~ sigma*sqrt(2 ln k)`, k=6/10/20 table, confirm-on-fresh-seeds rule, `--k` raises the threshold, `selection: k` added to the claim contract. |
| 3 | Boundary leak: `sigma = 0.16` (the author's own measured floor) was hardcoded in §8 and in the usage example. | Replaced with `<your measured floor>`. |
| 4 | The sign-symmetry test could be abused: a negative arm that is actually a broken protocol would "prove" the positive is noise. | Added the caveat: exclude broken arms explicitly, with a reason, and use neither to drive the conclusion. |
| 5 | Boundary with neighbouring skills unstated (`research-result-to-claim`, `paper-audit`, `coding-discipline`, `statistical-analysis`). | Chain declared in the header: this -> result-to-claim -> paper-audit. |

## 0.1 -- 2026-11-16, initial

Extracted from a review of the experiment logs of a low-resolution pose-estimation project,
after a two-week detour caused by comparing six ablations that were all inside the noise.
Twelve rules, two gates, three role boundaries, one script.
