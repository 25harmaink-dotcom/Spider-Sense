from sqlalchemy import inspect, text
from app.database import engine

TABLE_NAME = "status_history"

NEW_COLUMNS = {
    "previous_hash": "VARCHAR(64)",
    "event_hash": "VARCHAR(64)",
    "event_hmac": "VARCHAR(64)",
}


def migrate():
    inspector = inspect(engine)

    if TABLE_NAME not in inspector.get_table_names():
        raise RuntimeError("status_history table does not exist.")

    existing_columns = {
        column["name"]
        for column in inspector.get_columns(TABLE_NAME)
    }

    with engine.begin() as connection:
        for column_name, column_type in NEW_COLUMNS.items():

            if column_name in existing_columns:
                print(f"Already exists: {column_name}")
                continue

            connection.execute(
                text(
                    f"ALTER TABLE {TABLE_NAME} "
                    f"ADD COLUMN {column_name} {column_type}"
                )
            )

            print(f"Added: {column_name}")

    print("Migration completed successfully!")


if __name__ == "__main__":
    migrate()