from fastapi import FastAPI
from mock_services.routers import crm, core_banking, notifications, workflow

app = FastAPI(title="Mock Banking Services")

# Routers
app.include_router(crm.router, prefix="/crm", tags=["CRM"])
app.include_router(core_banking.router, prefix="/core", tags=["Core Banking"])
app.include_router(notifications.router, prefix="/notify", tags=["Notifications"])
app.include_router(workflow.router, prefix="/workflow", tags=["Workflow"])

@app.get("/")
async def root():
    return {"status": "mock services running"}
