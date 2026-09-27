"""
Each function in this file is the name of a table or dataset.
"""

import itertools
import logging

from .annual_sales import AnnualSales
from .transform import skip_fields, to_csv, with_bbl


def ecb_violations(dataset):
    return with_bbl(to_csv(dataset.files[0].dest), borough="boro")


def dob_violations(dataset):
    return with_bbl(to_csv(dataset.files[0].dest), borough="boro")


def pluto_latest(dataset):
    pluto_generator = to_csv(dataset.files[0].dest, header_replacements={"taxblock": "block", "taxlot": "lot"})
    pluto_fields_to_skip = dataset.schemas[0].get("skip")

    if pluto_fields_to_skip:
        pluto_generator = skip_fields(pluto_generator, [s.lower() for s in pluto_fields_to_skip])

    for line in pluto_generator:
        if line["bbl"] is None:
            logging.info(f"skipping pluto row without bbl: {line}")
        else:
            yield line


def dob_complaints(dataset):
    return to_csv(dataset.files[0].dest)


def dof_sales(dataset):
    return with_bbl(to_csv(dataset.files[0].dest))


def dobjobs(dataset):
    # Open Data renamed the GIS columns. The table still uses the old names.
    return with_bbl(
        to_csv(
            dataset.files[0].dest,
            header_replacements={
                "latitude": "gislatitude",
                "longitude": "gislongitude",
                "councildistrict": "giscouncildistrict",
                "censustract": "giscensustract",
                "nta": "gisntaname",
            },
        )
    )


def dob_now_jobs(dataset):
    # Work-type columns are now named "Standpipe (Work Type)" and similar.
    return with_bbl(
        skip_fields(
            to_csv(
                dataset.files[1].dest,
                header_replacements={
                    "standpipeworktype": "standpipe",
                    "antennaworktype": "antenna",
                    "signworktype": "sign",
                    "curbcutworktype": "curbcut",
                    "fenceworktype": "fence",
                    "scaffoldworktype": "scaffold",
                    "shedworktype": "shed",
                },
            ),
            [s.lower() for s in dataset.schemas[1]["skip"]],
        )
    )


def acris(dataset, schema):
    dest_file = next(filter(lambda f: schema["table_name"] in f.dest, dataset.files))
    _to_csv = to_csv(dest_file.dest)
    if "skip" in schema:
        return skip_fields(_to_csv, [s.lower() for s in schema["skip"]])
    else:
        return _to_csv


def dof_annual_sales(dataset):
    return itertools.chain(*[with_bbl(AnnualSales(f.dest)) for f in dataset.files])
