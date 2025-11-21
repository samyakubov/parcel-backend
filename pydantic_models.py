from dataclasses import dataclass
from datetime import datetime
import numpy as np
import pandas as pd
from pydantic import BaseModel, field_validator


@dataclass
class APIKeyConfig:
    """Represents the configuration of an API key.

    Attributes:
        id (int): The unique identifier of the API key.
        key (str): The API key string.
        name (str): The name associated with the API key.
        enabled (bool): Whether the API key is enabled.
        created_at (datetime): The timestamp when the API key was created.
        updated_at (datetime): The timestamp when the API key was last updated.
        last_used_at (Optional[datetime]): The timestamp when the API key was last used.
    """
    id: int
    key: str
    name: str
    enabled: bool
    created_at: datetime
    updated_at: datetime
    last_used_at: datetime | None


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
    last_used_at: str | None


class UpdateAPIKeyRequest(BaseModel):
    """Request model for updating an API key."""
    name: str | None = None
    enabled: bool | None = None


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
    prop_unit: str | None = None
    prop_streetnumber: str
    prop_streetname: str
    prop_partiallot: str | None = None
    prop_type: str | None = None
    party_borough: str | None = None
    partytype_desc: str | None = None
    party_name: str
    party_address1: str | None = None
    party_address2: str | None = None
    party_country: str | None = None
    party_city: str | None = None
    party_state: str | None = None
    party_zip: str | None = None
    doc_type: str | None = None
    record_filed: str

    @field_validator("record_filed", mode="before")
    @classmethod
    def convert_timestamp(cls, v):
        """Convert pandas Timestamp to string"""
        if isinstance(v, pd.Timestamp):
            return v.strftime("%Y-%m-%d")
        return v


class LastSold(BaseModel):
    """Response model for a last sold message."""

    last_sold_price: int
    last_sold_date: str  # Changed from Timestamp to str
    year_built: int | None = None
    land_sqft: int | None = None
    gross_sqft: int | None = None

    @field_validator("last_sold_date", mode="before")
    @classmethod
    def convert_timestamp(cls, v):
        """Convert pandas Timestamp to string"""
        if isinstance(v, pd.Timestamp):
            return v.strftime("%Y-%m-%d")
        return v

    @field_validator("year_built", "land_sqft", "gross_sqft", mode="before")
    @classmethod
    def convert_numpy_int(cls, v):
        """Convert numpy int32 to Python int"""
        if isinstance(v, (np.integer, np.int32, np.int64)):
            return int(v)
        return v


class Owners(BaseModel):
    """Response model for listing owners."""

    current_owners: list[str]
    previous_owners: list[str]


class Violation(BaseModel):
    """
    Represents a building code or housing violation issued by a regulatory authority.

    Attributes:
        bbl: Borough-Block-Lot identifier for the property
        violation_status: Current status of the violation
            (e.g., open, closed, dismissed)
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
    description: str | None = None
    severity: str
    penalty_amount: float
    amount_paid: float
    balance_due: float
    respondent_name: str | None = None
    house_number: str | None = None
    street: str | None = None
    city: str | None = None
    zip: str | None = None

    @field_validator("issue_date", mode="before")
    @classmethod
    def convert_timestamp(cls, v):
        """Convert pandas Timestamp to string"""
        if isinstance(v, pd.Timestamp):
            return v.strftime("%Y-%m-%d")
        return v

    @field_validator("penalty_amount", "amount_paid", "balance_due", mode="before")
    @classmethod
    def convert_empty_string_to_zero(cls, v):
        """Convert empty strings to 0.0 for numeric fields"""
        if v == "" or v is None or (isinstance(v, float) and pd.isna(v)):
            return 0.0
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

    complaint_number: int | None = None
    bin: str
    special_district: str | None = None
    complaint_category: str
    disposition_date: str | None = None
    disposition_code: str | None = None
    inspection_date: str | None = None
    dobrun_date: str | None = None
    status: str

    @field_validator("complaint_number", mode="before")
    @classmethod
    def convert_nan_complaint_number(cls, v):
        """Convert NaN to None for complaint_number"""
        if pd.isna(v):
            return None
        return v

    @field_validator("disposition_date", "inspection_date", "dobrun_date", mode="before")
    @classmethod
    def convert_nan_to_none(cls, v):
        """Convert NaN to None for date fields"""
        if pd.isna(v):
            return None
        return v


class JobFiled(BaseModel):
    """
    Represents a construction or building job filing with regulatory authorities.

    Attributes:
        job_description: Description of the work to be performed
        bin: Building Identification Number
        applicant_first_name: First name of the person filing
            the job application
        applicant_last_name: Last name of the person filing
            the job application
        applicant_professional_title: Professional title or license type
            of the applicant (e.g., architect, engineer, contractor)
    """

    job_description: str | None = None
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
        zoning_districts: List of zoning district designations
            (e.g., R1, C2, M1)
        commercial_overlays: List of commercial overlay districts
            that apply
        special_districts: List of special purpose zoning districts
        limited_height_district: Designation for height restriction
            districts, if applicable
        last_updated: Date when the zoning information was last updated
    """

    zoning_districts: list[str]
    commercial_overlays: list[str]
    special_districts: list[str]
    limited_height_district: str | None = None
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

    last_sold: LastSold | None = None
    owners: Owners
    records: list[PropertyRecord]
    job_filings: list[JobFiled]
    violations: list[Violation]
    complaints: list[Complaint]
    zoning: Zoning | None = None
    coordinates: Coordinates | None = None


class PartyContact(BaseModel):
    """Contact information for a party."""

    addresses: list[str] = []  # Unique addresses from ACRIS records
    phone_numbers: list[str] = []  # From DOB jobs
    business_names: list[str] = []  # From DOB jobs


class PropertyOwnership(BaseModel):
    """Property ownership record for a party."""

    bbl: str
    address: str
    role: str  # GRANTOR/SELLER, GRANTEE/BUYER, etc.
    doc_type: str  # DEED, MORTGAGE, etc.
    amount: int | None = None
    date: str  # record_filed date


class CoParty(BaseModel):
    """Co-party information (people on same documents)."""

    name: str
    shared_document_count: int
    relationship_types: list[str] = []


class PersonProfile(BaseModel):
    """Profile for a distinct individual (grouped by address)."""

    identifier: str  # Unique address or "Unknown-{index}"
    primary_address: str | None = None  # The address used to identify this person
    record_count: int  # Total number of records for this person
    records: list[PropertyRecord] = []
    violations: list[Violation] = []
    contact_info: PartyContact | None = None
    properties: list[PropertyOwnership] = []
    co_parties: list[CoParty] = []


class PartySearchResponse(BaseModel):
    """Response model for searching by party name."""

    total_persons_found: int
    persons: list[PersonProfile]
