# Party 4a: DFT+BTE via almaBTE (true different-method-family party)

The production half of evidence party 4 (`../06_evidence_party_roadmap.md`).
Party id `BTE-DFT`. Status 2026-09-27: all 18 points in `results/`,
analysis in `RESULTS.md`, joined to the hypergraph.
Bring-up ran on notchpeak (almabte/1.3.2, Si+Ge database
entries fetched); validation gate pure Si @ 12^3 / 300 K = RTA 135.3,
full iterative BTE 141.3 W/mK (full BTE in the experimental band; the
140-155 target is the converged-grid RTA figure). Production array
**15859315** (6 compositions x {300, 700, 1100} K at 24^3, one array
task per composition) ran on notchpeak-guest / owner-guest.
Results are in `results/` and join the hypergraph via
`../pilot/kg/extract_kg.py --reuse`.

## Why almaBTE and not a from-scratch phono3py campaign

The roadmap's cost objection to a DFT party (hundreds to thousands of
core-hours per composition for anharmonic force constants) has a
shortcut almaBTE was built for: the almaBTE materials database ships
*precomputed ab initio 2nd/3rd-order force constants* for elemental Si
and Ge, and its virtual-crystal (VCA) machinery with mass-disorder
scattering is exactly the standard treatment for Si1-xGex; the alloy is
one of the almaBTE paper's own worked examples (Carrete et al., Comput.
Phys. Commun. 220, 351 (2017)). So the party enters at BTE solve cost
(CPU minutes-hours per point) instead of DFT campaign cost, while still
being genuinely first-principles in parentage: a true second textbook
against the Tersoff parties, and (unlike party 4b MACE) not an MD
method at all, which makes it the strongest independence unit the
campaign has.

The `almabte` module is a phase-0-verified CHPC module.

## Plan (matching the roadmap: small by design)

- Grid: x in {0, 0.15, 0.2, 0.5, 0.85, 1} at T in {300, 700, 1100} K
  (chosen to overlap every other party: Tersoff MD grid, GPUMD
  endpoints, DB-CITRINE x=0.2 rows, literature).
- `bringup_almabte.sh` is deliberately exploratory-but-logged: module
  environments differ, and the almaBTE database URL layout must be
  confirmed on the login node. It (1) loads the module and records the
  tool inventory, (2) fetches the Si and Ge database entries, (3) runs
  `VCAbuilder` and a single `kappa_Tsweep` for pure Si as the
  validation gate (target: Si kappa(300 K) ~ 140-155 W/mK RTA is the
  known almaBTE Si result; that this is *near experiment* while
  Tersoff-MD sits near 200+ is itself party-bias evidence), then
  (4) sweeps the grid. Everything echoes into `bringup.log` so a failed
  step can be iterated without guessing.
- BTE caveats to record per point: VCA + mass-disorder misses
  short-range order and anharmonic disorder coupling; RTA underpredicts
  kappa for weakly-scattering pure crystals (use the full iterative
  solution where the tool offers it); high-T (1100 K) perturbative
  phonons are stretched exactly where MD is comfortable. These enter
  the campaign record as method scope labels, mirroring how Tersoff's alloy
  suppression is recorded.
- Output: one JSON per point in `results/` with
  `{x, T, kappa_W_mK, tag}`; `../pilot/kg/extract_kg.py` already scans
  `party4_bte/results/`.
