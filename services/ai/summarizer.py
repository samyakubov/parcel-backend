from typing import Any

from pydantic_models import PropertyDetailsResponse


def create_summary_from_property_data(property_data: PropertyDetailsResponse) -> dict[str, Any]:
    """
    Creates a summary dictionary from the property data object.
    This summary is used to provide concise information to the language model.
    """
    if not property_data:
        return {}

    summary = {
        "owners": property_data.owners.model_dump() if property_data.owners else None,
        "last_sold": property_data.last_sold.model_dump() if property_data.last_sold else None,
        "zoning": property_data.zoning.model_dump() if property_data.zoning else None,
        "mortgage": property_data.mortgage.model_dump() if property_data.mortgage else None,
        "violation_count": len(property_data.violations) if property_data.violations else 0,
        "complaint_count": len(property_data.complaints) if property_data.complaints else 0,
        "job_filing_count": len(property_data.job_filings) if property_data.job_filings else 0,
        "latest_violation": property_data.violations[0].model_dump() if property_data.violations else None,
        "latest_record": property_data.records[0].model_dump() if property_data.records else None,
    }
    return summary
