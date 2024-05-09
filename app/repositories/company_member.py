from typing import Sequence
from uuid import UUID

from sqlalchemy import and_, insert, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.db.models import Company, CompanyMember, User
from app.utils.exceptions.company import CompanyMemberNotFoundException


class CompanyMemberRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_member_by_attributes(
        self,
        is_active: bool = True,
        **kwargs,
    ) -> CompanyMember:
        kwargs.update(is_active=is_active)

        query = select(CompanyMember).where(
            *(
                getattr(CompanyMember, attr) == value
                for attr, value in kwargs.items()
            )
        )
        result = await self.session.execute(query)
        if member := result.scalar():
            return member
        raise CompanyMemberNotFoundException(**kwargs)

    async def get_members_list_by_attributes(
        self,
        company_id: UUID,
        page: int,
        limit: int,
        role: str = None,
        **kwargs,
    ) -> list[CompanyMember]:
        query = (
            select(CompanyMember, Company, User)
            .join(User, CompanyMember.user_id == User.user_id)
            .join(Company, CompanyMember.company_id == Company.company_id)
            .options(
                joinedload(CompanyMember.user),
                joinedload(CompanyMember.company),
            )
            .where(
                and_(
                    CompanyMember.company_id == company_id,
                    CompanyMember.is_active == True,
                )
            )
        )
        query = query.limit(limit).offset(
            page - 1 if page == 1 else (page - 1) * limit
        )

        if role is not None:
            query = query.where(CompanyMember.role == role)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def remove_user_from_company(
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

    async def add_user_to_company(
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

    async def change_member_role(
        self, company_id: UUID, user_id: UUID, role: str
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
            .values(role=role)
            .returning(CompanyMember)
        )
        result = await self.session.execute(query)
        if company_member := result.scalar():
            return company_member
        raise CompanyMemberNotFoundException(
            company_id=company_id, user_id=user_id
        )

    async def get_user_id_company_members(self, company_id: UUID) -> Sequence:
        query = select(CompanyMember.user_id).where(
            and_(
                CompanyMember.company_id == company_id,
                CompanyMember.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalars().all()
