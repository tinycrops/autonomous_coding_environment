#!/usr/bin/env python3
"""Test project execution with improved task generation."""

from ace_v2_enhanced import ACEv2

def test_execution():
    print("🚀 Testing ACE v2 project execution...")
    
    # Initialize ACE v2
    ace = ACEv2(workspace='execution_test_workspace')
    
    # Create a simple project
    project_id = ace.create_project(
        'Basic Math', 
        'Create a simple function that calculates the square of a number with error handling'
    )
    print(f"✅ Project created: {project_id}")
    
    # Show the tasks
    project = ace.projects[project_id]
    print(f"\n📝 Tasks to execute:")
    for i, task in enumerate(project.tasks):
        print(f"  {i+1}. [{task.category}] {task.description}")
    
    # Execute the project without tests first (faster)
    print(f"\n🚀 Executing project without tests...")
    try:
        results = ace.execute_project(project_id, run_tests=False)
        
        print(f"\n✅ Execution results:")
        print(f"  - Success rate: {results['summary']['success_rate']:.1%}")
        print(f"  - Completed tasks: {results['summary']['completed_tasks']}")
        print(f"  - Failed tasks: {results['summary']['failed_tasks']}")
        print(f"  - Total phases: {results['summary']['total_phases']}")
        
        # Show some successful tasks
        successful_tasks = [task for task in project.tasks if task.status == "completed"]
        if successful_tasks:
            print(f"\n✅ Successfully completed tasks:")
            for task in successful_tasks[:3]:  # Show first 3
                print(f"  - {task.description[:60]}...")
        
        failed_tasks = [task for task in project.tasks if task.status == "failed"]
        if failed_tasks:
            print(f"\n❌ Failed tasks:")
            for task in failed_tasks[:3]:  # Show first 3
                print(f"  - {task.description[:60]}...")
                if task.execution_result:
                    error = task.execution_result.get('error', 'Unknown error')
                    print(f"    Error: {error[:100]}...")
    
    except Exception as e:
        print(f"❌ Execution failed: {str(e)}")
    
    print("\n✅ Execution test completed!")

if __name__ == "__main__":
    test_execution() 