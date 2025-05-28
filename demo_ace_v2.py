#!/usr/bin/env python3
"""
Demo script for ACE v2 - Enhanced Autonomous Coding Environment
This script demonstrates the key improvements and features of ACE v2.
"""

import os
import time
import json
from colorama import Fore, init

# Initialize colorama for colored output
init(autoreset=True)

def demo_ace_v2():
    """Demonstrate ACE v2 capabilities."""
    print(f"{Fore.CYAN}🚀 ACE v2 Demo - Enhanced Autonomous Coding Environment")
    print(f"{Fore.CYAN}=" * 60)
    
    try:
        # Import ACE v2 components
        from ace_v2_enhanced import ACEv2
        
        print(f"{Fore.GREEN}✅ Successfully imported ACE v2 components")
        
        # Initialize ACE v2
        print(f"\n{Fore.BLUE}📋 Initializing ACE v2...")
        ace = ACEv2(model="o4-mini", workspace="demo_workspace")
        
        # Demo 1: Create a simple project
        print(f"\n{Fore.YELLOW}🔨 Demo 1: Creating a simple project")
        project_id = ace.create_project(
            name="Calculator App",
            description="Create a simple calculator application with basic operations (add, subtract, multiply, divide) and error handling"
        )
        print(f"{Fore.GREEN}✅ Project created with ID: {project_id}")
        
        # Show project status
        status = ace.get_project_status(project_id)
        print(f"{Fore.CYAN}📊 Project Status:")
        print(f"  - Total tasks: {len(status['project']['tasks'])}")
        print(f"  - Ready tasks: {status['ready_tasks']}")
        for status_name, count in status['task_breakdown'].items():
            if count > 0:
                print(f"  - {status_name}: {count}")
        
        # Demo 2: Execute project with testing
        print(f"\n{Fore.YELLOW}🚀 Demo 2: Executing project with comprehensive testing")
        results = ace.execute_project(project_id, run_tests=True)
        
        print(f"{Fore.GREEN}✅ Project execution completed!")
        print(f"  - Success rate: {results['summary']['success_rate']:.1%}")
        print(f"  - Completed tasks: {results['summary']['completed_tasks']}")
        print(f"  - Failed tasks: {results['summary']['failed_tasks']}")
        print(f"  - Total phases: {results['summary']['total_phases']}")
        
        # Show test results if available
        if 'test_results' in results:
            test_summary = results['test_results']['summary']
            print(f"\n{Fore.BLUE}🧪 Testing Summary:")
            print(f"  - Total tests: {test_summary['total_tests']}")
            print(f"  - Passed tests: {test_summary['passed_tests']}")
            print(f"  - Test success rate: {test_summary['success_rate']:.1%}")
        
        # Show validation results if available
        if 'validation_results' in results:
            val_summary = results['validation_results']['summary']
            print(f"\n{Fore.MAGENTA}📝 Code Quality Summary:")
            print(f"  - Tasks validated: {val_summary['total_validated']}")
            print(f"  - Excellent quality: {val_summary['excellent']}")
            print(f"  - Good quality: {val_summary['good']}")
            print(f"  - Fair quality: {val_summary['fair']}")
            print(f"  - Poor quality: {val_summary['poor']}")
        
        # Demo 3: Create another project to show task library reuse
        print(f"\n{Fore.YELLOW}🔄 Demo 3: Creating another project to demonstrate task reuse")
        project_id_2 = ace.create_project(
            name="Advanced Calculator",
            description="Create an advanced calculator with scientific functions, memory operations, and a graphical interface"
        )
        
        print(f"{Fore.GREEN}✅ Second project created with ID: {project_id_2}")
        
        # Show task library growth
        print(f"\n{Fore.CYAN}📚 Task Library Status:")
        print(f"  - Total reusable tasks: {len(ace.task_library.tasks)}")
        
        # Demo 4: List all projects
        print(f"\n{Fore.YELLOW}📋 Demo 4: Project management overview")
        projects = ace.list_projects()
        print(f"{Fore.CYAN}All Projects:")
        for project in projects:
            status_color = Fore.GREEN if project["status"] == "completed" else \
                          Fore.BLUE if project["status"] == "in_progress" else Fore.YELLOW
            print(f"{status_color}  {project['id']}: {project['name']} ({project['status']}) - {project['tasks']} tasks")
        
        # Demo 5: Show workspace structure
        print(f"\n{Fore.YELLOW}📁 Demo 5: Workspace structure")
        workspace_path = ace.workspace
        if os.path.exists(workspace_path):
            print(f"{Fore.CYAN}Workspace: {workspace_path}")
            for root, dirs, files in os.walk(workspace_path):
                level = root.replace(workspace_path, '').count(os.sep)
                indent = ' ' * 2 * level
                print(f"{indent}{os.path.basename(root)}/")
                subindent = ' ' * 2 * (level + 1)
                for file in files[:5]:  # Show only first 5 files
                    print(f"{subindent}{file}")
                if len(files) > 5:
                    print(f"{subindent}... and {len(files) - 5} more files")
        
        print(f"\n{Fore.GREEN}🎉 Demo completed successfully!")
        print(f"{Fore.CYAN}Key improvements demonstrated:")
        print(f"  ✅ Modular architecture with reusable components")
        print(f"  ✅ Enhanced error handling and retry mechanisms")
        print(f"  ✅ Comprehensive testing framework")
        print(f"  ✅ Intelligent task library and reuse")
        print(f"  ✅ Advanced dependency management")
        print(f"  ✅ Detailed reporting and quality metrics")
        
    except ImportError as e:
        print(f"{Fore.RED}❌ Import Error: {str(e)}")
        print(f"{Fore.YELLOW}Make sure all required modules are available:")
        print(f"  - base_task_processor.py")
        print(f"  - enhanced_task_management.py")
        print(f"  - ace_testing_framework.py")
        print(f"  - ace_v2_enhanced.py")
        
    except Exception as e:
        print(f"{Fore.RED}❌ Demo Error: {str(e)}")
        print(f"{Fore.YELLOW}This might be due to:")
        print(f"  - Missing OpenAI API key")
        print(f"  - Network connectivity issues")
        print(f"  - Dependencies not installed")

