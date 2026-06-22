from phreeqpython import PhreeqPython
pp = PhreeqPython()
# Step 1: Define Raw Water at pH 7.5
sol = pp.add_solution({
    'units': 'mg/L',
    'temp': 25,
    'pH': 7.5,
    'Ca': 48.0,
    'Mg': 21.6,
    'Alkalinity': '180.0 as CaCO3',
    'S(6)': '114.0 as SO4',
    'Cl': 55.0,
    'F': 0.5,
    'Si': '6.8 as SiO2'
})
print('Raw Water Calcite SI:', sol.si('Calcite'))

# Step 2: Dose HCl to reach pH 6.1
sol.despeciate()
# We don't know the exact amount, but we can use phreeqc's titration or just change the pH and let PHREEQC balance with a phase.
# Or better, we just change the pH of the solution. If we change pH directly in phreeqpython:
sol.change_ph(6.1, 'HCl')
print('Feed Water Calcite SI (after acid dosing):', sol.si('Calcite'))

