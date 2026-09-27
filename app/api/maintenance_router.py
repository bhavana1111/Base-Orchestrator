"""
Optional isolated router registration.

Import this router from the application's API composition layer when
you are ready to expose maintenance endpoints:

    from app.api.maintenance import router as maintenance_router
    app.include_router(maintenance_router)

No existing application files are modified by this package.
"""

from app.api.maintenance import router

__all__ = ["router"]
