from fastmcp import FastMCP
import requests

mcp = FastMCP(name="DataServer")


CORE_URL = "https://s3.us-east-2.amazonaws.com/viktor-llm.txt/viktor-core-llm.txt"
GEOMETRY_VIEW = "https://s3.us-east-2.amazonaws.com/viktor-llm.txt/viktor-geometry-view.txt"
STAAD_PRO_WORKER = "https://s3.us-east-2.amazonaws.com/viktor-llm.txt/viktor-staad-pro-worker.txt"
UPLOAD_PROCESS_EXCEL_FILES = "https://s3.us-east-2.amazonaws.com/viktor-llm.txt/viktor-upload_process_excel_files.txt"
INPUTS = "https://s3.us-east-2.amazonaws.com/viktor-llm.txt/viktor-parametrization-inputs.txt"
STYLING = "https://s3.us-east-2.amazonaws.com/viktor-llm.txt/viktor-styling.txt"
STYLE_URL = STYLING
TABLE_VIEW = "https://s3.us-east-2.amazonaws.com/viktor-llm.txt/viktor-table-data-view.txt"
AEC_DATA_Model = "https://s3.us-east-2.amazonaws.com/viktor-llm.txt/aec_data_model_autodesk_api.txt"
IFC_OPEN_SHELL = "https://s3.us-east-2.amazonaws.com/viktor-llm.txt/viktor-ifcOpenShell.txt"
@mcp.tool(
    name="ViktorCore",
    description="Reference sheet for VIKTOR core functions. Run This Tool Always First",
)
def core() -> str:
    """Return the core reference file."""
    return (
    "Based on this context, now use <ParametrizationInputs>, then <AppStyling>. "
    "From the following content, decide which output to use and pick a tool to get more information about that visualization. "
    "Fetch the relevant guidelines before coding: "
    "use <TableView/DataView> for tabular data, <GeometryView> for 3D geometry, "
    "and <UploadProcessExcelFiles> for Excel/data ingestion. For structural analysis, use <StaadProWorker>.\n\n"
        f"{requests.get(CORE_URL, timeout=10).text}"
    )

@mcp.tool(
    name="GeometryView",
    description="Reference information for VIKTOR geometry view functions",
)
def get_geometry_view_reference() -> str:
    """Return the geometry view reference file."""
    return requests.get(GEOMETRY_VIEW, timeout=10).text

@mcp.tool(
    name="TableView-DataView",
    description="If the application displays results in tabular form, it is required to use this tool for reference information and guidelines (vkt.TableView, vkt.DataView)",
)
def get_table_view_reference() -> str:
    return requests.get(TABLE_VIEW, timeout=10).text

@mcp.tool(
    name="StaadProWorker",
    description="Reference information and examples for STAAD.Pro worker integration",
)
def get_staad_pro_worker_reference() -> str:
    """Return the STAAD.Pro worker reference file."""
    return requests.get(STAAD_PRO_WORKER, timeout=10).text

@mcp.tool(
    name="UploadProcessExcelFiles",
    description="Reference sheet for uploading and processing Excel files",
)
def get_upload_process_excel_files_reference() -> str:
    """Return the upload/process Excel files reference file."""
    return requests.get(UPLOAD_PROCESS_EXCEL_FILES, timeout=10).text

@mcp.tool(
    name="ParametrizationInputs",
    description="Run This Tool Always Second after ViktorCore and use this information to correctly use the input element for the viktor app, following this tools use AppStyling",
)
def get_parametrization_inputs_reference() -> str:
    """Return the parametrization inputs reference file."""
    return requests.get(INPUTS, timeout=10).text

@mcp.tool(
    name="AppStyling",
    description="Run This Tool Always Third after ParametrizationInputs to get guidelines on how to add application title and descriptions in the Parametrization, use before ParametrizationInputs",
)
def get_app_styling() -> str:
    """Return styling guidelines for application title and description."""
    return requests.get(STYLE_URL, timeout=10).text


@mcp.tool(
    name="AECDataModel",
    description=(
        "Context for Autodesk Construction Cloud (ACC) AEC data model: helps selecting files from "
        "ACC, querying and operating on model data (properties, types, families), and creating "
        "quantity takeoffs based on the provided content."
    ),
)
def get_autodesk_aec_data_model() -> str:
    """Return the Autodesk AEC data model reference file."""
    return requests.get(AEC_DATA_Model, timeout=10).text


@mcp.tool(
    name="IfcOpenShell",
    description=(
        "Reference information and examples for IfcOpenShell: authoring, editing, "
        "reading, and analysis workflows with ifcopenshell API usage patterns."
    ),
)
def get_ifc_open_shell_reference() -> str:
    """Return the IfcOpenShell reference file."""
    return requests.get(IFC_OPEN_SHELL, timeout=10).text



if __name__ == "__main__":
    mcp.run()
