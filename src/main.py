from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
import sentry_sdk

from .auth import router as auth_router
from .clients import router as clients_router
from .products import router as products_router
from .orders import router as orders_router
from .core.config import settings
from .core.database import engine # Import engine to potentially create tables (optional)
# from .models import Base # Import Base if using create_all

# Initialize Sentry if DSN is provided
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=1.0,
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        profiles_sample_rate=1.0,
    )

# Optional: Create database tables on startup if not using Alembic migrations
# This is generally NOT recommended for production when using migrations.
# Uncomment the following lines only if you are *not* using Alembic.
# from .models import Base
# Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Lu Estilo API",
    description="API para gerenciamento comercial da Lu Estilo Confecções.",
    version="0.1.0",
    openapi_url="/api/v1/openapi.json", # Customize OpenAPI URL
    docs_url="/api/docs", # Customize Swagger UI URL
    redoc_url="/api/redoc" # Customize ReDoc URL
)

# CORS Middleware Configuration
# Adjust origins as needed for your frontend application
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for now, restrict in production
    allow_credentials=True,
    allow_methods=["*"], # Allow all methods
    allow_headers=["*"], # Allow all headers
)

# Include Routers
app.include_router(auth_router.router, prefix="/auth", tags=["Authentication"])
app.include_router(clients_router.router, prefix="/clients", tags=["Clients"])
app.include_router(products_router.router, prefix="/products", tags=["Products"])
app.include_router(orders_router.router, prefix="/orders", tags=["Orders"])

# Custom Exception Handler for Validation Errors (optional, for cleaner responses)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # You can format the error details as needed
    # error_details = exc.errors()
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()}, # Pydantic v2 errors() format
    )

# Root endpoint
@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Bem-vindo à API Lu Estilo! Acesse /api/docs para a documentação."}

# Placeholder for WhatsApp integration endpoint/webhook if needed
# @app.post("/whatsapp/webhook", tags=["WhatsApp"])
# async def whatsapp_webhook(request: Request):
#     # Process incoming WhatsApp messages or events
#     pass