def demo_individual_components():
    """Demonstrate individual components separately."""
    print(f"\n{Fore.CYAN}🔧 Component-level Demo")
    print(f"{Fore.CYAN}=" * 30)
    
    try:
        # Demo BaseTaskProcessor
        print(f"{Fore.YELLOW}1. Base Task Processor Demo")
        from base_task_processor import BaseTaskProcessor, Task
        
        processor = BaseTaskProcessor()
        sample_task = Task(
            id="demo_task_001",
            description="Create a function that calculates the factorial of a number"
        )
        
        print(f"  - Created sample task: {sample_task.description}")
        
        # Validate the task structure
        issues = processor.validate_task(sample_task)
        print(f"  - Validation issues: {len(issues)}")
        
        print(f"{Fore.GREEN}  ✅ BaseTaskProcessor demo completed")
        
        # Demo EnhancedTaskManager
        print(f"\n{Fore.YELLOW}2. Enhanced Task Manager Demo")
        from enhanced_task_management import EnhancedTaskManager
        
        manager = EnhancedTaskManager()
        # This would normally call OpenAI API, so we'll just show the structure
        print(f"  - Enhanced task manager initialized")
        print(f"  - Supports dependency resolution and project estimation")
        print(f"{Fore.GREEN}  ✅ EnhancedTaskManager demo completed")
        
        # Demo Testing Framework
        print(f"\n{Fore.YELLOW}3. Testing Framework Demo")
        from ace_testing_framework import ACETestFramework, TaskValidator
        
        test_framework = ACETestFramework()
        validator = TaskValidator(test_framework)
        
        print(f"  - Test framework initialized")
        print(f"  - Can generate and run tests for any task")
        print(f"  - Includes static code analysis")
        print(f"{Fore.GREEN}  ✅ Testing framework demo completed")
        
    except ImportError as e:
        print(f"{Fore.RED}❌ Component Import Error: {str(e)}")
    except Exception as e:
        print(f"{Fore.RED}❌ Component Demo Error: {str(e)}")

def main():
    """Main demo function."""
    print(f"{Fore.CYAN}🌟 Welcome to ACE v2 Enhanced Autonomous Coding Environment Demo!")
    print(f"{Fore.WHITE}This demo showcases the key improvements in ACE v2:")
    print(f"  • Enhanced error handling and robustness")
    print(f"  • Comprehensive testing framework")
    print(f"  • Advanced dependency management")
    print(f"  • Intelligent task library and reuse")
    print(f"  • Modular, maintainable architecture")
    
    choice = input(f"\n{Fore.GREEN}Choose demo type:\n1. Full ACE v2 demo\n2. Component-level demo\n3. Both\nEnter choice (1-3): ").strip()
    
    if choice in ["1", "3"]:
        demo_ace_v2()
    
    if choice in ["2", "3"]:
        demo_individual_components()
    
    print(f"\n{Fore.CYAN}📖 For more information, see README_v2.md")
    print(f"{Fore.CYAN}🚀 To start using ACE v2: python ace_v2_enhanced.py")

if __name__ == "__main__":
    main() 