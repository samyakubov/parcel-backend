from langchain_core.tools import tool

from database_connector import DatabaseConnector
from endpoint_handlers.property_search.search_by_property_address import (
    search_by_property_address,
)
from endpoint_handlers.property_search.search_by_property_bbl import (
    search_by_property_bbl,
)
from services.ai.summarizer import create_summary_from_property_data


def get_tools(db: DatabaseConnector):
    @tool
    def lookup_property_by_address(address: str):
        """
        Search for property details using its address.
        Useful for finding owners, violations, zoning, and other usage details for a specific address.
        """
        try:
            result = search_by_property_address(address, db)
            summary = create_summary_from_property_data(result)
            return {"summary": str(summary), "full_data": result}
        except Exception as e:
            return f"Error searching for property: {str(e)}"

    @tool
    def lookup_property_by_bbl(bbl: str):
        """
        Search for property details using its BBL (Borough-Block-Lot).
        BBL is a unique identifier for NYC properties. Format is usually a 10-digit string.
        Useful when the user provides a BBL directly.
        """
        try:
            result = search_by_property_bbl(bbl, db)
            summary = create_summary_from_property_data(result)
            return {"summary": str(summary), "full_data": result}
        except Exception as e:
            return f"Error searching for property by BBL: {str(e)}"

    return [lookup_property_by_address, lookup_property_by_bbl]
