from fastmcp import FastMCP
import os
import requests
from functools import lru_cache
from starlette.responses import PlainTextResponse
from starlette.requests import Request

mcp = FastMCP(name="DataServer")

CORE_URL = "https://s3.us-east-2.amazonaws.com/viktor-llm.txt/viktor-core-llm.txt"
GEOMETRY_VIEW = "https://s3.us-east-2.amazonaws.com/viktor-llm.txt/viktor-geometry-view.txt"
STAAD_PRO_WORKER = "https://s3.us-east-2.amazonaws.com/viktor-llm.txt/viktor-staad-pro-worker.txt"
UPLOAD_PROCESS_EXCEL_FILES = "https://s3.us-east-2.amazonaws.com/viktor-llm.txt/viktor-upload_process_excel_files.txt"
INPUTS = "https://s3.us-east-2.amazonaws.com/viktor-llm.txt/viktor-parametrization-inputs.txt"
STYLING = "https://s3.us-east-2.amazonaws.com/viktor-llm.txt/viktor-styling.txt"
TABLE_VIEW = "https://s3.us-east-2.amazonaws.com/viktor-llm.txt/viktor-table-data-view.txt"
AEC_DATA_Model = "https://s3.us-east-2.amazonaws.com/viktor-llm.txt/aec_data_model_autodesk_api.txt"
IFC_OPEN_SHELL = "https://s3.us-east-2.amazonaws.com/viktor-llm.txt/viktor-ifcOpenShell.txt"

_session = requests.Session()

@lru_cache(maxsize=None)
def _fetch(url: str) -> str:
    return _session.get(url, timeout=20).text

@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> PlainTextResponse:
    return PlainTextResponse("OK")

@mcp.tool(name="ViktorCore", description="Reference sheet for VIKTOR core functions. Run This Tool Always First")
def core() -> str:
    return (
        "Based on this context, now use <ParametrizationInputs>, then <AppStyling>. "
        "From the following content, decide which output to use and pick a tool to get more information about that visualization. "
        "Fetch the relevant guidelines before coding: "
        "use <TableView/DataView> for tabular data, <GeometryView> for 3D geometry, "
        "and <UploadProcessExcelFiles> for Excel/data ingestion. For structural analysis, use <StaadProWorker>.\n\n"
        f"{_fetch(CORE_URL)}"
    )

@mcp.tool(name="GeometryView", description="Reference information for VIKTOR geometry view functions")
def get_geometry_view_reference() -> str:
    return _fetch(GEOMETRY_VIEW)

@mcp.tool(name="TableView-DataView", description="Reference info for vkt.TableView/vkt.DataView")
def get_table_view_reference() -> str:
    return _fetch(TABLE_VIEW)

@mcp.tool(name="StaadProWorker", description="Reference info and examples for STAAD.Pro worker integration")
def get_staad_pro_worker_reference() -> str:
    return _fetch(STAAD_PRO_WORKER)

@mcp.tool(name="UploadProcessExcelFiles", description="Reference sheet for uploading and processing Excel files")
def get_upload_process_excel_files_reference() -> str:
    return _fetch(UPLOAD_PROCESS_EXCEL_FILES)

@mcp.tool(name="ParametrizationInputs", description="Run second after ViktorCore")
def get_parametrization_inputs_reference() -> str:
    return _fetch(INPUTS)

@mcp.tool(name="AppStyling", description="Run third after ParametrizationInputs")
def get_app_styling() -> str:
    return _fetch(STYLING)

@mcp.tool(name="AECDataModel", description="Context for Autodesk ACC AEC data model")
def get_autodesk_aec_data_model() -> str:
    return _fetch(AEC_DATA_Model)

@mcp.tool(name="IfcOpenShell", description="Reference info for IfcOpenShell")
def get_ifc_open_shell_reference() -> str:
    return _fetch(IFC_OPEN_SHELL)

if __name__ == "__main__":
    host = os.getenv("MCP_HOST", "127.0.0.1")
    port = int(os.getenv("MCP_PORT", "8000"))
    mcp.run(transport="sse", host=host, port=port)
