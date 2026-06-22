from phreeqpython import PhreeqPython
pp = PhreeqPython(database='pitzer.dat')
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
print('CF=1:')
print('Gypsum:', sol.si('Gypsum'))
print('Anhydrite:', sol.si('Anhydrite'))
print('Calcite:', sol.si('Calcite'))
print('Aragonite:', sol.si('Aragonite'))

sol4 = pp.add_solution({
    'units': 'mg/L',
    'temp': 25,
    'pH': 7.2,
    'Ca': 85.0 * 4,
    'Mg': 28.0 * 4,
    'Na': 130.0 * 4,
    'K': 4.5 * 4,
    'Cl': 180.0 * 4,
    'S(6)': f"{110.0 * 4} as SO4",
    'C(4)': f"{165.0 * 4} as HCO3",
    'Sr': 1.2 * 4,
    'F': 0.6 * 4,
    'Si': f"{18.0 * 4} as SiO2",
    'Ba': 0.05 * 4
})
print('\nCF=4:')
print('Gypsum:', sol4.si('Gypsum'))
print('Anhydrite:', sol4.si('Anhydrite'))
print('Calcite:', sol4.si('Calcite'))
