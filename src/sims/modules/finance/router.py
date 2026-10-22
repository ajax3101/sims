import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from sims.core.db import commit, get_session
from sims.core.errors import NotFound
from sims.models import Contract, Payment, PaymentScheduleItem, Student
from sims.modules.academic.views import v_contract_balance
from sims.modules.finance.schemas import ContractIn, ContractPatch, PaymentIn
from sims.modules.students.schemas import ContractOut, PaymentOut
from sims.modules.students.service import contract_out

router = APIRouter(prefix="/api/contracts", tags=["finance"])
Session = Depends(get_session)


async def _contract_out(session: AsyncSession, contract_id: uuid.UUID) -> ContractOut:
    c = await session.scalar(select(Contract).where(Contract.id == contract_id).execution_options(populate_existing=True)
                             .options(selectinload(Contract.schedule), selectinload(Contract.payments)))
    if c is None:
        raise NotFound("contract")
    balance = (await session.execute(select(v_contract_balance).where(v_contract_balance.c.contract_id == c.id))).one()
    return contract_out(c, balance)


@router.post("", response_model=ContractOut, status_code=status.HTTP_201_CREATED)
async def create_contract(data: ContractIn, session: AsyncSession = Session):
    if await session.get(Student, data.student_id) is None:
        raise NotFound("student")
    c = Contract(**data.model_dump(exclude={"schedule"}))
    c.schedule = [PaymentScheduleItem(**s.model_dump()) for s in data.schedule]
    session.add(c)
    await commit(session)
    return await _contract_out(session, c.id)


@router.get("/{contract_id}", response_model=ContractOut)
async def get_contract(contract_id: uuid.UUID, session: AsyncSession = Session):
    return await _contract_out(session, contract_id)


@router.patch("/{contract_id}", response_model=ContractOut)
async def patch_contract(contract_id: uuid.UUID, data: ContractPatch, session: AsyncSession = Session):
    c = await session.get(Contract, contract_id)
    if c is None:
        raise NotFound("contract")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(c, field, value)
    await commit(session)
    return await _contract_out(session, contract_id)


@router.post("/{contract_id}/payments", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
async def add_payment(contract_id: uuid.UUID, data: PaymentIn, session: AsyncSession = Session):
    if await session.get(Contract, contract_id) is None:
        raise NotFound("contract")
    p = Payment(contract_id=contract_id, **data.model_dump())
    session.add(p)
    await commit(session)
    return p
