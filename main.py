from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import agencies, auth, conversacional, leads, posts, properties
from api.agente import agente as lead_agent

from core.config import settings
from core.middleware import TokenAuthMiddleware

app = FastAPI(title=settings.project_name, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev: permitir cualquier origin
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TokenAuthMiddleware)


app.include_router(auth.router)
app.include_router(agencies.router)
app.include_router(leads.router)
app.include_router(properties.router)
app.include_router(posts.router)
app.include_router(conversacional.router)
app.include_router(lead_agent.router)


@app.get("/health")
def healthcheck():
    return {"status": "ok"}
