import logging
from typing import Optional, List

from pydantic import BaseModel
from open_webui.models.organizations import (
    Organizations,
    OrganizationForm,
    OrganizationUpdateForm,
    OrganizationResponse,
)

from open_webui.constants import ERROR_MESSAGES
from fastapi import APIRouter, Depends, HTTPException, status

from open_webui.utils.auth import get_admin_user, get_verified_user
from open_webui.env import SRC_LOG_LEVELS


log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MAIN"])

router = APIRouter()

############################
# GetOrganizations
############################


@router.get("/", response_model=List[OrganizationResponse])
async def get_organizations(user=Depends(get_admin_user)):
    """Get all organizations (admin only)"""
    return Organizations.get_organizations()


############################
# CreateNewOrganization
############################


@router.post("/create", response_model=Optional[OrganizationResponse])
async def create_new_organization(
    form_data: OrganizationForm, user=Depends(get_admin_user)
):
    """Create a new organization (admin only)"""
    try:
        organization = Organizations.insert_new_organization(form_data)
        if organization:
            return organization
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("Error creating organization"),
            )
    except ValueError as ve:
        log.exception(f"Validation error creating organization: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except Exception as e:
        log.exception(f"Error creating a new organization: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(e),
        )


############################
# GetOrganizationById
############################


@router.get("/id/{id}", response_model=Optional[OrganizationResponse])
async def get_organization_by_id(id: str, user=Depends(get_admin_user)):
    """Get organization by ID (admin only)"""
    organization = Organizations.get_organization_by_id(id)
    if organization:
        return organization
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )


############################
# GetOrganizationByCode
############################


@router.get("/code/{org_code}", response_model=Optional[OrganizationResponse])
async def get_organization_by_code(org_code: str, user=Depends(get_admin_user)):
    """Get organization by code (admin only)"""
    organization = Organizations.get_organization_by_code(org_code)
    if organization:
        return organization
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )


############################
# UpdateOrganizationById
############################


@router.post("/id/{id}/update", response_model=Optional[OrganizationResponse])
async def update_organization_by_id(
    id: str, form_data: OrganizationUpdateForm, user=Depends(get_admin_user)
):
    """Update organization by ID (admin only)"""
    try:
        organization = Organizations.update_organization_by_id(id, form_data)
        if organization:
            return organization
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("Error updating organization"),
            )
    except ValueError as ve:
        log.exception(f"Validation error updating organization: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except Exception as e:
        log.exception(f"Error updating organization {id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(e),
        )


############################
# AddUsersToOrganization
############################


class UserIdsForm(BaseModel):
    user_ids: List[str]


@router.post("/id/{id}/users/add", response_model=Optional[OrganizationResponse])
async def add_users_to_organization(
    id: str, form_data: UserIdsForm, user=Depends(get_admin_user)
):
    """Add users to organization (admin only)"""
    try:
        organization = Organizations.add_users_to_organization(id, form_data.user_ids)
        if organization:
            return organization
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("Error adding users to organization"),
            )
    except Exception as e:
        log.exception(f"Error adding users to organization {id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(e),
        )


############################
# RemoveUsersFromOrganization
############################


@router.post("/id/{id}/users/remove", response_model=Optional[OrganizationResponse])
async def remove_users_from_organization(
    id: str, form_data: UserIdsForm, user=Depends(get_admin_user)
):
    """Remove users from organization (admin only)"""
    try:
        organization = Organizations.remove_users_from_organization(
            id, form_data.user_ids
        )
        if organization:
            return organization
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("Error removing users from organization"),
            )
    except Exception as e:
        log.exception(f"Error removing users from organization {id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(e),
        )


############################
# AddPlansToOrganization
############################


class PlanIdsForm(BaseModel):
    plan_ids: List[str]


@router.post("/id/{id}/plans/add", response_model=Optional[OrganizationResponse])
async def add_plans_to_organization(
    id: str, form_data: PlanIdsForm, user=Depends(get_admin_user)
):
    """Add subscription plans to organization (admin only)"""
    try:
        organization = Organizations.add_plans_to_organization(id, form_data.plan_ids)
        if organization:
            return organization
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("Error adding plans to organization"),
            )
    except Exception as e:
        log.exception(f"Error adding plans to organization {id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(e),
        )


############################
# RemovePlansFromOrganization
############################


@router.post("/id/{id}/plans/remove", response_model=Optional[OrganizationResponse])
async def remove_plans_from_organization(
    id: str, form_data: PlanIdsForm, user=Depends(get_admin_user)
):
    """Remove subscription plans from organization (admin only)"""
    try:
        organization = Organizations.remove_plans_from_organization(
            id, form_data.plan_ids
        )
        if organization:
            return organization
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT(
                    "Error removing plans from organization"
                ),
            )
    except Exception as e:
        log.exception(f"Error removing plans from organization {id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(e),
        )


############################
# DeleteOrganizationById
############################


@router.delete("/id/{id}/delete", response_model=bool)
async def delete_organization_by_id(id: str, user=Depends(get_admin_user)):
    """Delete organization by ID (admin only)"""
    try:
        result = Organizations.delete_organization_by_id(id)
        if result:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT("Error deleting organization"),
            )
    except Exception as e:
        log.exception(f"Error deleting organization {id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(e),
        )


############################
# Public Organization Signup Endpoints
############################


@router.get("/public/code/{org_code}", response_model=Optional[dict])
async def get_organization_signup_info(org_code: str):
    """Get organization info for signup page (public endpoint)"""
    try:
        organization = Organizations.get_organization_by_code(org_code)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )
        
        if not organization.signup_enabled or organization.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Signup is not available for this organization",
            )
        
        # Return organization info without sensitive data
        return {
            "id": organization.id,
            "org_name": organization.org_name,
            "org_code": organization.org_code,
            "plans": organization.plans or []
        }
    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"Error getting organization signup info: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(e),
        )
