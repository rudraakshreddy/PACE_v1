# Walkthrough: Implementing Intake-Limited UF Sizing

We corrected the UF system calculation engine to use an **intake-limited** approach instead of a net-product-limited approach.

## Summary of Changes

Previously, the sizing model treated the user's input flow as a target net permeate flow ($Q_{\text{net}}$) and scaled up the gross feed flow ($Q_{\text{gross}}$) to account for backwash ($BW$) and forward flush ($FF$) losses.

Now, the system treats the input flow as the **intake/gross feed flow** ($Q_{\text{gross}}$). The number of modules is determined from this gross flow, and the net permeate product flow ($Q_{\text{net}}$) is calculated by subtracting the computed losses:
\[ Q_{\text{net}} = Q_{\text{gross}} - (\text{BW Loss} + \text{FF Loss}) \]

---

## Detailed Code Diffs

### 1. [uf_engine.py](file:///c:/Users/Rudraaksh/OneDrive/Desktop/intern_proj/backend/uf_engine.py)

We changed the signature of `simulate_uf` to accept `gross_feed_flow_m3h` instead of `target_net_flow_m3h`. We removed the recovery-based initial estimation of gross flow and calculated the module counts and flux directly from the gross intake.

```diff
     def simulate_uf(self, 
-                    target_net_flow_m3h: float, 
+                    gross_feed_flow_m3h: float, 
                     temp_c: float,
                     module_name: str,
                     feed_turbidity: float = 20.0,
@@ -34,16 +34,12 @@
         area = module["membrane_area_m2"]
         design_flux = module["design_flux_lmh"]
         
-        # Approximate gross flow initially (assume 95% recovery)
-        est_gross_flow = target_net_flow_m3h / 0.95
-        
-        # Calculate required modules
-        exact_modules = (est_gross_flow * 1000.0) / (design_flux * area)
+        # Intake is fixed, so use gross flow directly to calculate modules
+        exact_modules = (gross_feed_flow_m3h * 1000.0) / (design_flux * area)
         n_modules = math.ceil(exact_modules)
         
-        # Recalculate actual filtration flux
-        actual_gross_flow = est_gross_flow # we will refine this
-        actual_flux = (actual_gross_flow * 1000.0) / (n_modules * area)
+        # Recalculate actual filtration flux based on gross flow
+        actual_flux = (gross_feed_flow_m3h * 1000.0) / (n_modules * area)
         
         # 2. Operating Cycles
         t_filt_min = 90.0
@@ -63,10 +63,9 @@
         
         total_loss_m3h = bw_loss_m3h + ff_loss_m3h
         
-        gross_feed_flow = target_net_flow_m3h + total_loss_m3h
-        actual_flux = (gross_feed_flow * 1000.0) / (n_modules * area)
-        
-        system_recovery = (target_net_flow_m3h / gross_feed_flow) * 100.0
+        net_flow_m3h = gross_feed_flow_m3h - total_loss_m3h
+        
+        system_recovery = (net_flow_m3h / gross_feed_flow_m3h) * 100.0
```

And in the returned payload:

```diff
         return {
             "overview": {
                 "module_type": module_name,
                 "online_units": 1,
                 "total_modules": n_modules,
-                "gross_feed_m3h": round(gross_feed_flow, 1),
-                "net_product_m3h": round(target_net_flow_m3h, 1),
+                "gross_feed_m3h": round(gross_feed_flow_m3h, 1),
+                "net_product_m3h": round(net_flow_m3h, 1),
                 "recovery_pct": round(system_recovery, 2),
                 "tmp_design_bar": round(clean_tmp, 2),
                 "tmp_tmin_bar": round(clean_tmp_tmin, 2)
```

---

### 2. [system_engine.py](file:///c:/Users/Rudraaksh/OneDrive/Desktop/intern_proj/backend/system_engine.py)

We updated the main Technology Train coordinator to pass the system's `target_flow` (representing feed intake) directly to the UF simulation without scaling it, and fed the resulting calculated net permeate flow directly to the RO/NF simulation.

```diff
         # 1. UF Simulation
         if "UF" in train:
             # The system feed flow enters the UF.
-            # UF engine expects target_net_flow_m3h, which is approximately 95% of gross feed.
-            uf_target_net = target_flow * 0.95
-            
+            # UF engine expects gross_feed_flow_m3h (intake limited).
             uf_res = self.uf_engine.simulate_uf(
-                target_net_flow_m3h=uf_target_net,
+                gross_feed_flow_m3h=target_flow,
                 temp_c=feed.get("temperature", 25.0),
                 module_name=input_data.get("uf_module", "IntegraTec-SFD-2880"),
                 feed_turbidity=feed.get("turbidity", 20.0),
@@ -54,7 +54,7 @@
             result["uf_results"] = uf_res
             
             # The feed to the RO/NF system is the UF product
-            ro_feed_flow = uf_target_net
+            ro_feed_flow = uf_res["overview"]["net_product_m3h"]
         else:
             # No UF, RO feed is direct from system feed flow
             ro_feed_flow = target_flow
```
