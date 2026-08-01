from pydantic import BaseModel
from typing import Optional


class Certificate(BaseModel):
    id: str                    # slug, e.g. "aws-solutions-architect"
    title: str                 # "AWS Certified Solutions Architect"
    issuer: str                # "Amazon Web Services"
    date: str                  # "2025-03" (YYYY-MM or YYYY-MM-DD)
    category: str = "General"  # used for filter pills, e.g. "Cloud", "Security"
    filename: str              # PDF filename inside /certificates
    credential_id: Optional[str] = None   # the issuer's certificate/serial number
    credential_url: Optional[str] = None  # public verification link, if any
    skills: list[str] = []                 # tags shown on the card
