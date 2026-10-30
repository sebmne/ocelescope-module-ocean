from fastapi import APIRouter

from ocelescope_module_socel.api.routes import (
    build_socel,
    classes,
    classification,
    configure_socel,
    connect_factor_catalog,
    disconnect_factor_catalog,
    flow_instances,
    flow_inventory,
    flow_records,
    impact,
    list_factor_catalogs,
    preview_record_file,
    resolve_catalog_factor,
    search_factor_catalog,
    status,
    taxonomy,
    upload_record_file,
)

router = APIRouter(tags=["sOCEL"])
logs = APIRouter(prefix="/logs/{ocel_id}")

for resource in (
    status,
    classes,
    flow_inventory,
    flow_instances,
    flow_records,
    classification,
    build_socel,
    configure_socel,
    upload_record_file,
    preview_record_file,
    impact,
):
    logs.include_router(resource.router)

for resource in (
    taxonomy,
    list_factor_catalogs,
    connect_factor_catalog,
    disconnect_factor_catalog,
    search_factor_catalog,
    resolve_catalog_factor,
):
    router.include_router(resource.router)

router.include_router(logs)
