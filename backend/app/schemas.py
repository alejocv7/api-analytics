from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class MetricBase(BaseModel):
    project_id: str
    url_path: str
    method: str
    response_status_code: int
    response_time_ms: float
    user_agent: Optional[str] = None
    ip_hash: Optional[str] = None


class MetricCreate(MetricBase):
    pass


class MetricInDBBase(MetricBase):
    id: int
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)


class Metric(MetricInDBBase):
    pass
