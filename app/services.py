from app.models import (Forms, FormVersion, Schema, Submission)
from app.schema import (
    FormCreateRequest, 
    FormUpdateRequest, 
    FormSubmissionRequest, 
    FormCreateResponse, 
    FormResponse, 
    UpdateFormResponse, 
    SubmissionResponse
)
from app.db_config import init_db
from app.validators import (
    validate_schema, 
    compute_changelog, 
    validate_submission,
    evaluate_computed_fields,
    normalize_submission,
)
from beanie import PydanticObjectId
from fastapi import HTTPException
from typing import List


async def create_form_service(data: FormCreateRequest):
    """
    Validates the form schema and creates a new form along with its initial version.
    If the schema is invalid, raises an HTTPException with status code 422 and details of
    """
    errors = validate_schema(data.form_schema)
    if errors:
        raise HTTPException(status_code=422, detail=errors)

    form = Forms(name=data.name, description=data.description)
    await form.insert()
    
    form_version = FormVersion(
        form_id=str(form.id), 
        version_number=1, 
        form_schema=data.form_schema
    )
    await form_version.insert()
    
    form.latest_version_id = str(form_version.id)
    await form.save()
    
    return FormCreateResponse(
        id=str(form.id),
        name=form.name,
        description=form.description,
        created_at=form.created_at,
        version_id=str(form_version.id),
        version_number=form_version.version_number
    )


async def get_forms_service() -> List[FormResponse]:
    """
    Retrieves all forms from the database and returns them as a list of FormResponse objects.
    """
    forms = await Forms.find_all().to_list()
    response = []
    for form in forms:
        latest_version = await FormVersion.find_one(FormVersion.id == form.latest_version_id)
        response.append(FormResponse(
            id=str(form.id),
            name=form.name,
            description=form.description,
            created_at=str(form.created_at),
            latest_version_id=str(form.latest_version_id) if form.latest_version_id else None,
            latest_version_number=latest_version.version_number if latest_version else 0
        ))
    return response


async def update_form_service(form_id: str, data: FormUpdateRequest):
    """
    Validates the updated form schema and creates a new version of the form.
    If the schema is invalid, raises an HTTPException with status code 422 and details of
    """
    form = await Forms.get(form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")

    changelog = None
    
    # only update name/description if provided
    if data.name is not None:
        form.name = data.name
    if data.description is not None:
        form.description = data.description

    # only create a new version if schema was provided
    if data.form_schema is not None:
        errors = validate_schema(data.form_schema)
        if errors:
            raise HTTPException(status_code=422, detail=errors)

        latest_version = await FormVersion.get(form.latest_version_id)
        if not latest_version:
            raise HTTPException(status_code=404, detail="Form version not found")

        latest_version = await FormVersion.get(PydanticObjectId(form.latest_version_id))
        new_version_number = (latest_version.version_number + 1) if latest_version else 1
        
        changelog = compute_changelog(latest_version.form_schema if latest_version else Schema(fields=[]), data.form_schema)

        form_version = FormVersion(
            form_id=form_id, 
            version_number=new_version_number, 
            form_schema=data.form_schema
        )
        await form_version.insert()
        form.latest_version_id = str(form_version.id)
    
    await form.save()
    
    return UpdateFormResponse(
        id=str(form.id),
        name=form.name,
        description=form.description,
        created_at=str(form.created_at),
        version_id=str(form.latest_version_id) if form.latest_version_id else None,
        version_number=form_version.version_number + 1 if data.form_schema else None,
        changelog=changelog
    )


async def submit_form_service(form_id: str, data: FormSubmissionRequest):
    """
    Validates the submitted data against the form schema and creates a new submission.
    If the form or its latest version is not found, raises an HTTPException with status code 404.
    If the submitted data is invalid, raises an HTTPException with status code 422 and details of
    """
    form = await Forms.get(form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")

    form_version = await FormVersion.get(PydanticObjectId(form.latest_version_id))
    if not form_version:
        raise HTTPException(status_code=404, detail="Form version not found")

    errors = validate_submission(data.data, form_version.form_schema)
    if errors:
        raise HTTPException(status_code=422, detail=errors)

    evaluated_data = evaluate_computed_fields(data.data, form_version.form_schema)

    submission = Submission(
        form_id=form_id,
        version_id=str(form_version.id),
        data=evaluated_data
    )
    await submission.insert()

    return SubmissionResponse(
        id=str(submission.id),
        form_id=submission.form_id,
        version_id=submission.version_id,
        data=submission.data,
        submitted_at=submission.submitted_at
    )

async def get_submissions_service(form_id: str) -> List[SubmissionResponse]:
    """
    Retrieves all submissions for a given form and returns them as a list of SubmissionResponse objects.
    If the form is not found, raises an HTTPException with status code 404.
    """
    form = await Forms.get(PydanticObjectId(form_id))
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")

    latest_version = await FormVersion.get(PydanticObjectId(form.latest_version_id))
    if not latest_version:
        raise HTTPException(status_code=404, detail="Form version not found")
    
    latest_field_names = [field.name for field in latest_version.form_schema.fields]

    submissions = await Submission.find(Submission.form_id == form_id).to_list()

    return [SubmissionResponse(
        id=str(submission.id),
        form_id=submission.form_id,
        version_id=submission.version_id,
        data=normalize_submission(submission.data, latest_field_names),
        submitted_at=submission.submitted_at
    ) for submission in submissions]

