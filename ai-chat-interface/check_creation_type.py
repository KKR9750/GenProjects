#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check and add creation_type column using Supabase API
"""

import os
import sys
from supabase import create_client, Client

# UTF-8 출력 설정
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def check_creation_type():
    """Check if creation_type column exists"""

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")

    if not supabase_key:
        print("ERROR: SUPABASE_ANON_KEY environment variable not set")
        print("Set it with: set SUPABASE_ANON_KEY=your_key_here")
        return

    print(f"Supabase URL: {supabase_url}")

    try:
        supabase: Client = create_client(supabase_url, supabase_key)

        # Check projects table
        print("\nChecking projects table...")
        result = supabase.table('projects').select('*').limit(1).execute()

        print(f"SUCCESS: Projects table accessible ({len(result.data)} records)")

        if result.data and len(result.data) > 0:
            columns = list(result.data[0].keys())
            print(f"Current columns: {', '.join(columns)}")

            if 'creation_type' in columns:
                print("\nSUCCESS: creation_type column already exists!")

                # Check values
                all_projects = supabase.table('projects').select('project_id, creation_type').execute()
                dynamic = sum(1 for p in all_projects.data if p.get('creation_type') == 'dynamic')
                template = sum(1 for p in all_projects.data if p.get('creation_type') == 'template')
                null = sum(1 for p in all_projects.data if not p.get('creation_type'))

                print(f"  - Dynamic projects: {dynamic}")
                print(f"  - Template projects: {template}")
                print(f"  - NULL projects: {null}")

                if null > 0:
                    print(f"\nUpdating {null} NULL projects to 'template'...")
                    for project in all_projects.data:
                        if not project.get('creation_type'):
                            supabase.table('projects').update({
                                'creation_type': 'template'
                            }).eq('project_id', project['project_id']).execute()
                    print(f"SUCCESS: Updated {null} projects to 'template'")
            else:
                print("\nWARNING: creation_type column does NOT exist")
                print("\nYou need to add it manually in Supabase SQL Editor:")
                print("=" * 60)
                print("""
ALTER TABLE projects
ADD COLUMN creation_type VARCHAR(20) DEFAULT 'template';

UPDATE projects
SET creation_type = 'template'
WHERE creation_type IS NULL;
                """)
                print("=" * 60)
                print("\nSupabase Dashboard:")
                print(f"https://supabase.com/dashboard/project/{supabase_url.split('//')[1].split('.')[0]}/editor")
        else:
            print("WARNING: projects table is empty")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_creation_type()
