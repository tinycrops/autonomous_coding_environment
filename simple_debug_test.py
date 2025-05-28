#!/usr/bin/env python3
"""Simple debug test with detailed logging."""

from ace_v2_enhanced import ACEv2

def main():
    print("🔍 Running simple debug test...")
    
    ace = ACEv2(workspace='debug_workspace')
    project_id = ace.create_project('Simple Test', 'Create a function that returns 42')
    print(f'✅ Project created: {project_id}')
    
    print('🚀 Executing project...')
    results = ace.execute_project(project_id, run_tests=False)
    print(f'📊 Results: {results["summary"]["success_rate"]:.1%}')
    
    # Show details of first failed task
    project = ace.projects[project_id]
    failed_tasks = [t for t in project.tasks if t.status == "failed"]
    if failed_tasks:
        task = failed_tasks[0]
        print(f"\n❌ First failed task: {task.description}")
        if task.execution_result:
            print(f"   Return code: {task.execution_result.get('return_code')}")
            print(f"   Error: {task.execution_result.get('error', 'No error')[:200]}")

if __name__ == "__main__":
    main() 