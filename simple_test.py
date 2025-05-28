#!/usr/bin/env python3
"""Simple test to validate ACE v2 core functionality."""

from ace_v2_enhanced import ACEv2

def test_basic_functionality():
    print("🧪 Testing ACE v2 basic functionality...")
    
    # Initialize ACE v2
    ace = ACEv2(workspace='test_workspace_v2')
    
    # Create a simple project with improved prompt
    project_id = ace.create_project(
        'Calculator Functions', 
        'Create Python functions for basic calculator operations: add, subtract, multiply, divide, with input validation and error handling'
    )
    print(f"✅ Project created: {project_id}")
    
    # List projects
    projects = ace.list_projects()
    print(f"📋 Projects: {projects}")
    
    # Get project status
    status = ace.get_project_status(project_id)
    print(f"📊 Project status: {status['project']['status']}")
    print(f"📊 Total tasks: {len(status['project']['tasks'])}")
    
    # Show some task details
    project = ace.projects[project_id]
    print(f"\n📝 Generated tasks:")
    for i, task in enumerate(project.tasks[:5]):  # Show first 5 tasks
        print(f"  {i+1}. [{task.category}] {task.description}")
    
    print("\n✅ Basic functionality test completed!")

if __name__ == "__main__":
    test_basic_functionality() 