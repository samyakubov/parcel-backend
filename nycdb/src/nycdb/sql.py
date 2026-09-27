import re


def _column_definition(table_name, field, type_str):
    """
    Postgres `serial` is not a DuckDB type. Replace it with an integer
    that defaults to the next value of a sequence created for that column.
    """
    if "serial" in type_str.lower():
        rest = re.sub(r"serial", "", type_str, count=1, flags=re.IGNORECASE).strip()
        sequence_name = f"{table_name}_{field}_seq"
        column = f"{field} INTEGER"
        if rest:
            column += f" {rest}"
        column += f" DEFAULT nextval('{sequence_name}')"
        return column, f"CREATE SEQUENCE {sequence_name}"

    return f"{field} {type_str}", None


def create_table(table_name, fields) -> str:
    """
    String, Iterable --> String
    """
    sequences = []
    columns = []
    for field, type_str in fields.items():
        column, sequence = _column_definition(table_name, field, type_str)
        if sequence:
            sequences.append(sequence)
        columns.append(column)

    create = f"CREATE TABLE {table_name} (" + ", ".join(columns) + ")"
    if sequences:
        return "; ".join(sequences + [create])
    return create


def drop_table(table_name) -> str:
    """
    String --> String
    """
    return f"DROP TABLE IF EXISTS {table_name}"
