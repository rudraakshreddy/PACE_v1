# Process Logic & Algorithmic Changes: PACE Calculation Module

This document outlines the modifications, enhancements, and corrections made to the process logic, algorithms, and mathematical formulations of the PACE Calculation Module since its initial specification.

---

## 1. Self-Consistent Element Solute Mass Balance
* **Original Logic**: The element solver approximated the average bulk concentration ($C_b$) inside a membrane element using a static concentration factor derived solely from water flows:
  $$C_b = C_f \times \frac{Q_f}{Q_f - Q_p/2}$$
  This formulation assumes $100\%$ solute rejection. For low-rejection Nanofiltration (NF) membranes, it artificially inflated the bulk concentrations, leading to unphysical scenarios where calculated permeate TDS ($C_p$) exceeded the inlet feed TDS ($C_f$).
* **Updated Logic**: We replaced the static concentration factor with a coupled, self-consistent solver that resolves the local transport and mass conservation equations simultaneously inside the element solver loop:
  * **Flow Ratio ($r$)**:
    $$r = \frac{Q_p}{2 Q_c}$$
  * **Solute Passage Factor ($F_{ion}$)** (Film Theory & Spiegler-Kedem):
    $$F_{ion} = \frac{\beta (1 - R_{true})}{R_{true} + \beta (1 - R_{true})}$$
    where $R_{true}$ is the Spiegler-Kedem reflection coefficient and $\beta$ is the concentration polarization factor ($C_m/C_b$).
  * **Permeate Concentration ($C_p$)**:
    $$C_p = C_f \frac{F_{ion} (1 + r)}{1 + F_{ion} r}$$
  * **Bulk Concentration ($C_b$)**:
    $$C_b = C_f \frac{1 + r}{1 + F_{ion} r}$$
  * **Membrane Surface Concentration ($C_m$)**:
    $$C_m = C_b \frac{\beta}{R_{true} + \beta (1 - R_{true})}$$
  * **Element Concentrate Concentration ($C_c$)**:
    $$C_c = C_f \frac{1 + r (2 - F_{ion})}{1 + F_{ion} r}$$
* **Impact**: Solute mass conservation is strictly preserved. It is mathematically guaranteed that $C_p \le C_f \le C_b \le C_c$ holds for all membranes, eliminating the high permeate TDS bug.

---

## 2. Iterative Feed Pressure Solver (Bisection Method)
* **Original Logic**: The feed pump pressure was calculated using a simple rule-of-thumb starting guess ($P_{start} = \pi_{feed} + 15.0$ bar) and did not iterate to match the user's design target recovery.
* **Updated Logic**: Integrated an iterative feedback bisection solver in `system_engine.py` that search-solves the feed pump operating pressure required to achieve the user's `target_recovery_pct` (within a tolerance of $\pm 0.5\%$).
* **Adaptive Search Window**: To ensure convergence for high-salinity seawater systems and low-salinity groundwater systems alike, the search boundaries are shifted dynamically based on the estimated feed osmotic pressure:
  $$low\_p = \max(1.0, \pi_{feed} - 5.0) \text{ bar}$$
  $$high\_p = \max(120.0, \pi_{feed} + 60.0) \text{ bar}$$
* **Impact**: The simulated system recovery always matches the user's design recovery goal, and the system reports the exact feed pressure required to achieve it.

---

## 3. Dynamic Staged NDP Balancing for Booster Pumps
* **Original Logic**: The interstage booster pump algorithm calculated required feed pressure for subsequent stages by assuming a fixed target Net Driving Pressure (NDP) of $10.0$ bar for NF and $15.0$ bar for RO.
* **Updated Logic**: At low operating pressures (e.g. 2 bar for NF), a static 10 bar target NDP drove the second stage to a massive over-pressure, resulting in a localized $99.9\%$ stage recovery and breaking system-wide recovery control. We changed the booster pump algorithm to target a balanced flux:
  * The booster pump calculates the average NDP of the preceding stage ($Stage\_N$):
    $$NDP_{avg, N} = \frac{1}{N_{elems}} \sum_{elem=1}^{N_{elems}} NDP_{elem}$$
  * The target NDP for the next stage ($Stage\_N+1$) is set to this average value:
    $$NDP_{target, N+1} = \max(0.5, NDP_{avg, N})$$
* **Impact**: Eliminates recovery imbalances across stages, balances fluxes, and ensures that booster pump power calculations scale reasonably with the system's feed pump pressure.

---

## 4. Process Recommendation Upgrade Logic
* **Original Logic**: If NF was drafted as the primary train because of low feed TDS, but failed to meet the target permeate TDS because of low rejection, the engine kept NF as the recommendation and only flagged a warning.
* **Updated Logic**: Restored the strict override rule:
  * If the estimated NF permeate TDS ($C_{p, NF}$) exceeds the target TDS limit ($C_{target}$) by more than $10\%$:
    $$C_{p, NF} > 1.1 \times C_{target}$$
  * The primary recommended technology is automatically upgraded to RO.
* **Impact**: The recommendation engine now guarantees that the recommended technology train is physically capable of meeting the user's target permeate water quality.

---

## 5. UI Parameter Optimization
* **Change**: Removed the redundant "Target Permeate Flow" input field from the UI.
* **Rationale**: Treating both "Target Permeate Flow" and "Feed Flow Rate" as inputs led to conflicts in the element solver. The system now strictly takes "Feed Flow Rate" and "Target Recovery" as the primary inputs, calculating permeate flow as an output ($Q_p = Q_f \times Recovery$).
