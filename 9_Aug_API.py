from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()
@app.get("/manas/pandey/xyz")
def add(a: int,b: int):
    return a + b


#Which python for path 
#export PATH="/usr/local/bin:$PATH"
#source ~/.zshrc   # or ~/.bash_profile if you use bash ---Restart your termonal



#/usr/local/bin/python3 -m pip install fastapi uvicorn
#/usr/local/bin/python3 /Users/saumyapandey/Downloads/GenAI-2Aug-Euron/9_Aug_API.py


class subtractModel(BaseModel):
    a: int
    b: int

@app.post("/manas/pandey/xyz/subtract")
def subtract(a: int, b: int):
    return a - b

def subgract_numbers(model: subtractModel):
    return subtract(model.a - model.b)

print(add(3,4))