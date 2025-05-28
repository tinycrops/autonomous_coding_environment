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

# ... (previous class definitions remain unchanged)

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

    # ... (previous methods remain unchanged)

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

    def run(self):
        """Run the enhanced autonomous coding environment with intuitive task list management."""
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

    # ... (remaining methods stay the same)

if __name__ == "__main__":
    try:
        ace = EnhancedAutonomousCodingEnvironment(workspace="enhanced_autonomous_coding_workspace")
        ace.run()
    except Exception as e:
        logger.critical(f"{Fore.RED}💥 Critical error: {str(e)}")
        logger.critical(traceback.format_exc())