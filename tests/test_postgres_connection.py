"""
Safe PostgreSQL Database Connection Test
Executes SELECT 1 against PostgreSQL cosmetic_verification_db via SQLAlchemy.
"""

import sys
from pathlib import Path
from sqlalchemy import text

BASE_DIR = Path(__file__).parent.parent.resolve()
SITE_PACKAGES_DIR = BASE_DIR / "ai-service" / "venv" / "Lib" / "site-packages"

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if SITE_PACKAGES_DIR.exists() and str(SITE_PACKAGES_DIR) not in sys.path:
    sys.path.insert(0, str(SITE_PACKAGES_DIR))

from database.connection import engine, get_masked_database_url

def test_postgres_connection():
    print("=" * 80)
    print("TESTING POSTGRESQL DATABASE CONNECTION")
    print("=" * 80)
    print(f"Target Database URL: {get_masked_database_url()}")

    # 1. Establish connection from engine
    connection = engine.connect()
    print("  Status: SQLAlchemy Connection Established.")

    try:
        # 2. Execute SELECT 1
        result = connection.execute(text("SELECT 1;")).scalar()
        assert result == 1, "Expected SELECT 1 to return 1"
        print("  Status: Query Execution 'SELECT 1;' Succeeded -> Result: 1")

        # 3. Check PostgreSQL database name & server version
        if engine.dialect.name == "postgresql":
            db_name = connection.execute(text("SELECT current_database();")).scalar()
            print(f"  Status: Connected PostgreSQL Database -> '{db_name}'")
            version_str = connection.execute(text("SELECT version();")).scalar()
            print(f"  Status: PostgreSQL Server Version -> '{version_str[:50]}...'")
        else:
            print(f"  Status: Dialect '{engine.dialect.name}' active.")

        print("-" * 80)
        print("POSTGRESQL CONNECTION TEST PASSED SUCCESSFULLY!")
        print("=" * 80)
    finally:
        # 4. Verify connection closes cleanly
        connection.close()
        engine.dispose()
        print("  Status: Connection & Engine Disposed Cleanly.")

if __name__ == "__main__":
    test_postgres_connection()
