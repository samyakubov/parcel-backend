from pydantic import BaseModel, field_validator
from typing import Optional, List
import pandas as pd
import numpy as np


class CreateAPIKeyResponse(BaseModel):
    """Response model for creating a new API key."""
    id: int
    key: str
    name: str
    enabled: bool
    created_at: str


class APIKeyListItem(BaseModel):
    """Response model for listing an API key."""
    id: int
    name: str
    enabled: bool
    created_at: str
    updated_at: str
    last_used_at: Optional[str]


class UpdateAPIKeyRequest(BaseModel):
    """Request model for updating an API key."""
    name: Optional[str] = None
    enabled: Optional[bool] = None

class MessageResponse(BaseModel):
    """Response model for a simple message."""
    message: str


class PropertyRecord(BaseModel):
    documentid: str
    bbl: str
    amount: float
    prop_borough: int
    prop_block: int
    prop_lot: int
    prop_unit: Optional[str] = None
    prop_streetnumber: str
    prop_streetname: str
    prop_partiallot: Optional[str] = None
    prop_type: str
    party_borough: Optional[str] = None
    partytype_desc: Optional[str] = None
    party_name: str
    party_address1: Optional[str] = None
    party_address2: Optional[str] = None
    party_country: Optional[str] = None
    party_city: Optional[str] = None
    party_state: Optional[str] = None
    party_zip: Optional[str] = None
    doc_type: Optional[str] = None
    record_filed: str

    @field_validator('record_filed', mode='before')
    @classmethod
    def convert_timestamp(cls, v):
        """Convert pandas Timestamp to string"""
        if isinstance(v, pd.Timestamp):
            return v.strftime('%Y-%m-%d')
        return v


class LastSold(BaseModel):
    """Response model for a last sold message."""
    last_sold_price: int
    last_sold_date: str  # Changed from Timestamp to str
    year_built: Optional[int] = None
    land_sqft: Optional[int] = None
    gross_sqft: Optional[int] = None

    @field_validator('last_sold_date', mode='before')
    @classmethod
    def convert_timestamp(cls, v):
        """Convert pandas Timestamp to string"""
        if isinstance(v, pd.Timestamp):
            return v.strftime('%Y-%m-%d')
        return v

    @field_validator('year_built', 'land_sqft', 'gross_sqft', mode='before')
    @classmethod
    def convert_numpy_int(cls, v):
        """Convert numpy int32 to Python int"""
        if isinstance(v, (np.integer, np.int32, np.int64)):
            return int(v)
        return v


class Owners(BaseModel):
    """Response model for listing owners."""
    current_owners: List[str]
    previous_owners: List[str]


class Violation(BaseModel):
    """
    Represents a building code or housing violation issued by a regulatory authority.

    Attributes:
        bbl: Borough-Block-Lot identifier for the property
        violation_status: Current status of the violation (e.g., open, closed, dismissed)
        issue_date: Date when the violation was issued
        violation_type: Category or type of the violation
        description: Detailed description of the violation
        severity: Severity level of the violation (e.g., minor, major, critical)
        penalty_amount: Total monetary penalty assessed for the violation
        amount_paid: Amount of penalty that has been paid
        balance_due: Remaining balance owed on the penalty
        respondent_name: Name of the person or entity responsible for the violation
        house_number: Street number of the property
        street: Street name of the property
        city: City where the property is located
        zip: ZIP code of the property
    """
    bbl: str
    violation_status: str
    issue_date: str
    violation_type: str
    description: str
    severity: str
    penalty_amount: float
    amount_paid: float
    balance_due: float
    respondent_name: str
    house_number: str
    street: str
    city: str
    zip: str

    @field_validator('issue_date', mode='before')
    @classmethod
    def convert_timestamp(cls, v):
        """Convert pandas Timestamp to string"""
        if isinstance(v, pd.Timestamp):
            return v.strftime('%Y-%m-%d')
        return v


class Complaint(BaseModel):
    """
    Represents a complaint filed with the Department of Buildings or similar authority.

    Attributes:
        complaint_number: Unique identifier for the complaint
        bin: Building Identification Number
        special_district: Special zoning or regulatory district designation
        complaint_category: Category or type of complaint filed
        disposition_date: Date when the complaint was resolved or closed
        disposition_code: Code indicating how the complaint was resolved
        inspection_date: Date when an inspection was conducted
        dobrun_date: Date of Department of Buildings run or processing
        status: Current status of the complaint (e.g., pending, resolved, closed)
    """
    complaint_number: int
    bin: str
    special_district: Optional[str] = None  # Made optional (was None in logs)
    complaint_category: str
    disposition_date: str
    disposition_code: str
    inspection_date: str
    dobrun_date: Optional[str] = None  # Made optional (was nan in logs)
    status: str

    @field_validator('dobrun_date', mode='before')
    @classmethod
    def convert_nan(cls, v):
        """Convert NaN to None"""
        if pd.isna(v):
            return None
        return v


class JobFiled(BaseModel):
    """
    Represents a construction or building job filing with regulatory authorities.

    Attributes:
        job_description: Description of the work to be performed
        bin: Building Identification Number
        applicant_first_name: First name of the person filing the job application
        applicant_last_name: Last name of the person filing the job application
        applicant_professional_title: Professional title or license type of the applicant
            (e.g., architect, engineer, contractor)
    """
    job_description: str
    bin: str
    applicant_first_name: str
    applicant_last_name: str
    applicant_professional_title: str
    job_status: str
    job_type: str


class Zoning(BaseModel):
    """
    Represents zoning information for a property or area.

    Attributes:
        zoning_districts: List of zoning district designations (e.g., R1, C2, M1)
        commercial_overlays: List of commercial overlay districts that apply
        special_districts: List of special purpose zoning districts
        limited_height_district: Designation for height restriction districts, if applicable
        last_updated: Date when the zoning information was last updated
    """
    zoning_districts: List[str]
    commercial_overlays: List[str]
    special_districts: List[str]
    limited_height_district: Optional[str] = None
    last_updated: str


class Coordinates(BaseModel):
    """
    Represents geographic coordinates for a location.

    Attributes:
        latitude: Latitude coordinate in decimal degrees
        longitude: Longitude coordinate in decimal degrees
    """
    latitude: float
    longitude: float


class PropertyDetailsResponse(BaseModel):
    """Response model for a single property's details."""
    last_sold: Optional[LastSold] = None
    owners: Owners
    records: List[PropertyRecord]
    job_filings: List[JobFiled]
    violations: List[Violation]
    complaints: List[Complaint]
    zoning: Optional[Zoning] = None
    coordinates: Optional[Coordinates] = None