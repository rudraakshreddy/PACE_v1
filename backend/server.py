from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import phreeqpython
from process_engine import ProcessInputData, ProcessRecommendationEngine
from process_engine import ProcessInputData, ProcessRecommendationEngine
from system_engine import SystemEngine
from membrane_database import MembraneDatabase
from report_generator import ReportGenerator
from membrane_recommender import MembraneRecommender
from typing import List, Optional
from fastapi.responses import FileResponse
import os

app = FastAPI(title="PHREEQC Scaling Engine API")

# Allow CORS for the frontend to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize PHREEQC engine
pp = phreeqpython.PhreeqPython(database='phreeqc.dat')

class FeedWaterData(BaseModel):
    temperature: float
    ph: float
    calcium: float
    magnesium: float
    sodium: float
    chloride: float
    sulfate: float
    bicarbonate: float
    strontium: float
    fluoride: float
    silica: float
    barium: float
    potassium: float
    ammonium: float
    carbonate: float
    nitrate: float
    aluminium: float
    iron: float
    manganese: float
    phosphate: float
    tss: Optional[float] = 0.0
    turbidity: Optional[float] = 0.0
    tds: Optional[float] = 0.0

class EconomicParams(BaseModel):
    electricity_tariff: float = 7.50
    membrane_cost: float = 26880.0
    vessel_cost: float = 48000.0
    pump_cost_kw: float = 96000.0
    ic_factor: float = 0.15
    contingency_factor: float = 0.10
    plant_availability: float = 0.90
    membrane_lifetime: float = 5.0
    discount_rate: float = 0.10
    project_life: float = 20.0

class SystemCalcInput(BaseModel):
    technology_train: str
    feed_water: dict
    target_flow_m3h: float
    target_recovery_pct: float
    target_tds: Optional[float] = 50.0
    source_type: Optional[str] = "LOW_TDS"
    ro_membrane: str
    uf_module: Optional[str] = None
    stages: int
    vessels_per_stage: List[int]
    elements_per_vessel: int
    economic_params: Optional[EconomicParams] = None
    recycle_enabled: Optional[bool] = False
    recycle_ratio: Optional[float] = 0.0

@app.get("/")
def read_root():
    return {"status": "ok", "message": "PHREEQC Engine is running."}

@app.post("/api/calculate-scaling")
def calculate_scaling(data: FeedWaterData):
    try:
        # Create a new solution
        sol = pp.add_solution({
            'units': 'mg/L',
            'temp': data.temperature,
            'pH': data.ph,
            'Ca': data.calcium,
            'Mg': data.magnesium,
            'Na': data.sodium,
            'K': data.potassium,
            'N(-3)': f"{data.ammonium} as NH4",
            'Cl': data.chloride,
            'S(6)': f"{data.sulfate} as SO4",
            'Alkalinity': f"{data.bicarbonate} as CaCO3",
            'N(5)': f"{data.nitrate} as NO3",
            'Sr': data.strontium,
            'F': data.fluoride,
            'Si': f"{data.silica} as SiO2",
            'Ba': data.barium,
            'Al': data.aluminium,
            'Fe': data.iron,
            'Mn': data.manganese,
            'P': f"{data.phosphate} as PO4"
        })
        
        # Retrieve saturation indices (SI)
        results = {
            "gypsum_si": sol.si("Gypsum"),
            "calcite_si": sol.si("Calcite"),
            "aragonite_si": sol.si("Aragonite"),
            "barite_si": sol.si("Barite"),
            "lsi": sol.si("Calcite"), # LSI is approximated by Calcite SI in pure systems
            "celestite_si": sol.si("Celestite"),
            "fluorite_si": sol.si("Fluorite"),
            "anhydrite_si": sol.si("Anhydrite"),
            "silica_si": sol.si("SiO2(a)"),
            "iron_si": sol.si("Fe(OH)3(a)"),
            "aluminium_si": sol.si("Al(OH)3(a)"),
            "manganese_si": sol.si("Pyrolusite"),
            "calcium_phosphate_si": sol.si("Hydroxyapatite")
        }
        
        # We can also calculate LSI more specifically if needed, but Calcite SI is the rigorous thermodynamic equivalent.
        
        # Clean up memory
        sol.forget()
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process-recommendation")
def process_recommendation(data: ProcessInputData):
    try:
        engine = ProcessRecommendationEngine(pp)
        result = engine.run(data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/calculate-system")
def calculate_system(data: SystemCalcInput):
    try:
        print("CALCULATE SYSTEM INPUT PAYLOAD:", data.dict())
        engine = SystemEngine()
        input_dict = data.dict()
        # Route to recycle wrapper if recycle is enabled
        if data.recycle_enabled and data.recycle_ratio and data.recycle_ratio > 0:
            result = engine.calculate_system_with_recycle(input_dict)
        else:
            result = engine.calculate_system(input_dict)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auto-select-membrane")
def auto_select_membrane(data: SystemCalcInput):
    try:
        best_membrane = None
        best_recovery = 0.0
        smallest_gap = float('inf')
        target = data.target_recovery_pct / 100.0  # Convert % to fraction
        
        membranes = MembraneDatabase.list_ro_membranes()
        engine = SystemEngine()
        
        for mem in membranes:
            data_dict = data.dict()
            data_dict["ro_membrane"] = mem["id"]
            result = engine.calculate_system(data_dict)
            
            if result and "ro_results" in result and result["ro_results"]:
                recovery = result["ro_results"]["summary"]["total_recovery"]
                gap = abs(recovery - target)
                if gap < smallest_gap:
                    smallest_gap = gap
                    best_recovery = recovery
                    best_membrane = mem["id"]
                    
        return {"best_membrane": best_membrane, "max_recovery": best_recovery}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/membranes")
def list_membranes():
    try:
        return {
            "ro_membranes": MembraneDatabase.list_ro_membranes(),
            "uf_modules": MembraneDatabase.list_uf_modules()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-calculation-report")
def generate_calc_report(data: SystemCalcInput):
    try:
        engine = SystemEngine()
        input_dict = data.dict()
        # Route to recycle wrapper if recycle is enabled
        if data.recycle_enabled and data.recycle_ratio and data.recycle_ratio > 0:
            result = engine.calculate_system_with_recycle(input_dict)
        else:
            result = engine.calculate_system(input_dict)
        
        reporter = ReportGenerator()
        file_path = reporter.generate_calculation_report(result)
        
        return FileResponse(
            path=file_path, 
            filename="PACE_Calculation_Report.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/recommend-membrane")
def recommend_membrane(data: SystemCalcInput):
    """Returns ranked Permionics membrane recommendations with scores and rationale."""
    try:
        recommender = MembraneRecommender()
        result = recommender.recommend(data.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
