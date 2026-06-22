from phreeqpython import PhreeqPython
pp = PhreeqPython()
sol = pp.add_solution({
    'units': 'mg/L',
    'temp': 25,
    'pH': 7.0,
    'Fe': 1.0,
    'Al': 1.0,
    'Mn': 1.0,
    'P': 1.0,
    'Ca': 50.0
})
import pprint
pprint.pprint(sol.phases)
