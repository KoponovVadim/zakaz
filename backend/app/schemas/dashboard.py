from pydantic import BaseModel


class DashboardSummary(BaseModel):
    clients: int
    sites: int
    active_sites: int
    orders: int
    new_orders: int
