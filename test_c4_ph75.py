from phreeqpython import PhreeqPython
pp = PhreeqPython()
sol = pp.add_solution({
    'units': 'mg/L',
    'temp': 25,
    'pH': 7.5,
    'Ca': 48.0,
    'Mg': 21.6,
    'C(4)': '180.0 as CaCO3',
    'S(6)': '114.0 as SO4',
    'Cl': 55.0,
    'F': 0.5,
    'Si': '6.8 as SiO2'
})
print('Calcite SI:', sol.si('Calcite'))
