import os
import subprocess
import time
import random
import openai
from typing import List, Dict, Any, Optional, Union
import json
import logging
import shutil
from pydantic import BaseModel, Field
import jsonlines
from tqdm import tqdm
from colorama import Fore, Style, init

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize OpenAI client (make sure to set your API key in environment variables)
client = openai.OpenAI()

class CodeBlock(BaseModel):
    language: str
    code: str

class Metadata(BaseModel):
    description: str
    tags: List[str] = Field(default_factory=list)
    complexity: int = Field(ge=1, le=10)
    estimated_time: str
    poetic_description: str

class Task(BaseModel):
    id: str
    description: str
    code: str
    metadata: Optional[Metadata] = None
    dependencies: List[str] = Field(default_factory=list)
    status: str = "pending"  # pending, completed, failed
    execution_result: Optional[Dict[str, Any]] = None

class Project(BaseModel):
    id: str
    name: str
    description: str
    tasks: List[Task] = Field(default_factory=list)

class TaskLibrary(BaseModel):
    tasks: Dict[str, Task] = Field(default_factory=dict)

class EnhancedAutonomousCodingEnvironment:
    def __init__(self, model: str = "o4-mini", workspace: str = "enhanced_autonomous_workspace"):
        self.model = model
        self.workspace = workspace
        self.projects: Dict[str, Project] = {}
        self.task_library = TaskLibrary()
        self.setup_workspace()

    def setup_workspace(self):
        """Set up a dedicated workspace for the autonomous coding environment."""
        if os.path.exists(self.workspace):
            shutil.rmtree(self.workspace)  # Clean up existing workspace
        os.makedirs(self.workspace)
        logger.info(f"{Fore.GREEN}🏗️ Created workspace: {self.workspace}")

    def create_project(self, name: str, description: str) -> str:
        """Create a new project and break it down into tasks."""
        project_id = f"project_{len(self.projects) + 1}"
        project = Project(id=project_id, name=name, description=description)
        
        # Generate tasks for the project
        tasks = self.generate_tasks(project)
        project.tasks = tasks
        
        self.projects[project_id] = project
        logger.info(f"{Fore.CYAN}📁 Created project: {name} (ID: {project_id})")
        return project_id

    def generate_tasks(self, project: Project) -> List[Task]:
        """Generate tasks for a given project using the AI model."""
        system_message = (
            "You are an expert project manager and software architect. "
            "Break down the given project into small, manageable tasks. "
            "Each task should be a specific coding task that can be implemented independently. "
            "Provide a brief description for each task and identify any dependencies between tasks."
        )
        
        user_message = f"Project: {project.name}\nDescription: {project.description}\n\nBreak this project down into small coding tasks."

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ]
            )
            tasks_description = response.choices[0].message.content.strip()
            
            # Parse the tasks from the AI's response
            tasks = []
            for i, task_desc in enumerate(tasks_description.split("\n")):
                if task_desc.strip():
                    task_id = f"{project.id}_task_{i+1}"
                    tasks.append(Task(id=task_id, description=task_desc.strip(), code=""))
            
            logger.info(f"{Fore.YELLOW}🧩 Generated {len(tasks)} tasks for project {project.name}")
            return tasks
        except Exception as e:
            logger.error(f"{Fore.RED}❌ Error generating tasks: {str(e)}")
            return []

    def implement_task(self, task: Task) -> str:
        """Implement a single task using the AI model."""
        system_message = (
            "You are an expert Python developer tasked with implementing a specific coding task. "
            "Provide a complete and working implementation for the given task description. "
            "Include error handling, logging, and comments in your code."
        )
        
        user_message = f"Task: {task.description}\n\nImplement this task in Python."

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ]
            )
            implementation = response.choices[0].message.content.strip()
            logger.info(f"{Fore.GREEN}💻 Generated implementation for task: {task.id}")
            return implementation
        except Exception as e:
            logger.error(f"{Fore.RED}❌ Error implementing task: {str(e)}")
            return ""

    def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a single task and return the result."""
        task_filename = os.path.join(self.workspace, f"{task.id}.py")
        try:
            with open(task_filename, 'w') as f:
                f.write(task.code)
            
            result = subprocess.run(['python', task_filename], capture_output=True, text=True, timeout=30)
            
            execution_result = {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr
            }
            logger.info(f"{Fore.CYAN}🚀 Executed task: {task.id}")
            return execution_result
        except subprocess.TimeoutExpired:
            logger.warning(f"{Fore.YELLOW}⏳ Task execution timed out: {task.id}")
            return {"success": False, "error": "Execution timed out"}
        except Exception as e:
            logger.error(f"{Fore.RED}❌ Error executing task: {str(e)}")
            return {"success": False, "error": str(e)}


    def generate_task_metadata(self, task: Task) -> Metadata:
        """Generate metadata for a task, including a poetic description."""
        system_message = """
        You are an AI expert in software development and poetry. Analyze the given task and its code to generate metadata.
        Provide a concise description, relevant tags, estimate the complexity (1-10), and estimated time to complete.
        Also, create a short, poetic description that captures the essence of the task in a memorable way.
        """
        
        user_message = f"""
        Task: {task.description}
        
        Code:
        {task.code}
        
        Generate metadata including:
        1. A concise description
        2. Relevant tags
        3. Complexity (1-10)
        4. Estimated time to complete
        5. A short, poetic description of the task
        """

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ]
            )
            metadata_str = response.choices[0].message.content.strip()
            
            # Parse the metadata from the AI's response
            lines = metadata_str.split("\n")
            description = lines[0].split("Description: ")[-1]
            tags = lines[1].split("Tags: ")[-1].split(", ")
            complexity = int(lines[2].split("Complexity: ")[-1])
            estimated_time = lines[3].split("Estimated time: ")[-1]
            poetic_description = "\n".join(lines[4:]).strip()
            
            return Metadata(
                description=description,
                tags=tags,
                complexity=complexity,
                estimated_time=estimated_time,
                poetic_description=poetic_description
            )
        except Exception as e:
            logger.error(f"{Fore.RED}❌ Error generating task metadata: {str(e)}")
            return Metadata(
                description=task.description,
                tags=["error"],
                complexity=5,
                estimated_time="unknown",
                poetic_description="A task shrouded in mystery, its true nature yet to be revealed."
            )

    def implement_task(self, task: Task) -> Task:
        """Implement a single task using the AI model and generate metadata."""
        # ... (previous implementation code)
        
        task.code = self.generate_code_for_task(task)
        task.metadata = self.generate_task_metadata(task)
        return task

    def update_task_library(self, task: Task):
        """Update the task library with a successful task implementation."""
        if task.status == "completed":
            self.task_library.tasks[task.id] = task
            self.save_task_to_file(task)
            logger.info(f"{Fore.GREEN}📚 Added task to library: {task.id}")

    def save_task_to_file(self, task: Task):
        """Save a task to a file in the workspace."""
        task_dir = os.path.join(self.workspace, "task_library")
        os.makedirs(task_dir, exist_ok=True)
        task_file = os.path.join(task_dir, f"{task.id}.json")
        with open(task_file, 'w') as f:
            json.dump(task.dict(), f, indent=2)

    def load_task_library(self):
        """Load tasks from files in the workspace."""
        task_dir = os.path.join(self.workspace, "task_library")
        if os.path.exists(task_dir):
            for filename in os.listdir(task_dir):
                if filename.endswith(".json"):
                    with open(os.path.join(task_dir, filename), 'r') as f:
                        task_data = json.load(f)
                        task = Task(**task_data)
                        self.task_library.tasks[task.id] = task
        logger.info(f"{Fore.GREEN}📚 Loaded {len(self.task_library.tasks)} tasks from library")

    def find_similar_task(self, task: Task) -> Optional[Task]:
        """Find a similar task in the task library using metadata and poetic descriptions."""
        system_message = """
        You are an AI expert in code similarity and poetic analysis. Compare the given task with the tasks in the library.
        Consider the task descriptions, code similarity, metadata, and poetic descriptions.
        If you find a similar task, return its ID. If not, return 'None'.
        """
        
        task_library_desc = "\n".join([
            f"{t.id}:\nDescription: {t.description}\nTags: {', '.join(t.metadata.tags)}\nPoetic: {t.metadata.poetic_description}"
            for t in self.task_library.tasks.values()
        ])
        user_message = f"""
        Task to compare:
        Description: {task.description}
        
        Task Library:
        {task_library_desc}
        
        Find a similar task ID or return 'None'.
        """

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ]
            )
            similar_task_id = response.choices[0].message.content.strip()
            if similar_task_id != "None" and similar_task_id in self.task_library.tasks:
                logger.info(f"{Fore.YELLOW}🔍 Found similar task: {similar_task_id}")
                return self.task_library.tasks[similar_task_id]
            return None
        except Exception as e:
            logger.error(f"{Fore.RED}❌ Error finding similar task: {str(e)}")
            return None

    def adapt_task(self, original_task: Task, similar_task: Task) -> str:
        """Adapt a similar task's implementation to fit the current task."""
        system_message = (
            "You are an expert Python developer tasked with adapting existing code to fit a new requirement. "
            "Modify the given code to implement the new task while maintaining its structure and error handling."
        )
        
        user_message = f"Original task: {original_task.description}\nSimilar task: {similar_task.description}\n\nSimilar task code:\n\n{similar_task.code}\n\nAdapt this code to implement the original task."

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ]
            )
            adapted_code = response.choices[0].message.content.strip()
            logger.info(f"{Fore.GREEN}🔄 Adapted similar task for: {original_task.id}")
            return adapted_code
        except Exception as e:
            logger.error(f"{Fore.RED}❌ Error adapting task: {str(e)}")
            return ""

    def execute_project(self, project_id: str):
        """Execute all tasks in a project."""
        project = self.projects.get(project_id)
        if not project:
            logger.error(f"{Fore.RED}❌ Project not found: {project_id}")
            return

        logger.info(f"{Fore.CYAN}🚀 Executing project: {project.name}")
        for task in tqdm(project.tasks, desc="Executing tasks", unit="task"):
            if task.status != "pending":
                continue

            # Check for unmet dependencies
            if any(dep_task.status != "completed" for dep_task in project.tasks if dep_task.id in task.dependencies):
                logger.info(f"{Fore.YELLOW}⏳ Skipping task due to unmet dependencies: {task.id}")
                continue

            # Find similar task in library
            similar_task = self.find_similar_task(task)
            
            if similar_task:
                # Adapt similar task
                task.code = self.adapt_task(task, similar_task)
            else:
                # Implement new task
                task.code = self.implement_task(task)

            # Execute task
            task.execution_result = self.execute_task(task)
            
            if task.execution_result["success"]:
                task.status = "completed"
                self.update_task_library(task)
            else:
                task.status = "failed"
                logger.warning(f"{Fore.RED}❌ Task failed: {task.id}")
                logger.warning(f"Error: {task.execution_result['error']}")

        self.generate_project_report(project)

    def generate_project_report(self, project: Project):
        """Generate a summary report of the project execution."""
        report = f"{Fore.CYAN}📊 Project Execution Report: {project.name}\n"
        report += f"Total Tasks: {len(project.tasks)}\n"
        completed_tasks = sum(1 for task in project.tasks if task.status == "completed")
        failed_tasks = sum(1 for task in project.tasks if task.status == "failed")
        report += f"Completed Tasks: {completed_tasks}\n"
        report += f"Failed Tasks: {failed_tasks}\n"
        report += f"Success Rate: {completed_tasks / len(project.tasks):.2%}\n"
        
        report += "\nTask Details:\n"
        for task in project.tasks:
            status_color = Fore.GREEN if task.status == "completed" else Fore.RED
            report += f"{status_color}[{task.status.upper()}] {task.id}: {task.description}\n"
        
        report_file = os.path.join(self.workspace, f"{project.id}_report.txt")
        with open(report_file, 'w') as f:
            f.write(report)
        print(report)
        logger.info(f"{Fore.GREEN}📝 Generated project report: {report_file}")

    def run(self):
        """Run the enhanced autonomous coding environment."""
        self.load_task_library()  # Load existing tasks from files
        while True:
            print(f"\n{Fore.CYAN}=== Autonomous Coding Environment ===")
            print(f"{Fore.YELLOW}1. Create a new project")
            print(f"{Fore.YELLOW}2. Execute a project")
            print(f"{Fore.YELLOW}3. View task library")
            print(f"{Fore.YELLOW}4. Search task library")
            print(f"{Fore.YELLOW}5. Exit")
            
            choice = input(f"{Fore.GREEN}Enter your choice (1-5): ")
            
            if choice == "1":
                name = input("Enter project name: ")
                description = input("Enter project description: ")
                self.create_project(name, description)
            elif choice == "2":
                project_id = input("Enter project ID to execute: ")
                self.execute_project(project_id)
            elif choice == "3":
                self.view_task_library()
            elif choice == "4":
                self.search_task_library()
            elif choice == "5":
                print(f"{Fore.GREEN}Exiting Autonomous Coding Environment. Goodbye!")
                break
            else:
                print(f"{Fore.RED}Invalid choice. Please try again.")

    def view_task_library(self):
        """View the contents of the task library."""
        print(f"\n{Fore.CYAN}=== Task Library ===")
        for task_id, task in self.task_library.tasks.items():
            print(f"{Fore.YELLOW}ID: {task_id}")
            print(f"Description: {task.description}")
            print(f"Tags: {', '.join(task.metadata.tags)}")
            print(f"Poetic Description: {task.metadata.poetic_description}")
            print(f"{Fore.CYAN}---")

    def search_task_library(self):
        """Search the task library using natural language queries."""
        query = input("Enter your search query: ")
        system_message = """
        You are an AI expert in searching and matching code tasks. Given a search query and a list of tasks,
        return the IDs of the most relevant tasks, along with a brief explanation of why they match.
        """
        
        task_library_desc = "\n".join([
            f"{t.id}:\nDescription: {t.description}\nTags: {', '.join(t.metadata.tags)}\nPoetic: {t.metadata.poetic_description}"
            for t in self.task_library.tasks.values()
        ])
        user_message = f"""
        Search Query: {query}
        
        Task Library:
        {task_library_desc}
        
        Return the IDs of the most relevant tasks and explain why they match the query.
        """

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ]
            )
            search_results = response.choices[0].message.content.strip()
            print(f"\n{Fore.CYAN}=== Search Results ===")
            print(search_results)
        except Exception as e:
            logger.error(f"{Fore.RED}❌ Error searching task library: {str(e)}")
            print(f"{Fore.RED}An error occurred while searching the task library.")

if __name__ == "__main__":
    ace = EnhancedAutonomousCodingEnvironment(workspace="enhanced_autonomous_coding_workspace")
    ace.run()