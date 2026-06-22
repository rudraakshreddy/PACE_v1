from phreeqpython import PhreeqPython
pp = PhreeqPython()
sol = pp.add_solution({
    'units': 'mg/L',
    'temp': 25,
    'pH': 7.2,
    'Ca': 85 * 4,
    'Mg': 28 * 4,
    'Na': 130 * 4,
    'Cl': 180 * 4,
    'S(6)': f"{110 * 4} as SO4",
    'C': f"{165 * 4} as HCO3",
    'Sr': 1.2 * 4,
    'F': 0.6 * 4,
    'Si': f"{18 * 4} as SiO2",
    'Ba': 0.05 * 4
})
print('Gypsum:', sol.si('Gypsum'))
print('Anhydrite:', sol.si('Anhydrite'))
print('Calcite:', sol.si('Calcite'))
print('Aragonite:', sol.si('Aragonite'))
