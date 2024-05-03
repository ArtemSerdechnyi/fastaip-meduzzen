from uuid import UUID

from app.db.models import (
    CompanyRequestStatus,
    CompanyRole,
    User,
    UserRequestStatus,
)
from app.repositories.company_member import CompanyMemberRepository
from app.repositories.company_request import CompanyRequestRepository
from app.repositories.user_request import UserRequestRepository
from app.schemas.company_member import (
    CompanyMemberDetailResponseScheme,
    ListNestedCompanyMemberDetailResponseScheme,
    NestedCompanyMemberDetailResponseScheme,
)
from app.schemas.company_request import (
    CompanyRequestCreateScheme,
    CompanyRequestDetailResponseScheme,
    CompanyRequestListDetailResponseScheme,
)
from app.schemas.user_request import UserRequestDetailResponseScheme
from app.services.base import Service
from app.utils.validators import CompanyValidator


class CompanyActionService(Service):
    validator: CompanyValidator = CompanyValidator()

    def __init__(self, session):
        self.company_request_repository = CompanyRequestRepository(session)
        self.user_request_repository = UserRequestRepository(session)
        self.company_member_repository = CompanyMemberRepository(session)
        super().__init__(session)

    @validator.validate_check_user_not_in_company
    @validator.validate_company_request_non_existing
    @validator.validate_user_exist_and_active_by_user_id
    @validator.validate_company_id_by_owner
    async def create_company_request(
        self, user_id: UUID, company_id: UUID, owner: User
    ) -> CompanyRequestDetailResponseScheme:
        scheme = CompanyRequestCreateScheme(
            user_id=user_id, company_id=company_id
        )
        company_request = (
            self.company_request_repository.create_company_request(
                scheme=scheme
            )
        )
        return CompanyRequestDetailResponseScheme.from_orm(company_request)

    @validator.validate_company_owner_by_company_request_id
    async def remove_company_request(self, request_id: UUID, owner: User):
        company_request = (
            await self.company_request_repository.inactive_company_request(
                request_id=request_id
            )
        )
        return CompanyRequestDetailResponseScheme.from_orm(company_request)

    @validator.validate_user_exist_and_active_by_user_id
    @validator.validate_company_id_by_owner
    async def remove_user_from_company(
        self, user_id: UUID, company_id: UUID, owner: User
    ) -> CompanyMemberDetailResponseScheme:
        company_member = (
            await self.company_member_repository.remove_user_from_company(
                company_id=company_id, user_id=user_id
            )
        )
        return CompanyMemberDetailResponseScheme.from_orm(company_member)

    async def get_company_members(
        self,
        company_id: UUID,
        page: int,
        limit: int,
        role: str = None,
    ) -> ListNestedCompanyMemberDetailResponseScheme:
        raw_members = await self.company_member_repository.get_members_list_by_attributes(
            company_id=company_id, page=page, limit=limit, role=role
        )
        members = [
            NestedCompanyMemberDetailResponseScheme.from_orm(m)
            for m in raw_members
        ]
        return ListNestedCompanyMemberDetailResponseScheme(members=members)

    @validator.validate_company_id_by_owner
    async def get_company_users_request(
        self,
        company_id: UUID,
        owner: User,
        page: int,
        limit: int,
        status: str = None,
    ) -> CompanyRequestListDetailResponseScheme:
        raw_user_requests = await self.user_request_repository.get_user_requests_list_by_attributes(
            page=page, limit=limit, status=status, company_id=company_id
        )
        requests = [
            CompanyRequestDetailResponseScheme.from_orm(request)
            for request in raw_user_requests
        ]
        return CompanyRequestListDetailResponseScheme(requests=requests)

    @validator.validate_user_request_by_request_id
    @validator.validate_company_owner_by_user_request_id
    async def confirm_user_request(
        self, request_id: UUID, owner: User
    ) -> CompanyMemberDetailResponseScheme:
        accept_status = UserRequestStatus.accepted.value
        user_request = (
            await self.user_request_repository.update_user_request_status(
                request_id=request_id, status=accept_status
            )
        )
        raw_member = await self.company_member_repository.add_user_to_company(
            company_id=user_request.company_id, user_id=user_request.user_id
        )
        return CompanyMemberDetailResponseScheme.from_orm(raw_member)

    @validator.validate_user_request_by_request_id
    @validator.validate_company_owner_by_user_request_id
    async def deny_user_request(
        self, request_id: UUID, owner: User
    ) -> UserRequestDetailResponseScheme:
        deny_status = CompanyRequestStatus.denied.value
        user_request = (
            await self.user_request_repository.update_user_request_status(
                request_id=request_id, status=deny_status
            )
        )
        return UserRequestDetailResponseScheme.from_orm(user_request)

    @validator.validate_check_user_in_company
    @validator.validate_user_exist_and_active_by_user_id
    @validator.validate_company_id_by_owner
    async def appoint_administrator(
        self, company_id: UUID, user_id: UUID, owner: User
    ) -> CompanyMemberDetailResponseScheme:
        admin_role = CompanyRole.admin.value
        raw_member = await self.company_member_repository.change_member_role(
            company_id=company_id, user_id=user_id, role=admin_role
        )
        return CompanyMemberDetailResponseScheme.from_orm(raw_member)
