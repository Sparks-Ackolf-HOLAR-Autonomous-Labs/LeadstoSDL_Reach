# Party 4a results: almaBTE DFT+BTE kappa(x, T), array 15859315

Collected 2026-09-27. All 6 array tasks COMPLETED exit 0 on
notchpeak-guest, ~75 min each, zero preemptions. 18 points (6
compositions x {300, 700, 1100} K), 24^3 q-grid, full iterative BTE
with RTA also recorded per point. Raw JSON in `results/`; joined to the
evidence hypergraph as party `BTE-DFT` (the campaign's first
first-principles-parentage party).

## The numbers (full iterative BTE, W/mK)

| x_Ge | 300 K | 700 K | 1100 K |
|---|---|---|---|
| 0 (pure Si) | 160.5 | 63.8 | 40.5 |
| 0.15 | 8.33 | 6.69 | 5.72 |
| 0.2 | 7.27 | 5.89 | 5.07 |
| 0.5 | 6.49 | 5.08 | 4.30 |
| 0.85 | 11.54 | 7.83 | 6.21 |
| 1 (pure Ge) | 57.1 | 25.7 | 16.7 |

RTA sits 1-2% below full BTE for the alloys and 3-9% below for the pure
elements, the expected pattern (normal-process repopulation matters most
in weakly-scattering crystals).

## Cross-party comparison at 300 K (the point of party 4)

| x_Ge | BTE-DFT | Tersoff rNEMD kappa_inf | GPUMD Tersoff HNEMD | experiment / DB |
|---|---|---|---|---|
| 0 | 160.5 | ballistic (lower bound 34.7) | 163 +/- 40, 216 +/- 87 | ~148 (lit), 150 (Citrine 298 K) |
| 0.15 | 8.33 | 1.96 | - | ~10 (Abeles-line bulk) |
| 0.2 | 7.27 | - | - | Citrine RTG-grade: 2.4-4.3 |
| 0.5 | 6.49 | 1.80 | 1.885 +/- 0.19 | 7.1 (Citrine), ~8-9 (lit bulk) |
| 1 | 57.1 | ballistic | 66.8 +/- 25 | ~60 |

### Findings

1. **The Tersoff alloy suppression is now measured, not asserted: a
   factor ~3.6 at x=0.5/300 K** (BTE 6.49 vs Tersoff 1.80-1.885), and
   ~4.2 at x=0.15 (8.33 vs 1.96). BTE itself lands within ~10-30% of
   the experimental bulk values. This is the measured inter-party
   error the flagged independence-units assumption wanted: the number
   the fitted law's Tersoff-parentage scope label now carries.
2. **CORRECTED 2026-09-29: at 300 K the endpoints do NOT agree; see `../gpumd/production/RESULTS.md`.** The pre-registered GPUMD production campaign (longer runs, more seeds) gives Tersoff Si 284-423 and Ge 89-107 W/mK at 300 K, about 1.6-1.8x the BTE values; agreement holds only at 1100 K (Si 51 vs 40.5, Ge 18 vs 16.7). The original text below was based on the short validation-gate runs and is kept for the record.
   Original: **At the pure endpoints the two method families agree.** BTE Si
   160.5 vs GPUMD-Tersoff 163 +/- 40; BTE Ge 57.1 vs GPUMD 66.8 +/-
   25; both near experiment (~148 / ~60). So the party disagreement
   decomposes cleanly by regime: Tersoff-1989 transport is fine for
   the pure elements and fails specifically in the mass-disorder
   alloy regime. A per-regime scope label, exactly the shape the
   shard machinery stores, and much more useful than "Tersoff is
   biased" as a blanket statement.
3. **The endpoint restore path now has two independent witnesses.**
   The rNEMD ballistic wall that forced the alloys-only scope-limit is
   bridged by GPUMD HNEMD (Tersoff family) and almaBTE (DFT family)
   agreeing within errors at both endpoints. This is the evidence
   P2's pre-registered endpoint-restoration campaign lifts the
   scope-limit with.
4. **The Citrine x=0.2 gap is the microstructure story again.** BTE
   perfect-crystal VCA gives 7.27; the Citrine Si0.8Ge0.2 rows read
   2.4-4.3 because they are hot-pressed, doped RTG thermoelectric
   material (grain-boundary + dopant scattering). Composition and
   temperature alone cannot reconcile them; microstructure scope can.
   Live confirmation of the P1 metadata claim, now from a
   first-principles direction.
5. **Temperature trends agree qualitatively across families**: alloy
   kappa decreases weakly with T (BTE -34% over 300->1100 K at x=0.5;
   Tersoff rNEMD -16%), pure elements strongly (~1/T). BTE's extra
   decrease is Umklapp on top of alloy scattering; at 1100 K
   perturbative phonons are stretched (recorded per point in
   `scope_notes`).

### Flag: Ge-rich vs Si-rich asymmetry (candidate shard action)

BTE gives x=0.85 (11.5) noticeably above x=0.15 (8.3), while the
classic Abeles-line experimental data has the two sides roughly
comparable (Si-rich if anything slightly higher). Plausible VCA
mechanism: mass-disorder scattering strength scales with (dM/M_avg)^2,
and the heavier Ge-rich virtual crystal sees a smaller relative mass
variance. Whether that asymmetry is physical or a VCA artifact is
precisely a question the machinery should spend an audit on: flagged
as a candidate shard action (cross-check against digitized Abeles
1963 data in the literature party) rather than resolved by hand here.

## Scope notes carried per point (in each JSON)

- VCA + mass-disorder: no short-range order, no anharmonic-disorder
  coupling; known to underpredict the alloy dip depth somewhat.
- Perturbative phonon picture stretched at 1100 K (where MD is
  comfortable): the two families' strong/weak regimes are
  complementary by design.
- First-principles parentage: almaBTE database DFT force constants
  (Carrete et al., CPC 220, 351 (2017)); party independence unit =
  DFT/BTE method family, not MD.
