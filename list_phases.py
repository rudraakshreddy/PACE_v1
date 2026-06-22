from phreeqpython import PhreeqPython
pp = PhreeqPython()
print("Phases:", pp.ip.get_phase_list())
