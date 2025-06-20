from fastapi import FastAPI

app = FastAPI(
    title="Procurement Management System",
    description="Backend API for managing procurement purposes, EMFs, costs, and hierarchies",
    version="1.0.0",
)


@app.get("/")
def root():
    return {"message": "Procurement Management System API"}
