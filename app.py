from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, computed_field
from typing import Annotated, Literal, Optional
import pandas as pd
import pickle

#import ML Model
with open("model.pkl", "rb") as f:
    model = pickle.load(f)
    
app = FastAPI()

tier_1_cities = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata", "Hyderabad", "Pune"]
tier_2_cities = [
    "Jaipur", "Chandigarh", "Indore", "Lucknow", "Patna", "Ranchi", "Visakhapatnam", "Coimbatore",
    "Bhopal", "Nagpur", "Vadodara", "Surat", "Rajkot", "Jodhpur", "Raipur", "Amritsar", "Varanasi",
    "Agra", "Dehradun", "Mysore", "Jabalpur", "Guwahati", "Thiruvananthapuram", "Ludhiana", "Nashik",
    "Allahabad", "Udaipur", "Aurangabad", "Hubli", "Belgaum", "Salem", "Vijayawada", "Tiruchirappalli",
    "Bhavnagar", "Gwalior", "Dhanbad", "Bareilly", "Aligarh", "Gaya", "Kozhikode", "Warangal",
    "Kolhapur", "Bilaspur", "Jalandhar", "Noida", "Guntur", "Asansol", "Siliguri"
]

#pydantic validate incoming data 
class UserInput(BaseModel):
    age: Annotated[int, Field(..., gt=0, lt=120, description="Age of the patient")]
    weight: Annotated[float, Field(..., gt=0, description="Weight of the patient in kilograms")]
    height: Annotated[float, Field(..., gt=0, description="Height of the patient in meters")]
    income_lpa: Annotated[float, Field(..., gt=0, description="Income of the patient in LPA")]
    smoker: Annotated[bool,Field(..., description="Whether the patient is a smoker or not")]
    city: Annotated[str, Field(..., description="City where the patient is living")]
    occupation: Annotated[Literal["retired","unemployed","government_job","student","Freelancer","freelancer","private_job","business_owner"], Field(..., description="Occupation of the patient")]
    
    @computed_field
    @property
    def bmi(self) -> float:
        return round(self.weight / (self.height ** 2), 2)
    
    @computed_field
    @property
    def lifestyle_risk(self) -> str:
        if self.smoker and self.bmi > 30:
            return "high"
        elif self.smoker or self.bmi > 27:
            return "medium"
        else:
            return "low"
        
    @computed_field
    @property
    def age_group(self) -> str:
        if self.age < 25:
            return "young"
        elif self.age < 45:
            return "adult"
        elif self.age < 60:
            return "middle_aged"
        else:
            return "senior"
        
    @computed_field
    @property
    def city_tier(self) -> int:
        if self.city in tier_1_cities:
            return 1
        elif self.city in tier_2_cities:
            return 2
        else:
            return 3
        
@app.post("/predict")
def predict_predict(data: UserInput):
    
    Input_df = pd.DataFrame([{
        "bmi":data.bmi,
        "age_group":data.age_group,
        "lifestyle_risk":data.lifestyle_risk,
        "city_tier":data.city_tier,
        "occupation":data.occupation.lower(),
        "income_lpa":data.income_lpa
    }])
    
    prediction = model.predict(Input_df)[0]
    return JSONResponse(status_code= 200,content={"prediction_category": prediction})