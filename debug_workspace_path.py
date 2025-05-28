#!/usr/bin/env python3
"""Debug workspace path construction."""

import os
from ace_v2_enhanced import ACEv2

def main():
    print("🔍 Debugging workspace path...")
    
    ace = ACEv2(workspace='debug_workspace')
    print(f"ACE workspace: {ace.workspace}")
    
    project_id = ace.create_project('Test', 'Simple function')
    print(f"Project ID: {project_id}")
    
    # Check what the project workspace should be
    expected_workspace = os.path.join(ace.workspace, "projects", project_id)
    print(f"Expected project workspace: {expected_workspace}")
    
    # Check if it exists
    print(f"Workspace exists: {os.path.exists(expected_workspace)}")
    
    # List what's in the projects directory
    projects_dir = os.path.join(ace.workspace, "projects")
    if os.path.exists(projects_dir):
        print(f"Projects directory contents: {os.listdir(projects_dir)}")

if __name__ == "__main__":
    main() 