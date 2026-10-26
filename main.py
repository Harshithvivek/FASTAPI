
from fastapi import FastAPI, Path, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, computed_field
from typing import Annotated, Literal, Optional
import json

app = FastAPI()


# Patient model
class Patient(BaseModel):
    id: Annotated[
        str,
        Field(..., description="ID of the patient", examples=["P001"])
    ]
    name: Annotated[str, Field(..., description="Name of the patient")]
    city: Annotated[str, Field(..., description="City where the patient is living")]
    age: Annotated[
        int,
        Field(..., gt=0, lt=120, description="Age of the patient")
    ]
    gender: Annotated[
        Literal["male", "female", "others"],
        Field(..., description="Gender of the patient")
    ]
    height: Annotated[
        float,
        Field(..., gt=0, description="Height of the patient in metres")
    ]
    weight: Annotated[
        float,
        Field(..., gt=0, description="Weight of the patient in kilograms")
    ]

    @computed_field
    @property
    def bmi(self) -> float:
        return round(self.weight / (self.height ** 2), 2)

    @computed_field
    @property
    def verdict(self) -> str:
        if self.bmi < 18.5:
            return "Underweight"
        elif self.bmi < 25:
            return "Normal"
        elif self.bmi < 30:
            return "Overweight"
        else:
            return "Obese"


# Model for updating patient information
class PatientUpdate(BaseModel):
    name: Annotated[Optional[str], Field(default=None)]
    city: Annotated[Optional[str], Field(default=None)]
    age: Annotated[Optional[int], Field(default=None, gt=0, lt=120)]
    gender: Annotated[
        Optional[Literal["male", "female", "others"]],
        Field(default=None)
    ]
    height: Annotated[Optional[float], Field(default=None, gt=0)]
    weight: Annotated[Optional[float], Field(default=None, gt=0)]


# Load data from JSON
def load_data():
    with open("patients.json", "r") as f:
        return json.load(f)


# Save data to JSON
def save_data(data):
    with open("patients.json", "w") as f:
        json.dump(data, f, indent=4)


@app.get("/")
def hello():
    return {"message": "Patient Management System API"}


@app.get("/about")
def about():
    return {
        "message": "A fully functional API to manage your patient records"
    }


@app.get("/view")
def view():
    return load_data()


@app.get("/patient/{patient_id}")
def view_patient(
    patient_id: str = Path(
        ...,
        description="ID of the patient in the DB",
        examples=["P001"]
    )
):
    data = load_data()

    if patient_id in data:
        return data[patient_id]

    raise HTTPException(status_code=404, detail="Patient not found")


@app.get("/sort")
def sort_patients(
    sort_by: str = Query(
        ...,
        description="Sort by height, weight or BMI",
        examples=["height"]
    ),
    order: str = Query(
        "asc",
        description="Sort in ascending or descending order",
        examples=["asc"]
    )
):
    valid_fields = ["height", "weight", "bmi"]

    if sort_by not in valid_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid field. Select from {valid_fields}"
        )

    if order not in ["asc", "desc"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid order. Select either asc or desc"
        )

    data = load_data()

    # Calculate BMI for sorting, even if it isn't stored in the JSON
    patients = []
    for patient_id, patient in data.items():
        patient_copy = patient.copy()
        patient_copy["id"] = patient_id

        if "height" in patient_copy and "weight" in patient_copy:
            patient_copy["bmi"] = round(
                patient_copy["weight"] / patient_copy["height"] ** 2, 2
            )

        patients.append(patient_copy)

    sort_order = order == "desc"

    sorted_data = sorted(
        patients,
        key=lambda patient: patient.get(sort_by, 0),
        reverse=sort_order
    )

    return sorted_data


@app.post("/create", status_code=201)
def create_patient(patient: Patient):
    data = load_data()

    if patient.id in data:
        raise HTTPException(
            status_code=400,
            detail="Patient already exists"
        )

    # Store calculated BMI and verdict with the patient
    data[patient.id] = patient.model_dump(exclude=["id"])

    save_data(data)

    return JSONResponse(
        status_code=201,
        content={"message": "Patient created successfully"}
    )


@app.put("/edit/{patient_id}")
def update_patient(patient_id: str, patient_update: PatientUpdate):
    data = load_data()

    if patient_id not in data:
        raise HTTPException(
            status_code=404,
            detail="Patient not found"
        )

    existing_patient_info = data[patient_id].copy()

    # Update only the fields provided by the user
    updated_patient_info = patient_update.model_dump(exclude_unset=True)

    for key, value in updated_patient_info.items():
        existing_patient_info[key] = value

    # Revalidate all required fields and recalculate BMI and verdict
    existing_patient_info["id"] = patient_id
    patient_pydantic_obj = Patient(**existing_patient_info)

    # Exclude ID because it is used as the JSON dictionary key
    existing_patient_info = patient_pydantic_obj.model_dump(exclude={"id"})

    data[patient_id] = existing_patient_info
    save_data(data)

    return JSONResponse(
        status_code=200,
        content={"message": "Patient updated successfully"}
    )


@app.delete("/delete/{patient_id}")
def delete_patient(patient_id: str):
    data = load_data()

    if patient_id not in data:
        raise HTTPException(
            status_code=404,
            detail="Patient not found"
        )

    del data[patient_id]
    save_data(data)

    return JSONResponse(
        status_code=200,
        content={"message": "Patient deleted successfully"}
    )
