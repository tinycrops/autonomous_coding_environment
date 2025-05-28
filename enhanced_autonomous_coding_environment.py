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
import traceback

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

class ScriptResponse(BaseModel):
    explanation: str
    code_blocks: List[CodeBlock]

class Metadata(BaseModel):
    description: str
    tags: List[str] = Field(default_factory=list)
    complexity: int = Field(ge=1, le=10)
    estimated_time: str
    poetic_description: str

class MetadataResponse(BaseModel):
    description: str
    tags: List[str]
    complexity: int
    estimated_time: str
    poetic_description: str

class Task(BaseModel):
    id: str
    description: str
    code: str = ""
    metadata: Optional[Metadata] = None
    dependencies: List[str] = Field(default_factory=list)
    status: str = "pending"  # pending, in_progress, completed, failed
    execution_result: Optional[Dict[str, Any]] = None

class SimilarTaskResponse(BaseModel):
    similar_task_id: Optional[str]
    explanation: str

class Project(BaseModel):
    id: str
    name: str
    description: str
    tasks: List[Task] = Field(default_factory=list)

class TaskLibrary(BaseModel):
    tasks: Dict[str, Task] = Field(default_factory=dict)

class TaskListResponse(BaseModel):
    tasks: List[Dict[str, Any]]
    summary: str

class TaskActionResponse(BaseModel):
    action: str
    task_id: str
    result: str

class TaskLine(BaseModel):
    """Represents a single task in one line."""
    line: str

class OneLineTaskListResponse(BaseModel):
    """Represents the response for a one-line task list."""
    tasks: List[TaskLine]
    summary: str

