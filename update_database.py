
from sqlalchemy import inspect, text
from app import app, db

with app.app_context():
    existing_columns = {
        column["name"]
        for column in inspect(db.engine).get_columns("users")
    }

    new_columns = {
        "role": "VARCHAR(20) NOT NULL DEFAULT 'viewer'",
        "display_name": "VARCHAR(100)",
        "image_filename": "VARCHAR(255)"
    }

    with db.engine.begin() as connection:
        for column_name, column_type in new_columns.items():
            if column_name not in existing_columns:
                connection.execute(
                    text(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
                )
                print(f"Added column: {column_name}")
            else:
                print(f"Column already exists: {column_name}")

    print("Database update completed!")
