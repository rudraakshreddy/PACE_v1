import requests

payload = {
    'temperature': 25,
    'ph': 7.2,
    'calcium': 85.0,
    'magnesium': 28.0,
    'sodium': 130.0,
    'chloride': 180.0,
    'sulfate': 110.0,
    'bicarbonate': 165.0,
    'strontium': 1.2,
    'fluoride': 0.6,
    'silica': 18.0,
    'barium': 0.05,
    'potassium': 4.5,
    'ammonium': 0.2,
    'carbonate': 0.8,
    'nitrate': 15.0
}
r = requests.post('http://localhost:8000/api/calculate-scaling', json=payload)
print(r.json())
