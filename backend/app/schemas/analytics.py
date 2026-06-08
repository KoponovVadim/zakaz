from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class DirectSummary(BaseModel):
    cost: Decimal = Decimal("0")
    clicks: int = 0
    impressions: int = 0
    rsform_leads: int = 0
    virtuemart_orders: int = 0
    total_requests: int = 0
    revenue: Decimal = Decimal("0")


class DirectDailyRow(DirectSummary):
    date: date


class DirectSiteRow(DirectSummary):
    client: str
    site: str
