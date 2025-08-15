from fastapi import FastAPI
from pydantic import BaseModel

app= FastAPI()

class Calaculator(BaseModel):
    a: int
    b: int

@app.post("/manas/pandey/xyz/multiply")
def multiply(model: Calaculator):
    return{"product":model.a * model.b}

@app.post("/manas/pandey/xyz/divide")
def divide(model: Calaculator):
    if model.b ==0:
        return {"error": "Division by zero is not allowed"}
    return {"Quotient":model.a/model.b}

@app.post("/manas/pandey/xyz/add")
def add(model: Calaculator):
    return {"sum":model.a + model.b}

@app.post("/manas/pandey/xyz/subtract")
def suntract(model: Calaculator):
    return {"difference": model.a - model.b}