from fastapi import FastAPI
from ocelescope_backend.app.modules import Module, ModuleMeta
from packaging.version import Version
from socel import SOCEL

from ocelescope_module_socel.api import router
from ocelescope_module_socel.api.exception_handlers import register_exception_handlers


class Socel(Module):
    # Mounted at /modules/socel/v1. The frontend's `generate:api` script uses this key.
    meta = ModuleMeta(key="socel", version=Version("1.0"))
    # The host recognizes sOCELs among the logs by this extension, lists it in their
    # metadata and hands it to the endpoints that ask for it (api/dependencies.py).
    extensions = [SOCEL]

    def create_app(self) -> FastAPI:
        app = FastAPI(title="sOCEL", version=str(self.meta.version), docs_url=None, redoc_url=None)
        register_exception_handlers(app)
        app.include_router(router.router)
        return app
