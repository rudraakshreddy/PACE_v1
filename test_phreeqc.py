from phreeqpython import PhreeqPython
pp = PhreeqPython()
sol = pp.add_solution({
    'units': 'mg/L',
    'temp': 25,
    'pH': 7.2,
    'Ca': 85,
    'Mg': 28,
    'Na': 130,
    'Cl': 180,
    'S(6)': '110 as SO4',
    'C': '165 as HCO3',
    'Sr': 1.2,
    'F': 0.6,
    'Si': '18 as SiO2',
    'Ba': 0.05
})
print('Gypsum:', sol.si('Gypsum'))
print('Anhydrite:', sol.si('Anhydrite'))
print('Calcite:', sol.si('Calcite'))
print('Aragonite:', sol.si('Aragonite'))
