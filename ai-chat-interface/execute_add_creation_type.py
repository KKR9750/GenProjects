#!/usr/bin/env python3
"""Add creation_type column to projects table"""

import sys
sys.path.append('.')

from database import get_db_connection

def add_creation_type_column():
    """Add creation_type column to distinguish template vs dynamic projects"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Add column
        cursor.execute("""
            ALTER TABLE projects
            ADD COLUMN IF NOT EXISTS creation_type VARCHAR(20) DEFAULT 'template';
        """)

        # Update existing projects
        cursor.execute("""
            UPDATE projects
            SET creation_type = 'template'
            WHERE creation_type IS NULL;
        """)

        conn.commit()
        print("✅ Successfully added creation_type column to projects table")
        print("   - Column added with default value 'template'")
        print("   - Existing projects updated to 'template' type")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error adding creation_type column: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    add_creation_type_column()
