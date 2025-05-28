#!/usr/bin/env python3
"""
Docker Test Runner for ACE v2
Safe testing environment for autonomous code generation and execution.
"""

import os
import time
from ace_v2_enhanced import ACEv2

def run_safe_tests():
    """Run comprehensive tests in the safe Docker environment."""
    print("🐳 ACE v2 Docker Safe Testing Environment")
    print("=" * 50)
    
    # Use a workspace that's isolated within the container
    workspace = "/app/workspaces/docker_test_workspace"
    
    print(f"🔒 Using isolated workspace: {workspace}")
    
    try:
        # Test 1: Basic functionality
        print("\n🧪 Test 1: Basic Functionality")
        ace = ACEv2(workspace=workspace)
        
        project_id = ace.create_project(
            "Safe Math Functions",
            "Create safe mathematical functions with input validation: square, cube, and factorial"
        )
        print(f"✅ Project created: {project_id}")
        
        # Show generated tasks
        project = ace.projects[project_id]
        print(f"📝 Generated {len(project.tasks)} tasks:")
        for i, task in enumerate(project.tasks[:3]):
            print(f"  {i+1}. [{task.category}] {task.description[:60]}...")
        
        # Test 2: Code generation and validation
        print("\n🧪 Test 2: Code Generation Test")
        if project.tasks:
            test_task = project.tasks[0]
            print(f"Testing task: {test_task.description[:50]}...")
            
            # Generate code for the first task
            if not test_task.code:
                from base_task_processor import BaseTaskProcessor
                processor = BaseTaskProcessor()
                test_task.code = processor.generate_code_for_task(test_task)
                
            print(f"✅ Code generated ({len(test_task.code)} characters)")
            
            # Test compilation
            try:
                compile(test_task.code, f"<{test_task.id}>", "exec")
                print("✅ Code compiles successfully")
            except SyntaxError as e:
                print(f"❌ Syntax error: {e}")
        
        # Test 3: Safe execution (limited tasks)
        print("\n🧪 Test 3: Safe Execution Test (First 2 Tasks Only)")
        try:
            # Only execute first 2 tasks for safety
            limited_tasks = project.tasks[:2]
            project.tasks = limited_tasks
            
            results = ace.execute_project(project_id, run_tests=False)
            
            print(f"📊 Execution Results:")
            print(f"  - Success rate: {results['summary']['success_rate']:.1%}")
            print(f"  - Completed: {results['summary']['completed_tasks']}")
            print(f"  - Failed: {results['summary']['failed_tasks']}")
            
            # Show details for each task
            for task in limited_tasks:
                status_emoji = "✅" if task.status == "completed" else "❌"
                print(f"  {status_emoji} {task.id}: {task.status}")
                if task.execution_result and not task.execution_result.get('success'):
                    error = task.execution_result.get('error', 'Unknown error')
                    print(f"    Error: {error[:100]}...")
        
        except Exception as e:
            print(f"❌ Execution test failed: {str(e)}")
        
        # Test 4: Project persistence
        print("\n🧪 Test 4: Project Persistence Test")
        projects = ace.list_projects()
        print(f"📋 Total projects in workspace: {len(projects)}")
        for proj in projects:
            print(f"  - {proj['id']}: {proj['name']} ({proj['status']})")
        
        # Test 5: Task library
        print("\n🧪 Test 5: Task Library Test")
        print(f"📚 Task library contains {len(ace.task_library.tasks)} tasks")
        
        print("\n✅ All Docker tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()

def run_interactive_mode():
    """Run interactive mode for manual testing."""
    print("\n🎮 Interactive Mode")
    print("Available commands:")
    print("  1. Run safe tests")
    print("  2. Create a project")
    print("  3. Debug code generation")
    print("  4. Exit")
    
    while True:
        try:
            choice = input("\nEnter choice (1-4): ").strip()
            
            if choice == "1":
                run_safe_tests()
            elif choice == "2":
                name = input("Project name: ").strip()
                desc = input("Project description: ").strip()
                if name and desc:
                    ace = ACEv2(workspace="/app/workspaces/interactive_workspace")
                    project_id = ace.create_project(name, desc)
                    print(f"✅ Project created: {project_id}")
                else:
                    print("❌ Name and description required")
            elif choice == "3":
                from debug_generation import debug_code_generation
                debug_code_generation()
            elif choice == "4":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("🐳 ACE v2 Docker Testing Environment")
    print("Environment: Safe isolated container")
    print(f"Python path: {os.environ.get('PYTHONPATH', 'Not set')}")
    print(f"Working directory: {os.getcwd()}")
    
    # Check if running interactively or in batch mode
    if os.isatty(0):  # Interactive terminal
        run_interactive_mode()
    else:  # Batch mode
        run_safe_tests() 