class EnhancedAutonomousCodingEnvironment:
    def __init__(self, model: str = "o4-mini", workspace: str = "enhanced_autonomous_workspace"):
        self.model = model
        self.workspace = workspace
        self.projects: Dict[str, Project] = {}
        self.task_library = TaskLibrary()
        self.setup_workspace()

    def setup_workspace(self):
        """Set up a dedicated workspace for the autonomous coding environment."""
        try:
            if os.path.exists(self.workspace):
                shutil.rmtree(self.workspace)  # Clean up existing workspace
            os.makedirs(self.workspace)
            logger.info(f"{Fore.GREEN}🏗️ Created workspace: {self.workspace}")
        except Exception as e:
            logger.error(f"{Fore.RED}❌ Error setting up workspace: {str(e)}")
            raise

    def create_project(self, name: str, description: str) -> str:
        """Create a new project and break it down into tasks."""
        try:
            project_id = f"project_{len(self.projects) + 1}"
            project = Project(id=project_id, name=name, description=description)
            
            # Generate tasks for the project
            tasks = self.generate_tasks(project)
            project.tasks = tasks
            
            self.projects[project_id] = project
            logger.info(f"{Fore.CYAN}📁 Created project: {name} (ID: {project_id})")
            return project_id
        except Exception as e:
            logger.error(f"{Fore.RED}❌ Error creating project: {str(e)}")
            raise

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
                    tasks.append(Task(id=task_id, description=task_desc.strip()))
            
            logger.info(f"{Fore.YELLOW}🧩 Generated {len(tasks)} tasks for project {project.name}")
            return tasks
        except Exception as e:
            logger.error(f"{Fore.RED}❌ Error generating tasks: {str(e)}")
            return []

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

    def generate_code_for_task(self, task: Task) -> str:
        """Generate code for a given task using the AI model with structured output."""
        system_message = """
        You are an expert Python developer tasked with implementing a specific coding task.
        Provide a complete and working implementation for the given task description.
        Include error handling, logging, and comments in your code.
        """
        
        user_message = f"Task: {task.description}\n\nImplement this task in Python."

        try:
            response = client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                response_format=ScriptResponse,
            )
            script_response = response.choices[0].message.parsed
            
            # Extract the main Python code block
            main_code_block = next((block for block in script_response.code_blocks if block.language.lower() == 'python'), None)
            
            if main_code_block:
                logger.info(f"{Fore.GREEN}💻 Generated code for task: {task.id}")
                return main_code_block.code
            else:
                logger.warning(f"{Fore.YELLOW}⚠️ No Python code block found in the response for task: {task.id}")
                return f"# Error: No Python code block found in the AI response\n\ndef error_function():\n    raise NotImplementedError('Task implementation failed')"
        except Exception as e:
            logger.error(f"{Fore.RED}❌ Error generating code for task: {str(e)}")
            return f"# Error generating code: {str(e)}\n\ndef error_function():\n    raise NotImplementedError('Task implementation failed')"

    def implement_task(self, task: Task) -> Task:
        """Implement a single task using the AI model and generate metadata."""
        try:
            task.code = self.generate_code_for_task(task)
            task.metadata = self.generate_task_metadata(task)
            return task
        except Exception as e:
            logger.error(f"{Fore.RED}❌ Error implementing task: {str(e)}")
            task.status = "failed"
            task.execution_result = {"success": False, "error": str(e)}
            return task

    def generate_task_metadata(self, task: Task) -> Metadata:
        """Generate metadata for a task, including a poetic description, using structured output."""

        system_message = """
        You are an AI expert in software development and poetry. Analyze the given task and its code to generate metadata.
        Provide a concise description, relevant tags, estimate the complexity (1-10), and estimated time to complete.
        Also, create a short, poetic description that captures the essence of the task in a memorable way.
        """
        
        user_message = f"""
        Task: {task.description}
        
        Code:
        {task.code}
        
        Generate metadata including a concise description, relevant tags, complexity (1-10), estimated time to complete, and a short, poetic description of the task.
        """

        try:
            response = client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                response_format=MetadataResponse,
            )
            metadata = response.choices[0].message.parsed
            
            return Metadata(
                description=metadata.description,
                tags=metadata.tags,
                complexity=metadata.complexity,
                estimated_time=metadata.estimated_time,
                poetic_description=metadata.poetic_description
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

    def update_task_library(self, task: Task):
        """Update the task library with a successful task implementation."""
        if task.status == "completed":
            self.task_library.tasks[task.id] = task
            self.save_task_to_file(task)
            logger.info(f"{Fore.GREEN}📚 Added task to library: {task.id}")

    def save_task_to_file(self, task: Task):
        """Save a task to a file in the workspace."""
        try:
            task_dir = os.path.join(self.workspace, "task_library")
            os.makedirs(task_dir, exist_ok=True)
            task_file = os.path.join(task_dir, f"{task.id}.json")
            with open(task_file, 'w') as f:
                json.dump(task.dict(), f, indent=2)
        except Exception as e:
            logger.error(f"{Fore.RED}❌ Error saving task to file: {str(e)}")

    def load_task_library(self):
        """Load tasks from files in the workspace."""
        task_dir = os.path.join(self.workspace, "task_library")
        if os.path.exists(task_dir):
            for filename in os.listdir(task_dir):
                if filename.endswith(".json"):
                    try:
                        with open(os.path.join(task_dir, filename), 'r') as f:
                            task_data = json.load(f)
                            task = Task(**task_data)
                            self.task_library.tasks[task.id] = task
                    except Exception as e:
                        logger.error(f"{Fore.RED}❌ Error loading task from file {filename}: {str(e)}")
        logger.info(f"{Fore.GREEN}📚 Loaded {len(self.task_library.tasks)} tasks from library")

    def find_similar_task(self, task: Task) -> Optional[Task]:
        """Find a similar task in the task library using metadata and poetic descriptions with structured output."""
        system_message = """
        You are an AI expert in code similarity and poetic analysis. Compare the given task with the tasks in the library.
        Consider the task descriptions, code similarity, metadata, and poetic descriptions.
        If you find a similar task, return its ID. If not, return None.
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
        
        Find a similar task ID or return None.
        """

        try:
            response = client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                response_format=SimilarTaskResponse,
            )
            result = response.choices[0].message.parsed
            
            if result.similar_task_id and result.similar_task_id in self.task_library.tasks:
                logger.info(f"{Fore.YELLOW}🔍 Found similar task: {result.similar_task_id}")
                logger.info(f"Explanation: {result.explanation}")
                return self.task_library.tasks[result.similar_task_id]
            return None
        except Exception as e:
            logger.error(f"{Fore.RED}❌ Error finding similar task: {str(e)}")
            return None

    def adapt_task(self, original_task: Task, similar_task: Task) -> str:
        """Adapt a similar task's implementation to fit the current task using structured output."""
        system_message = """
        You are an expert Python developer tasked with adapting existing code to fit a new requirement.
        Modify the given code to implement the new task while maintaining its structure and error handling.
        """
        
        user_message = f"Original task: {original_task.description}\nSimilar task: {similar_task.description}\n\nSimilar task code:\n\n{similar_task.code}\n\nAdapt this code to implement the original task."

        try:
            response = client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                response_format=ScriptResponse,
            )
            script_response = response.choices[0].message.parsed
            
            # Extract the main Python code block
            main_code_block = next((block for block in script_response.code_blocks if block.language.lower() == 'python'), None)
            
            if main_code_block:
                logger.info(f"{Fore.GREEN}🔄 Adapted similar task for: {original_task.id}")
                return main_code_block.code
            else:
                logger.warning(f"{Fore.YELLOW}⚠️ No Python code block found in the adapted response for task: {original_task.id}")
                return f"# Error: No Python code block found in the AI response\n\ndef error_function():\n    raise NotImplementedError('Task adaptation failed')"
        except Exception as e:
            logger.error(f"{Fore.RED}❌ Error adapting task: {str(e)}")
            return f"# Error adapting task: {str(e)}\n\ndef error_function():\n    raise NotImplementedError('Task adaptation failed')"

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

            try:
                # Find similar task in library
                similar_task = self.find_similar_task(task)
                
                if similar_task:
                    # Adapt similar task
                    task.code = self.adapt_task(task, similar_task)
                else:
                    # Implement new task
                    task = self.implement_task(task)

                # Execute task
                task.execution_result = self.execute_task(task)
                
                if task.execution_result["success"]:
                    task.status = "completed"
                    self.update_task_library(task)
                else:
                    task.status = "failed"
                    logger.warning(f"{Fore.RED}❌ Task failed: {task.id}")
                    logger.warning(f"Error: {task.execution_result['error']}")
            except Exception as e:
                task.status = "failed"
                logger.error(f"{Fore.RED}❌ Error executing task {task.id}: {str(e)}")
                logger.error(traceback.format_exc())

        self.generate_project_report(project)

    def generate_project_report(self, project: Project):
        """Generate a summary report of the project execution."""
        try:
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
        except Exception as e:
            logger.error(f"{Fore.RED}❌ Error generating project report: {str(e)}")


    def get_task_list(self, project_id: str) -> OneLineTaskListResponse:
        """Get an intuitive task list for a project using structured output, with one task per line."""
        project = self.projects.get(project_id)
        if not project:
            return OneLineTaskListResponse(tasks=[], summary="Project not found")

        system_message = """
        You are an AI project manager assistant. Given a list of tasks for a project,
        create an intuitive and organized task list. Each task should be represented
        in a single line, including its ID, status, and a brief description.
        Group tasks by their status and provide a brief summary of the project's progress.

        Use the following format for each task line:
        [STATUS] ID: Brief description (Dependencies: dep1, dep2)

        STATUS should be one of: PENDING, IN PROGRESS, COMPLETED, FAILED
        If there are no dependencies, omit the parentheses.
        """

        task_data = [
            {
                "id": task.id,
                "description": task.description,
                "status": task.status,
                "dependencies": task.dependencies,
                "metadata": task.metadata.dict() if task.metadata else None
            }
            for task in project.tasks
        ]

        user_message = f"""
        Project: {project.name}
        Description: {project.description}

        Tasks:
        {json.dumps(task_data, indent=2)}

        Create a one-line task list grouped by status (pending, in_progress, completed, failed)
        and provide a brief summary of the project's progress.
        """

        try:
            response = client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                response_format=OneLineTaskListResponse,
            )
            return response.choices[0].message.parsed
        except Exception as e:
            logger.error(f"{Fore.RED}❌ Error generating one-line task list: {str(e)}")
            return OneLineTaskListResponse(
                tasks=[TaskLine(line=f"Error: {str(e)}")],
                summary=f"Error generating task list: {str(e)}"
            )
        
    def process_task_action(self, project_id: str, action: str, task_id: str) -> TaskActionResponse:
        """Process a task action (start, complete, fail) using structured output."""
        project = self.projects.get(project_id)
        if not project:
            return TaskActionResponse(action=action, task_id=task_id, result="Project not found")

        task = next((t for t in project.tasks if t.id == task_id), None)
        if not task:
            return TaskActionResponse(action=action, task_id=task_id, result="Task not found")

        system_message = f"""
        You are an AI project management assistant. Process the following task action:
        Action: {action}
        Task ID: {task_id}
        Current Task Status: {task.status}

        Determine if the action is valid and update the task status accordingly.
        Provide a brief result message explaining the outcome.
        """

        user_message = f"""
        Process the task action and provide the result.
        Consider the current task status and any dependencies.
        """

        try:
            response = client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                response_format=TaskActionResponse,
            )
            result = response.choices[0].message.parsed

            # Update task status based on the AI's decision
            if result.action == "start" and task.status == "pending":
                task.status = "in_progress"
            elif result.action == "complete" and task.status in ["pending", "in_progress"]:
                task.status = "completed"
            elif result.action == "fail" and task.status in ["pending", "in_progress"]:
                task.status = "failed"

            return result
        except Exception as e:
            logger.error(f"{Fore.RED}❌ Error processing task action: {str(e)}")
            return TaskActionResponse(action=action, task_id=task_id, result=f"Error processing task action: {str(e)}")

    def run(self):
        """Run the enhanced autonomous coding environment."""
        try:
            self.load_task_library()  # Load existing tasks from files
            while True:
                print(f"\n{Fore.CYAN}=== Autonomous Coding Environment ===")
                print(f"{Fore.YELLOW}1. Create a new project")
                print(f"{Fore.YELLOW}2. View project task list")
                print(f"{Fore.YELLOW}3. Process task action")
                print(f"{Fore.YELLOW}4. Execute a project")
                print(f"{Fore.YELLOW}5. View task library")
                print(f"{Fore.YELLOW}6. Search task library")
                print(f"{Fore.YELLOW}7. Exit")
                
                choice = input(f"{Fore.GREEN}Enter your choice (1-7): ")
                
                if choice == "1":
                    name = input("Enter project name: ")
                    description = input("Enter project description: ")
                    self.create_project(name, description)
                elif choice == "2":
                    project_id = input("Enter project ID to view task list: ")
                    task_list = self.get_task_list(project_id)
                    print(f"\n{Fore.CYAN}=== Task List ===")
                    print(f"{Fore.WHITE}{task_list.summary}")
                    for task in task_list.tasks:
                        status_color = Fore.YELLOW if "PENDING" in task.line else \
                                       Fore.BLUE if "IN PROGRESS" in task.line else \
                                       Fore.GREEN if "COMPLETED" in task.line else Fore.RED
                        print(f"{status_color}{task.line}")
                elif choice == "3":
                    project_id = input("Enter project ID: ")
                    task_id = input("Enter task ID: ")
                    action = input("Enter action (start/complete/fail): ")
                    result = self.process_task_action(project_id, action, task_id)
                    print(f"{Fore.CYAN}Action result: {result.result}")
                elif choice == "4":
                    project_id = input("Enter project ID to execute: ")
                    self.execute_project(project_id)
                elif choice == "5":
                    self.view_task_library()
                elif choice == "6":
                    self.search_task_library()
                elif choice == "7":
                    print(f"{Fore.GREEN}Exiting Autonomous Coding Environment. Goodbye!")
                    break
                else:
                    print(f"{Fore.RED}Invalid choice. Please try again.")
        except Exception as e:
            logger.error(f"{Fore.RED}❌ Fatal error in main loop: {str(e)}")
            logger.error(traceback.format_exc())

    def view_task_library(self):
        """View the contents of the task library."""
        try:
            print(f"\n{Fore.CYAN}=== Task Library ===")
            for task_id, task in self.task_library.tasks.items():
                print(f"{Fore.YELLOW}ID: {task_id}")
                print(f"Description: {task.description}")
                print(f"Tags: {', '.join(task.metadata.tags)}")
                print(f"Poetic Description: {task.metadata.poetic_description}")
                print(f"{Fore.CYAN}---")
        except Exception as e:
            logger.error(f"{Fore.RED}❌ Error viewing task library: {str(e)}")

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
    try:
        ace = EnhancedAutonomousCodingEnvironment(workspace="enhanced_autonomous_coding_workspace")
        ace.run()
    except Exception as e:
        logger.critical(f"{Fore.RED}💥 Critical error: {str(e)}")
        logger.critical(traceback.format_exc())