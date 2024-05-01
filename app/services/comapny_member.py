from uuid import UUID

from sqlalchemy import and_, insert, update

from app.db.models import CompanyMember
from app.services.base import Service
from app.utils.exceptions.company import CompanyMemberNotFoundException


class CompanyMemberService(Service):
    async def _add_user_to_company(
        self, company_id: UUID, user_id: UUID
    ) -> CompanyMember:
        query = (
            insert(CompanyMember)
            .values(
                company_id=company_id,
                user_id=user_id,
            )
            .returning(CompanyMember)
        )
        result = await self.session.execute(query)
        company_member = result.scalar()
        return company_member

    async def _remove_user_from_company(
        self, company_id: UUID, user_id: UUID
    ) -> CompanyMember:
        query = (
            update(CompanyMember)
            .where(
                and_(
                    CompanyMember.company_id == company_id,
                    CompanyMember.user_id == user_id,
                    CompanyMember.is_active == True,
                )
            )
            .values(is_active=False)
            .returning(CompanyMember)
        )
        result = await self.session.execute(query)
        if company_member := result.scalar():
            return company_member
        raise CompanyMemberNotFoundException(
            company_id=company_id, user_id=user_id
        )
