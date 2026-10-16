# Si-depleted zone around SiC particles (2026-09-30)

Parent: [../small_sic/README.md](../small_sic/README.md). That check found
that a Si-rich zone around each SiC particle raises kappa by 13% to 64%, more
than the particle removes, but its 7 A width was imposed by the Tersoff Ge-C
gate, not predicted. This check asks whether the zone forms, how wide it is,
and whether it cancels the carbon benefit at the campaign recipe.

Design: [zone_design.json](zone_design.json), pre-registered on the campaign
campaign record (seq 62, commit `a1fdf97`) before any production run.

| Stage | What | Where |
|---|---|---|
| Z1 | MACE-MP-0 Ge segregation energy vs distance from an embedded 3C-SiC sphere in Si; equilibrium depletion at 1373 and 1473 K gives the equivalent zone width w_eq | CHPC notchpeak-guest, job 15921347 (reference) then 15921348 (18 sites, afterok) |
| Z2 | Tersoff rNEMD, 98k-atom boxes: host, R = 10 A pockets of width 7 and 12 A, and a SiC particle inside the 12 A pocket; tests the composite rule at a lower pocket fraction | CHPC notchpeak-guest, job 15921349 (8 runs) |
| Z3 | apply Z1 and Z2 to the 1 at% C recipe; registered rule strengthens, corrects or downweights the carbon claims | no compute |

Post-hoc basis (disclosed in the design): a Maxwell-Garnett composite with one
contrast parameter (c = 8.08) reproduces the three parent pocket effects within
1%. Z2 is the out-of-sample test.

## Results (2026-09-30)

Raw outputs ledgered at seq 69 before analysis; decision applied at seq 70
(`apply_zone_decision.py`). All gates pass (G1 19/19 relaxations; G2 Ge-C gap
11.3 A or more; G3 host seeds within 3.7%).

- **No equilibrium Si-rich zone.** MACE puts a Ge atom 0.09 eV lower in energy
  at 6.5 A from the SiC particle centre (1.5 A beyond its surface) and 0.07 eV
  lower at 7.5 A than far away; beyond 8 A the profile is flat within the
  0.01 eV floor, with a weak -0.02 eV shell at 11.5-12.5 A. Ge is attracted to
  the interface, which fits the tensile strain a smaller-lattice SiC particle
  leaves in the surrounding Si. PrZ1 (SiC repels Ge) is refuted and kept as
  refuted. The depleted width at 1373 K and 1473 K is 0.
- **The composite rule holds on new geometry (PrZ2).** Shell-only boxes at
  lower pocket fraction: 1.057 (predicted 1.062, w 7 A) and 1.135 (predicted
  1.139, w 12 A). Particle inside the 12 A pocket: 1.093 vs 1.098 (PrZ3).
  The one-parameter composite rule from the parent check transfers.
- **Decision: strengthen.** With no depleted zone the pocket cancels 0% of the
  particle effect; the seq-61 carbon claims (Ge saving 27-33%, 5 nm SiC) stand.
  A depleted zone would have to be 22 A (R 2.5 nm) or 48 A (R 5 nm) wide to
  erase the benefit.
- **Why the parent MD saw a zone effect:** the pocket in the parent check was
  imposed by the set-up. The equilibrium calculation says a sintered body
  should not form it; if anything, mild Ge enrichment at the interface adds
  alloy scattering, so the adopted numbers are conservative.
- Caveats: the two sites per bin were symmetry-equivalent, so the fixed
  0.01 eV floor, not a within-bin spread, set significance; the Z1 host is
  dilute Ge in pure Si; the particle is 5 A in radius, smaller than the
  campaign's 2.5-5 nm, and the elastic field of larger particles reaches
  further, which would widen the enriched (not depleted) shell.
