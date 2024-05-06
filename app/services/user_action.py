from uuid import UUID

from app.db.models import (
    CompanyRequestStatus,
    User,
)
from app.repositories.company_member import CompanyMemberRepository
from app.repositories.company_request import CompanyRequestRepository
from app.repositories.user_request import UserRequestRepository
from app.schemas.company_member import CompanyMemberDetailResponseScheme
from app.schemas.company_request import (
    CompanyRequestDetailResponseScheme,
    CompanyRequestListDetailResponseScheme,
)
from app.schemas.user_request import (
    UserRequestCreateScheme,
    UserRequestDetailResponseScheme,
    UserRequestListDetailResponseScheme,
)
from app.services.base import Service
from app.utils.validators.user import UserValidator


class UserActionService(Service):
    validator = UserValidator()

    def __init__(self, session):
        self.company_request_repository = CompanyRequestRepository(session)
        self.user_request_repository = UserRequestRepository(session)
        self.company_member_repository = CompanyMemberRepository(session)
        super().__init__(session)

    @validator.validate_check_user_not_in_company
    @validator.validate_user_request_non_existing
    @validator.validate_exist_company_is_active
    async def create_user_request(
        self, company_id: UUID, user: User
    ) -> UserRequestDetailResponseScheme:
        scheme = UserRequestCreateScheme(
            company_id=company_id, user_id=user.user_id
        )
        user_request = await self.user_request_repository.create_user_request(
            scheme=scheme
        )
        return UserRequestDetailResponseScheme.from_orm(user_request)

    async def cancel_user_request(self, request_id: UUID, user: User):
        user_request = (
            await self.user_request_repository.inactive_user_request(
                request_id=request_id, user_id=user.user_id
            )
        )
        return UserRequestDetailResponseScheme.from_orm(user_request)

    async def list_user_requests(self, user: User, page: int, limit: int):
        raw_requests = await self.user_request_repository.get_user_requests_list_by_attributes(
            page=page, limit=limit, user_id=user.user_id
        )
        requests = [
            UserRequestDetailResponseScheme.from_orm(request)
            for request in raw_requests
        ]
        return UserRequestListDetailResponseScheme(requests=requests)

    async def list_company_requests_for_user(
        self, user: User, page: int, limit: int
    ):
        raw_invitations = await self.company_request_repository.get_company_requests_list_by_attributes(
            page=page, limit=limit, user_id=user.user_id
        )
        invitations = [
            CompanyRequestDetailResponseScheme.from_orm(invitation)
            for invitation in raw_invitations
        ]
        return CompanyRequestListDetailResponseScheme(requests=invitations)

    @validator.validate_company_invitation
    async def accept_company_request(
        self, request_id: UUID, user: User
    ) -> CompanyMemberDetailResponseScheme:
        accept_status = CompanyRequestStatus.accepted.value
        company_request = await self.company_request_repository.update_company_request_status(
            request_id=request_id, status=accept_status
        )
        raw_member = await self.company_member_repository.add_user_to_company(
            company_id=company_request.company_id, user_id=user.user_id
        )
        return CompanyMemberDetailResponseScheme.from_orm(raw_member)

    @validator.validate_company_invitation
    async def reject_invitation(self, request_id: UUID, user: User):
        denied_status = CompanyRequestStatus.denied.value
        user_request = await self.company_request_repository.update_company_request_status(
            request_id=request_id, status=denied_status
        )
        return CompanyRequestDetailResponseScheme.from_orm(user_request)

    @validator.validate_user_leave_from_company
    async def leave_company(self, company_id: UUID, user: User):
        company_member = (
            await self.company_member_repository.remove_user_from_company(
                company_id=company_id, user_id=user.user_id
            )
        )
        return CompanyMemberDetailResponseScheme.from_orm(company_member)
