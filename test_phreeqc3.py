from phreeqpython import PhreeqPython
pp = PhreeqPython()
sol = pp.add_solution({
    'units': 'mg/L',
    'temp': 25,
    'pH': 7.2,
    'Ca': 85.0,
    'Mg': 28.0,
    'Na': 130.0,
    'K': 4.5,
    'Cl': 180.0,
    'S(6)': '110.0 as SO4',
    'C(4)': '165.0 as HCO3',
    'Sr': 1.2,
    'F': 0.6,
    'Si': '18.0 as SiO2',
    'Ba': 0.05
})
print('Gypsum:', sol.si('Gypsum'))
print('Anhydrite:', sol.si('Anhydrite'))
print('Calcite:', sol.si('Calcite'))
print('Aragonite:', sol.si('Aragonite'))
