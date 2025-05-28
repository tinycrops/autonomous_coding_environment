#!/usr/bin/env python3
"""
ACE v2 - Enhanced Autonomous Coding Environment
Integrates improved error handling, dependency management, testing, and code reusability.
"""

import os
import shutil
import json
import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import logging
from colorama import Fore, Style, init

# Import our enhanced components
from base_task_processor import BaseTaskProcessor, Task, Metadata
from enhanced_task_management import EnhancedTaskManager, EnhancedTask, ProjectOrchestrator
from ace_testing_framework import ACETestFramework, TaskValidator

# Initialize colorama
init(autoreset=True)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Project(BaseModel):
    id: str
    name: str
    description: str
    tasks: List[EnhancedTask] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    status: str = "planning"  # planning, in_progress, completed, failed
    execution_results: Optional[Dict[str, Any]] = None

class TaskLibrary(BaseModel):
    tasks: Dict[str, EnhancedTask] = Field(default_factory=dict)
    
    def add_task(self, task: EnhancedTask):
        """Add a completed task to the library."""
        if task.status == "completed":
            self.tasks[task.id] = task
    
    def find_similar_tasks(self, description: str, threshold: float = 0.7) -> List[EnhancedTask]:
        """Find similar tasks in the library (simplified similarity)."""
        # This could be enhanced with proper semantic similarity
        similar_tasks = []
        description_lower = description.lower()
        
        for task in self.tasks.values():
            task_desc_lower = task.description.lower()
            # Simple keyword-based similarity
            common_words = set(description_lower.split()) & set(task_desc_lower.split())
            similarity = len(common_words) / max(len(description_lower.split()), len(task_desc_lower.split()))
            
            if similarity >= threshold:
                similar_tasks.append(task)
        
        return similar_tasks

