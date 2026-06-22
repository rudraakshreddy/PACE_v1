from phreeqpython import PhreeqPython
pp = PhreeqPython(database='minteq.v4.dat')
sol = pp.add_solution({
    'units': 'mg/L',
    'temp': 25,
    'pH': 7.2,
    'Ca': 85.0,
    'S(6)': '110.0 as SO4'
})
print('Gypsum minteq:', sol.si('Gypsum'))
