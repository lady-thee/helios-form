from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.services import (
    create_form_service, 
    get_forms_service, 
    update_form_service,
    submit_form_service,
    get_submissions_service
)
from app.schema import (
    FormCreateRequest,
    FormUpdateRequest,
    FormSubmissionRequest
)

router = APIRouter(
    prefix="/api",
    tags=["api"]
)


@router.post("/forms", status_code=201, description="Create a new form")
async def create_form(body: FormCreateRequest):
    response = await create_form_service(body)
    return JSONResponse(
        content={
            "message": "Form created successfully",
            "form": response.model_dump(mode="json")
        }, 
        status_code=201
    )

@router.get("/forms")
async def get_form():
    response = await get_forms_service()
    response_data = [form.model_dump(mode="json") for form in response]
    return JSONResponse(
        content={
            "message": "Record retrieved successfully",
            "form": response_data
        }, 
        status_code=200
    )

@router.put("/forms/{form_id}")
async def update_form(form_id: str, body: FormUpdateRequest):
    response = await update_form_service(form_id, body)
    return JSONResponse(
        content={
            "message": f"Form {form_id} updated successfully",
            "form": response.model_dump(mode="json")
        }, 
        status_code=200
    )

@router.post("/forms/{form_id}/submit")
async def submit_form(form_id: str, body: FormSubmissionRequest):
    response = await submit_form_service(form_id, body)
    return JSONResponse(
        content={
            "message": f"Form {form_id} submitted successfully",
            "submission": response.model_dump(mode="json")
        }, 
        status_code=201
    )

@router.get("/forms/{form_id}/submissions")
async def get_submissions(form_id: str):
    response = await get_submissions_service(form_id)
    return JSONResponse(
        content={
            "message": "Submissions retrieved successfully",
            "submissions": [submission.model_dump(mode="json") for submission in response]
        }, 
        status_code=200
    )