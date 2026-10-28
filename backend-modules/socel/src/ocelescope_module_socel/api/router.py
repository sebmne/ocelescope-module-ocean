from fastapi import APIRouter

from ocelescope_module_socel.api.routes import (
    build_socel,
    classes,
    classification,
    configure_socel,
    flow_instances,
    flow_inventory,
    flow_records,
    impact,
    preview_record_file,
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

router.include_router(taxonomy.router)
router.include_router(logs)