class ACEv2:
    """Enhanced Autonomous Coding Environment v2 with comprehensive improvements."""
    
    def __init__(self, model: str = "o4-mini", workspace: str = "ace_v2_workspace"):
        self.model = model
        self.workspace = workspace
        self.projects: Dict[str, Project] = {}
        self.task_library = TaskLibrary()
        
        # Initialize components
        self.base_processor = BaseTaskProcessor(model)
        self.task_manager = EnhancedTaskManager(model)
        self.test_framework = ACETestFramework(model)
        self.task_validator = TaskValidator(self.test_framework)
        self.orchestrator = ProjectOrchestrator(self.task_manager, self.base_processor)
        
        self.setup_workspace()
        self.load_task_library()
        self.load_existing_projects()
        
        logger.info(f"{Fore.CYAN}🚀 ACE v2 initialized with workspace: {workspace}")
    
    def setup_workspace(self):
        """Set up the workspace directory structure."""
        try:
            if os.path.exists(self.workspace):
                # Don't backup if workspace already exists and is valid
                logger.info(f"{Fore.GREEN}📁 Using existing workspace: {self.workspace}")
            else:
                os.makedirs(self.workspace)
                logger.info(f"{Fore.GREEN}✅ Created new workspace: {self.workspace}")
            
            # Ensure subdirectories exist
            for subdir in ["projects", "library", "reports", "tests"]:
                subdir_path = os.path.join(self.workspace, subdir)
                os.makedirs(subdir_path, exist_ok=True)
            
        except Exception as e:
            logger.error(f"{Fore.RED}❌ Error setting up workspace: {str(e)}")
            raise
    
    def create_project(self, name: str, description: str) -> str:
        """Create a new project with enhanced task decomposition."""
        try:
            project_id = f"project_{len(self.projects) + 1:03d}"
            logger.info(f"{Fore.BLUE}📋 Creating project: {name}")
            
            # Create project
            project = Project(
                id=project_id,
                name=name,
                description=description
            )
            
            # Decompose into tasks
            tasks = self.task_manager.decompose_project_to_tasks(name, description)
            
            # Check task library for similar tasks
            enhanced_tasks = []
            for task in tasks:
                similar_tasks = self.task_library.find_similar_tasks(task.description)
                if similar_tasks:
                    logger.info(f"{Fore.YELLOW}🔍 Found {len(similar_tasks)} similar tasks for: {task.description[:50]}...")
                    # Use the best similar task as a starting point
                    best_similar = similar_tasks[0]
                    task.code = best_similar.code  # Start with existing code
                    task.metadata = best_similar.metadata
                
                enhanced_tasks.append(task)
            
            project.tasks = enhanced_tasks
            self.projects[project_id] = project
            
            # Save project
            self.save_project(project)
            
            logger.info(f"{Fore.GREEN}✅ Project created with {len(enhanced_tasks)} tasks")
            return project_id
            
        except Exception as e:
            logger.error(f"{Fore.RED}❌ Error creating project: {str(e)}")
            raise
    
    def execute_project(self, project_id: str, run_tests: bool = True) -> Dict[str, Any]:
        """Execute a project with comprehensive testing and validation."""
        if project_id not in self.projects:
            raise ValueError(f"Project {project_id} not found")
        
        project = self.projects[project_id]
        project.status = "in_progress"
        
        logger.info(f"{Fore.CYAN}🚀 Executing project: {project.name}")
        
        try:
            # Create project workspace
            project_workspace = os.path.join(self.workspace, "projects", project_id)
            os.makedirs(project_workspace, exist_ok=True)
            
            # Estimate project duration
            duration_estimate = self.task_manager.estimate_project_duration(project.tasks)
            logger.info(f"{Fore.BLUE}⏱️ Estimated duration: {duration_estimate['parallel_estimate_minutes']} minutes ({duration_estimate['estimated_phases']} phases)")
            
            # Execute with dependency management
            execution_results = self.orchestrator.execute_project_with_dependencies(
                project.tasks, project_workspace
            )
            
            # Run tests if requested
            if run_tests:
                logger.info(f"{Fore.BLUE}🧪 Running comprehensive tests...")
                test_results = self.run_project_tests(project, project_workspace)
                execution_results["test_results"] = test_results
            
            # Validate completed tasks
            validation_results = self.validate_project_tasks(project, project_workspace)
            execution_results["validation_results"] = validation_results
            
            # Update task library with successful tasks
            for task in project.tasks:
                if task.status == "completed":
                    self.task_library.add_task(task)
            
            # Update project status
            if execution_results["summary"]["success_rate"] == 1.0:
                project.status = "completed"
            else:
                project.status = "partially_completed"
            
            project.execution_results = execution_results
            
            # Generate comprehensive report
            report = self.generate_project_report(project, execution_results)
            self.save_report(project_id, report)
            
            # Save updated project and library
            self.save_project(project)
            self.save_task_library()
            
            logger.info(f"{Fore.GREEN}✅ Project execution completed with {execution_results['summary']['success_rate']:.1%} success rate")
            return execution_results
            
        except Exception as e:
            logger.error(f"{Fore.RED}❌ Error executing project: {str(e)}")
            project.status = "failed"
            raise
    
    def run_project_tests(self, project: Project, workspace_path: str) -> Dict[str, Any]:
        """Run tests for all completed tasks in the project."""
        test_results = {"task_tests": {}, "summary": {}}
        
        completed_tasks = [task for task in project.tasks if task.status == "completed"]
        
        for task in completed_tasks:
            try:
                # Generate and run tests
                test_suite = self.test_framework.generate_tests_for_task(task)
                if test_suite.test_cases:
                    task_test_results = self.test_framework.run_tests_for_task(
                        task, test_suite, workspace_path
                    )
                    test_results["task_tests"][task.id] = {
                        "test_suite": test_suite.model_dump(),
                        "results": [r.model_dump() for r in task_test_results]
                    }
                else:
                    logger.warning(f"{Fore.YELLOW}⚠️ No tests generated for task {task.id}")
                    
            except Exception as e:
                logger.error(f"{Fore.RED}❌ Error testing task {task.id}: {str(e)}")
                test_results["task_tests"][task.id] = {"error": str(e)}
        
        # Calculate summary
        total_tests = sum(
            len(task_data.get("results", [])) 
            for task_data in test_results["task_tests"].values()
            if "results" in task_data
        )
        passed_tests = sum(
            len([r for r in task_data.get("results", []) if r.get("passed", False)])
            for task_data in test_results["task_tests"].values()
            if "results" in task_data
        )
        
        test_results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
            "tested_tasks": len([t for t in test_results["task_tests"].values() if "results" in t])
        }
        
        return test_results
    
    def validate_project_tasks(self, project: Project, workspace_path: str) -> Dict[str, Any]:
        """Validate all project tasks using static analysis and testing."""
        validation_results = {"task_validations": {}, "summary": {}}
        
        for task in project.tasks:
            if task.code:  # Only validate tasks with code
                try:
                    validation = self.task_validator.full_task_validation(task, workspace_path)
                    validation_results["task_validations"][task.id] = validation
                except Exception as e:
                    logger.error(f"{Fore.RED}❌ Error validating task {task.id}: {str(e)}")
                    validation_results["task_validations"][task.id] = {"error": str(e)}
        
        # Calculate summary
        qualities = [
            v.get("overall_quality", "unknown") 
            for v in validation_results["task_validations"].values()
            if "overall_quality" in v
        ]
        
        validation_results["summary"] = {
            "total_validated": len(qualities),
            "excellent": qualities.count("excellent"),
            "good": qualities.count("good"),
            "fair": qualities.count("fair"),
            "poor": qualities.count("poor"),
            "quality_distribution": {q: qualities.count(q) for q in set(qualities)}
        }
        
        return validation_results
    
    def generate_project_report(self, project: Project, execution_results: Dict[str, Any]) -> str:
        """Generate a comprehensive project report."""
        report = f"""# Project Report: {project.name}

## Project Information
- **ID:** {project.id}
- **Description:** {project.description}
- **Created:** {project.created_at}
- **Status:** {project.status}

## Execution Summary
- **Total Tasks:** {execution_results['summary']['total_tasks']}
- **Completed Tasks:** {execution_results['summary']['completed_tasks']}
- **Failed Tasks:** {execution_results['summary']['failed_tasks']}
- **Success Rate:** {execution_results['summary']['success_rate']:.1%}
- **Phases Executed:** {execution_results['summary']['total_phases']}

"""
        
        # Add test results if available
        if "test_results" in execution_results:
            test_summary = execution_results["test_results"]["summary"]
            report += f"""## Testing Summary
- **Total Tests:** {test_summary['total_tests']}
- **Passed Tests:** {test_summary['passed_tests']}
- **Test Success Rate:** {test_summary['success_rate']:.1%}
- **Tested Tasks:** {test_summary['tested_tasks']}

"""
        
        # Add validation results if available
        if "validation_results" in execution_results:
            val_summary = execution_results["validation_results"]["summary"]
            report += f"""## Code Quality Summary
- **Tasks Validated:** {val_summary['total_validated']}
- **Excellent Quality:** {val_summary['excellent']}
- **Good Quality:** {val_summary['good']}
- **Fair Quality:** {val_summary['fair']}
- **Poor Quality:** {val_summary['poor']}

"""
        
        # Add detailed task results
        report += "## Task Details\n\n"
        for i, phase in enumerate(execution_results["phases"]):
            report += f"### Phase {phase['phase_number']}\n"
            for task_result in phase["results"]:
                status_emoji = "✅" if task_result["status"] == "completed" else "❌"
                report += f"- {status_emoji} **{task_result['task_id']}:** {task_result['status']}\n"
        
        return report
    
    def save_project(self, project: Project):
        """Save project to file."""
        project_file = os.path.join(self.workspace, "projects", f"{project.id}.json")
        with open(project_file, 'w') as f:
            json.dump(project.model_dump(), f, indent=2)
    
    def save_task_library(self):
        """Save task library to file."""
        library_file = os.path.join(self.workspace, "library", "task_library.json")
        with open(library_file, 'w') as f:
            json.dump(self.task_library.model_dump(), f, indent=2)
    
    def load_task_library(self):
        """Load task library from file."""
        library_file = os.path.join(self.workspace, "library", "task_library.json")
        if os.path.exists(library_file):
            try:
                with open(library_file, 'r') as f:
                    data = json.load(f)
                    self.task_library = TaskLibrary(**data)
                logger.info(f"{Fore.GREEN}📚 Loaded task library with {len(self.task_library.tasks)} tasks")
            except Exception as e:
                logger.warning(f"{Fore.YELLOW}⚠️ Could not load task library: {str(e)}")
    
    def save_report(self, project_id: str, report: str):
        """Save project report to file."""
        report_file = os.path.join(self.workspace, "reports", f"{project_id}_report.md")
        with open(report_file, 'w') as f:
            f.write(report)
        logger.info(f"{Fore.GREEN}📋 Report saved to {report_file}")
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects with their status."""
        return [
            {
                "id": project.id,
                "name": project.name,
                "status": project.status,
                "tasks": len(project.tasks),
                "created": project.created_at
            }
            for project in self.projects.values()
        ]
    
    def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """Get detailed status of a project."""
        if project_id not in self.projects:
            raise ValueError(f"Project {project_id} not found")
        
        project = self.projects[project_id]
        ready_tasks = self.task_manager.get_ready_tasks(project.tasks)
        
        return {
            "project": project.model_dump(),
            "ready_tasks": len(ready_tasks),
            "task_breakdown": {
                "pending": len([t for t in project.tasks if t.status == "pending"]),
                "in_progress": len([t for t in project.tasks if t.status == "in_progress"]),
                "completed": len([t for t in project.tasks if t.status == "completed"]),
                "failed": len([t for t in project.tasks if t.status == "failed"])
            }
        }
    
    def load_existing_projects(self):
        """Load existing projects from the workspace."""
        projects_dir = os.path.join(self.workspace, "projects")
        if os.path.exists(projects_dir):
            for filename in os.listdir(projects_dir):
                if filename.endswith('.json'):
                    try:
                        project_file = os.path.join(projects_dir, filename)
                        with open(project_file, 'r') as f:
                            project_data = json.load(f)
                            
                        # Convert task data to EnhancedTask objects
                        if 'tasks' in project_data:
                            enhanced_tasks = []
                            for task_data in project_data['tasks']:
                                enhanced_task = EnhancedTask(**task_data)
                                enhanced_tasks.append(enhanced_task)
                            project_data['tasks'] = enhanced_tasks
                        
                        project = Project(**project_data)
                        self.projects[project.id] = project
                        
                    except Exception as e:
                        logger.warning(f"{Fore.YELLOW}⚠️ Could not load project {filename}: {str(e)}")
        
        if self.projects:
            logger.info(f"{Fore.GREEN}📋 Loaded {len(self.projects)} existing projects")
    
    def run(self):
        """Run the interactive CLI."""
        try:
            while True:
                print(f"\n{Fore.CYAN}=== ACE v2 - Enhanced Autonomous Coding Environment ===")
                print(f"{Fore.YELLOW}1. Create a new project")
                print(f"{Fore.YELLOW}2. List projects")
                print(f"{Fore.YELLOW}3. Execute project")
                print(f"{Fore.YELLOW}4. View project status")
                print(f"{Fore.YELLOW}5. View task library")
                print(f"{Fore.YELLOW}6. Exit")
                
                choice = input(f"{Fore.GREEN}Enter your choice (1-6): ").strip()
                
                if choice == "1":
                    name = input("Enter project name: ").strip()
                    description = input("Enter project description: ").strip()
                    if name and description:
                        project_id = self.create_project(name, description)
                        print(f"{Fore.GREEN}✅ Project created with ID: {project_id}")
                    else:
                        print(f"{Fore.RED}❌ Name and description are required")
                        
                elif choice == "2":
                    projects = self.list_projects()
                    if projects:
                        print(f"\n{Fore.CYAN}📋 Projects:")
                        for project in projects:
                            status_color = Fore.GREEN if project["status"] == "completed" else \
                                         Fore.BLUE if project["status"] == "in_progress" else Fore.YELLOW
                            print(f"{status_color}  {project['id']}: {project['name']} ({project['status']}) - {project['tasks']} tasks")
                    else:
                        print(f"{Fore.YELLOW}📋 No projects found")
                        
                elif choice == "3":
                    project_id = input("Enter project ID to execute: ").strip()
                    if project_id in self.projects:
                        run_tests = input("Run tests? (y/n): ").strip().lower() == 'y'
                        results = self.execute_project(project_id, run_tests)
                        print(f"{Fore.GREEN}✅ Project execution completed")
                        print(f"Success rate: {results['summary']['success_rate']:.1%}")
                    else:
                        print(f"{Fore.RED}❌ Project not found")
                        
                elif choice == "4":
                    project_id = input("Enter project ID: ").strip()
                    if project_id in self.projects:
                        status = self.get_project_status(project_id)
                        print(f"\n{Fore.CYAN}📊 Project Status:")
                        print(f"Name: {status['project']['name']}")
                        print(f"Status: {status['project']['status']}")
                        print(f"Ready tasks: {status['ready_tasks']}")
                        for status_name, count in status['task_breakdown'].items():
                            print(f"  {status_name}: {count}")
                    else:
                        print(f"{Fore.RED}❌ Project not found")
                        
                elif choice == "5":
                    print(f"\n{Fore.CYAN}📚 Task Library:")
                    print(f"Total tasks: {len(self.task_library.tasks)}")
                    for task_id, task in list(self.task_library.tasks.items())[:10]:  # Show first 10
                        print(f"  {task_id}: {task.description[:60]}...")
                    if len(self.task_library.tasks) > 10:
                        print(f"  ... and {len(self.task_library.tasks) - 10} more")
                        
                elif choice == "6":
                    print(f"{Fore.GREEN}👋 Goodbye! Thank you for using ACE v2!")
                    break
                    
                else:
                    print(f"{Fore.RED}❌ Invalid choice. Please try again.")
                    
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}⚠️ Operation cancelled by user")
        except Exception as e:
            logger.error(f"{Fore.RED}❌ Fatal error: {str(e)}")
            raise

def main():
    """Main entry point for ACE v2."""
    try:
        ace = ACEv2(workspace="ace_v2_workspace")
        ace.run()
    except Exception as e:
        logger.critical(f"{Fore.RED}💥 Critical error: {str(e)}")
        raise

if __name__ == "__main__":
    main() 