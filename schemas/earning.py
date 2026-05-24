from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class PayoutMethodBase(BaseModel):
    provider: str
    account_id: str
    is_default: int = 0

class PayoutMethodCreate(PayoutMethodBase):
    pass

class PayoutMethod(PayoutMethodBase):
    id: int
    user_id: int
    class Config:
        from_attributes = True

class WithdrawalRequestBase(BaseModel):
    amount: float

class WithdrawalRequestCreate(WithdrawalRequestBase):
    pass

class WithdrawalRequest(WithdrawalRequestBase):
    id: int
    user_id: int
    status: str
    created_at: datetime
    class Config:
        from_attributes = True
