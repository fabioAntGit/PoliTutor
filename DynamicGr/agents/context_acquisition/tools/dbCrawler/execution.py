from dataclasses import dataclass
from typing import Any, Dict

from sqlalchemy import create_engine, inspect, text


@dataclass
class ConnectionInfo:
    engine: Any
    inspector: Any
    db_type: str


connections: Dict[str, ConnectionInfo] = {}


def create_db_connection(
    connection_alias: str,
    connection_url: str,
    db_type: str,
) -> dict:
    global connections

    try:
        supported_dbs = ["mysql", "mariadb", "postgresql"]
        if db_type not in supported_dbs:
            return {
                "status": "error",
                "message": f"Unsupported db_type. Use: {', '.join(supported_dbs)}",
            }

        engine = create_engine(connection_url, echo=False)

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        inspector = inspect(engine)

        connections[connection_alias] = ConnectionInfo(
            engine, inspector, db_type)

        return {
            "status": "success",
            "connection_alias": connection_alias,
            "db_type": db_type,
            "message": f"Connection '{connection_alias}' created successfully",
        }

    except Exception as error:
        return {"status": "error", "message": f"Connection failed: {str(error)}"}


def get_relational_schema(connection_alias: str) -> dict:
    global connections

    conn_info = connections.get(connection_alias)
    if not conn_info:
        return {
            "status": "error",
            "message": f"Connection '{connection_alias}' not found. Create it first.",
        }

    try:
        inspector = conn_info.inspector
        tables_info = []

        schemas = inspector.get_schema_names()
        main_schema = schemas[0] if schemas else None

        if not main_schema:
            return {"status": "error", "message": "No schemas found"}

        table_names = inspector.get_table_names(schema=main_schema)
        view_names = inspector.get_view_names(schema=main_schema)
        all_tables = table_names + view_names

        for table_name in all_tables:
            columns = inspector.get_columns(table_name, schema=main_schema)
            column_info = [
                {
                    "name": col["name"],
                    "type": str(col["type"]),
                    "nullable": col.get("nullable", True),
                    "primary_key": False,
                }
                for col in columns
            ]

            pk_constraint = inspector.get_pk_constraint(
                table_name, schema=main_schema)
            if pk_constraint:
                pk_columns = pk_constraint["constrained_columns"]
                for col_info in column_info:
                    if col_info["name"] in pk_columns:
                        col_info["primary_key"] = True

            foreign_keys = inspector.get_foreign_keys(
                table_name, schema=main_schema)
            relationships = []
            for fk in foreign_keys:
                relationships.append(
                    {
                        "source_table": table_name,
                        "source_columns": fk.get("constrained_columns", []),
                        "target_schema": fk.get("referred_schema", main_schema),
                        "target_table": fk.get("referred_table"),
                        "target_columns": fk.get("referred_columns", []),
                    }
                )

            tables_info.append(
                {
                    "schema": main_schema,
                    "name": table_name,
                    "type": "view" if table_name in view_names else "table",
                    "columns": column_info,
                    "relationships": relationships,
                }
            )

        return {
            "status": "success",
            "connection_alias": connection_alias,
            "schema": main_schema,
            "tables": tables_info,
            "total_tables": len(all_tables),
        }

    except Exception as error:
        return {
            "status": "error",
            "message": f"Schema extraction failed: {str(error)}",
        }


def get_table_permissions(connection_alias: str) -> dict:
    global connections

    conn_info = connections.get(connection_alias)
    if not conn_info:
        return {
            "status": "error",
            "message": f"Connection '{connection_alias}' not found.",
        }

    try:
        engine = conn_info.engine
        inspector = conn_info.inspector
        schemas = inspector.get_schema_names()
        main_schema = schemas[0] if schemas else None

        if not main_schema:
            return {"status": "error", "message": "No schemas found"}

        table_permissions: Dict[str, Dict[str, list[str]]] = {}

        with engine.connect() as conn:
            query = """
                SELECT
                    TABLE_SCHEMA,
                    TABLE_NAME,
                    GRANTEE as role,
                    PRIVILEGE_TYPE as action
                FROM information_schema.table_privileges
                WHERE TABLE_SCHEMA = :schema
            """

            result = conn.execute(
                text(query), {"schema": main_schema}).fetchall()

            for _schema, table, role, action in result:
                if table not in table_permissions:
                    table_permissions[table] = {}
                if role not in table_permissions[table]:
                    table_permissions[table][role] = []

                if action not in table_permissions[table][role]:
                    table_permissions[table][role].append(action)

        context_permissions = []
        for table_name, roles in table_permissions.items():
            table_entry = {"name": table_name, "roles_permissions": []}

            for role, actions in roles.items():
                table_entry["roles_permissions"].append(
                    {
                        "role": role,
                        "allowed_actions": sorted(actions),
                    }
                )

            context_permissions.append(table_entry)

        return {
            "status": "success",
            "connection_alias": connection_alias,
            "schema": main_schema,
            "table_permissions": table_permissions,
            "company_context_format": context_permissions,
        }

    except Exception as error:
        return {
            "status": "error",
            "message": f"Permissions extraction failed: {str(error)}",
        }


def extract_relational_db_context(connection_alias: str, connection_url: str, db_type: str) -> dict:
    connection_result = create_db_connection(
        connection_alias, connection_url, db_type)

    schema_result = {
        "status": "error",
        "message": "Schema extraction skipped: connection failed",
    }
    permissions_result = {
        "status": "error",
        "message": "Permissions extraction skipped: connection failed",
    }

    if connection_result.get("status") == "success":
        resolved_alias = connection_result.get("connection_alias")
        schema_result = get_relational_schema(resolved_alias)
        permissions_result = get_table_permissions(resolved_alias)

    all_success = all(
        result.get("status") == "success"
        for result in [connection_result, schema_result, permissions_result]
    )

    return {
        "status": "success" if all_success else "error",
        "connection_result": connection_result,
        "schema_result": schema_result,
        "permissions_result": permissions_result,
    }


def execute(params: Dict[str, Any]) -> dict:
    connection_alias = params.get("connection_alias", "default_connection")
    connection_url = params.get("connection_url")
    db_type = params.get("db_type")

    return extract_relational_db_context(connection_alias, connection_url, db_type)


if __name__ == "__main__":
    # Example usage
    params = {
        "connection_alias": "my_db",
        "connection_url": "mysql+pymysql://admin:admin@localhost:3306/autoDb",
        "db_type": "mysql",
    }
    result = execute(params)
    print(result)
