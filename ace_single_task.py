import os
import subprocess
import time
import random
import openai
from typing import List, Dict, Any, Optional
import json
import logging
import shutil
from pydantic import BaseModel, Field
import traceback
from colorama import Fore, Style, init
from datetime import datetime

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

class Task(BaseModel):
    id: str
    description: str
    code: str = ""
    metadata: Optional[Metadata] = None
    status: str = "pending"  # pending, in_progress, completed, failed
    execution_result: Optional[Dict[str, Any]] = None

class MetadataResponse(BaseModel):
    description: str
    tags: List[str]
    complexity: int
    estimated_time: str
    poetic_description: str

class AutonomousSingleTaskCodingEnvironment:
    def __init__(self, model: str = "gpt-4o-mini", workspace: str = "autonomous_single_task_workspace"):
        self.model = model
        self.workspace = workspace
        self.task: Optional[Task] = None
        self.activity_log: List[Dict[str, Any]] = []
        self.setup_workspace()

    def log_activity(self, activity: str, details: Dict[str, Any] = None):
        """Log an activity with timestamp and details."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "activity": activity,
            "details": details or {}
        }
        self.activity_log.append(log_entry)
        log_message = f"{Fore.BLUE}[ACTIVITY] {activity}"
        if details:
            log_message += f"\n{json.dumps(details, indent=2)}"
        print(log_message)
        logger.info(log_message)

    def setup_workspace(self):
        """Set up a dedicated workspace for the autonomous coding environment."""
        try:
            if os.path.exists(self.workspace):
                shutil.rmtree(self.workspace)  # Clean up existing workspace
            os.makedirs(self.workspace)
            self.log_activity("Workspace Created", {"workspace": self.workspace})
        except Exception as e:
            error_msg = f"Error setting up workspace: {str(e)}"
            self.log_activity("Workspace Setup Failed", {"error": error_msg})
            raise

    def create_task(self, description: str) -> str:
        """Create a new task based on the given description."""
        try:
            task_id = f"task_{int(time.time())}"
            self.task = Task(id=task_id, description=description)
            self.log_activity("Task Created", {"task_id": task_id, "description": description})
            return task_id
        except Exception as e:
            error_msg = f"Error creating task: {str(e)}"
            self.log_activity("Task Creation Failed", {"error": error_msg})
            raise

    def generate_code_for_task(self) -> str:
        """Generate code for the task using the AI model with structured output."""
        if not self.task:
            raise ValueError("No task has been created yet.")

        system_message = """
        You are an expert Python developer tasked with implementing a specific coding task.
        Provide a complete and working implementation for the given task description.
        Include error handling, logging, and comments in your code.
        Also, add emojis in the comments to make the code more engaging and easier to understand.
        """
        
        user_message = f"Task: {self.task.description}\n\nImplement this task in Python."

        try:
            self.log_activity("Generating Code", {"task_id": self.task.id})
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
                self.log_activity("Code Generated Successfully", {"task_id": self.task.id})
                return main_code_block.code
            else:
                error_msg = f"No Python code block found in the response for task: {self.task.id}"
                self.log_activity("Code Generation Failed", {"error": error_msg})
                return f"# Error: No Python code block found in the AI response\n\ndef error_function():\n    raise NotImplementedError('Task implementation failed')"
        except Exception as e:
            error_msg = f"Error generating code for task: {str(e)}"
            self.log_activity("Code Generation Failed", {"error": error_msg})
            return f"# Error generating code: {str(e)}\n\ndef error_function():\n    raise NotImplementedError('Task implementation failed')"

    def generate_task_metadata(self) -> Metadata:
        """Generate metadata for the task, including a poetic description, using structured output."""
        if not self.task:
            raise ValueError("No task has been created yet.")

        system_message = """
        You are an AI expert in software development and poetry. Analyze the given task and its code to generate metadata.
        Provide a concise description, relevant tags, estimate the complexity (1-10), and estimated time to complete.
        Also, create a short, poetic description that captures the essence of the task in a memorable way.
        """
        
        user_message = f"""
        Task: {self.task.description}
        
        Code:
        {self.task.code}
        
        Generate metadata including a concise description, relevant tags, complexity (1-10), estimated time to complete, and a short, poetic description of the task.
        """

        try:
            self.log_activity("Generating Task Metadata", {"task_id": self.task.id})
            response = client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                response_format=MetadataResponse,
            )
            metadata = response.choices[0].message.parsed
            
            generated_metadata = Metadata(
                description=metadata.description,
                tags=metadata.tags,
                complexity=metadata.complexity,
                estimated_time=metadata.estimated_time,
                poetic_description=metadata.poetic_description
            )
            self.log_activity("Task Metadata Generated", {"task_id": self.task.id, "metadata": generated_metadata.dict()})
            return generated_metadata
        except Exception as e:
            error_msg = f"Error generating task metadata: {str(e)}"
            self.log_activity("Metadata Generation Failed", {"error": error_msg})
            return Metadata(
                description=self.task.description,
                tags=["error"],
                complexity=5,
                estimated_time="unknown",
                poetic_description="A task shrouded in mystery, its true nature yet to be revealed."
            )

    def implement_task(self) -> Task:
        """Implement the task using the AI model and generate metadata."""
        if not self.task:
            raise ValueError("No task has been created yet.")

        try:
            self.log_activity("Implementing Task", {"task_id": self.task.id})
            self.task.code = self.generate_code_for_task()
            self.task.metadata = self.generate_task_metadata()
            self.log_activity("Task Implemented", {"task_id": self.task.id})
            return self.task
        except Exception as e:
            error_msg = f"Error implementing task: {str(e)}"
            self.log_activity("Task Implementation Failed", {"error": error_msg})
            self.task.status = "failed"
            self.task.execution_result = {"success": False, "error": str(e)}
            return self.task

    def execute_task(self) -> Dict[str, Any]:
        """Execute the task and return the result."""
        if not self.task:
            raise ValueError("No task has been created yet.")

        task_filename = os.path.join(self.workspace, f"{self.task.id}.py")
        try:
            self.log_activity("Executing Task", {"task_id": self.task.id, "filename": task_filename})
            with open(task_filename, 'w') as f:
                f.write(self.task.code)
            
            result = subprocess.run(['python', task_filename], capture_output=True, text=True, timeout=30)
            
            execution_result = {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr
            }
            self.log_activity("Task Execution Completed", {"task_id": self.task.id, "result": execution_result})
            return execution_result
        except subprocess.TimeoutExpired:
            error_msg = f"Task execution timed out: {self.task.id}"
            self.log_activity("Task Execution Timed Out", {"error": error_msg})
            return {"success": False, "error": "Execution timed out"}
        except Exception as e:
            error_msg = f"Error executing task: {str(e)}"
            self.log_activity("Task Execution Failed", {"error": error_msg})
            return {"success": False, "error": str(e)}

    def improve_task(self) -> Task:
        """Improve the task implementation based on execution results."""
        if not self.task or not self.task.execution_result:
            raise ValueError("No task has been executed yet.")

        if self.task.execution_result["success"]:
            self.log_activity("Task Improvement Skipped", {"reason": "Task already successful"})
            return self.task

        system_message = """
        You are an expert Python developer tasked with improving code that failed to execute correctly.
        Analyze the error message and the original code, then provide an improved implementation that addresses the issues.
        Include error handling, logging, and comments in your code.
        Also, add emojis in the comments to make the code more engaging and easier to understand.
        """
        
        user_message = f"""
        Original task: {self.task.description}
        
        Original code:
        {self.task.code}
        
        Error message:
        {self.task.execution_result['error']}
        
        Improve the code to fix the error and implement the task correctly.
        """

        try:
            self.log_activity("Improving Task", {"task_id": self.task.id})
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
                self.task.code = main_code_block.code
                self.log_activity("Task Improved", {"task_id": self.task.id})
                return self.task
            else:
                error_msg = f"No Python code block found in the improved response for task: {self.task.id}"
                self.log_activity("Task Improvement Failed", {"error": error_msg})
                return self.task
        except Exception as e:
            error_msg = f"Error improving task: {str(e)}"
            self.log_activity("Task Improvement Failed", {"error": error_msg})
            return self.task

    def save_activity_log(self):
        """Save the activity log to a file."""
        log_file = os.path.join(self.workspace, "activity_log.json")
        try:
            with open(log_file, 'w') as f:
                json.dump(self.activity_log, f, indent=2)
            print(f"\n{Fore.GREEN}📝 Activity log saved to: {log_file}")
        except Exception as e:
            print(f"\n{Fore.RED}❌ Error saving activity log: {str(e)}")

    def run(self):
        """Run the autonomous single-task coding environment."""
        try:
            print(f"{Fore.CYAN}=== Autonomous Single-Task Coding Environment ===")
            task_description = input(f"{Fore.GREEN}Enter task description: ")
            self.create_task(task_description)

            print(f"\n{Fore.YELLOW}Implementing task...")
            self.implement_task()

            print(f"\n{Fore.CYAN}=== Task Details ===")
            print(f"{Fore.WHITE}ID: {self.task.id}")
            print(f"Description: {self.task.description}")
            print(f"Complexity: {self.task.metadata.complexity}")
            print(f"Estimated Time: {self.task.metadata.estimated_time}")
            print(f"Tags: {', '.join(self.task.metadata.tags)}")
            print(f"Poetic Description: {self.task.metadata.poetic_description}")

            print(f"\n{Fore.YELLOW}Executing task...")
            self.task.execution_result = self.execute_task()

            if self.task.execution_result["success"]:
                self.task.status = "completed"
                print(f"\n{Fore.GREEN}✅ Task executed successfully!")
                print(f"{Fore.WHITE}Output:\n{self.task.execution_result['output']}")
            else:
                self.task.status = "failed"
                print(f"\n{Fore.RED}❌ Task execution failed.")
                print(f"{Fore.WHITE}Error:\n{self.task.execution_result['error']}")

                print(f"\n{Fore.YELLOW}Attempting to improve the task...")
                self.improve_task()

                print(f"\n{Fore.YELLOW}Re-executing improved task...")
                self.task.execution_result = self.execute_task()

                if self.task.execution_result["success"]:
                    self.task.status = "completed"
                    print(f"\n{Fore.GREEN}✅ Improved task executed successfully!")
                    print(f"{Fore.WHITE}Output:\n{self.task.execution_result['output']}")
                else:
                    print(f"\n{Fore.RED}❌ Improved task execution failed.")
                    print(f"{Fore.WHITE}Error:\n{self.task.execution_result['error']}")

            print(f"\n{Fore.CYAN}=== Final Task Status ===")
            print(f"{Fore.WHITE}Status: {self.task.status}")

            # Save the final task implementation
            task_file = os.path.join(self.workspace, f"{self.task.id}_final.py")
            with open(task_file, 'w') as f:
                f.write(self.task.code)
            print(f"\n{Fore.GREEN}💾 Final task implementation saved to: {task_file}")

            # Save the task metadata
            metadata_file = os.path.join(self.workspace, f"{self.task.id}_metadata.json")
            with open(metadata_file, 'w') as f:
                json.dump(self.task.metadata.dict(), f, indent=2)
            print(f"{Fore.GREEN}📊 Task metadata saved to: {metadata_file}")

            # Save the execution result
            result_file = os.path.join(self.workspace, f"{self.task.id}_result.json")
            with open(result_file, 'w') as f:
                json.dump(self.task.execution_result, f, indent=2)
            print(f"{Fore.GREEN}📈 Execution result saved to: {result_file}")

            # Save the activity log
            self.save_activity_log()

            print(f"\n{Fore.CYAN}=== Task Summary ===")
            print(f"{Fore.WHITE}Task ID: {self.task.id}")
            print(f"Description: {self.task.description}")
            print(f"Final Status: {self.task.status}")
            print(f"Complexity: {self.task.metadata.complexity}")
            print(f"Estimated Time: {self.task.metadata.estimated_time}")
            print(f"Tags: {', '.join(self.task.metadata.tags)}")
            print(f"\nPoetic Description:\n{self.task.metadata.poetic_description}")

            print(f"\n{Fore.CYAN}=== Activity Log Summary ===")
            for entry in self.activity_log:
                timestamp = entry['timestamp']
                activity = entry['activity']
                print(f"{Fore.YELLOW}{timestamp}: {Fore.WHITE}{activity}")

        except Exception as e:
            logger.critical(f"{Fore.RED}💥 Critical error: {str(e)}")
            logger.critical(traceback.format_exc())
            self.log_activity("Critical Error", {"error": str(e), "traceback": traceback.format_exc()})
        finally:
            self.save_activity_log()

if __name__ == "__main__":
    try:
        env = AutonomousSingleTaskCodingEnvironment(workspace="autonomous_single_task_workspace")
        env.run()
    except Exception as e:
        logger.critical(f"{Fore.RED}💥 Critical error: {str(e)}")
        logger.critical(traceback.format_exc())

"""
[ACTIVITY] Workspace Created
{
  "workspace": "autonomous_single_task_workspace"
}
2024-08-13 22:14:24,884 - INFO - [ACTIVITY] Workspace Created
{
  "workspace": "autonomous_single_task_workspace"
}
=== Autonomous Single-Task Coding Environment ===
Enter task description: a filing assistant for my data
[ACTIVITY] Task Created
{
  "task_id": "task_1723601722",
  "description": "a filing assistant for my data"
}
2024-08-13 22:15:22,981 - INFO - [ACTIVITY] Task Created
{
  "task_id": "task_1723601722",
  "description": "a filing assistant for my data"
}

Implementing task...
[ACTIVITY] Implementing Task
{
  "task_id": "task_1723601722"
}
2024-08-13 22:15:22,981 - INFO - [ACTIVITY] Implementing Task
{
  "task_id": "task_1723601722"
}
[ACTIVITY] Generating Code
{
  "task_id": "task_1723601722"
}
2024-08-13 22:15:22,981 - INFO - [ACTIVITY] Generating Code
{
  "task_id": "task_1723601722"
}
2024-08-13 22:15:31,888 - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
[ACTIVITY] Code Generated Successfully
{
  "task_id": "task_1723601722"
}
2024-08-13 22:15:31,947 - INFO - [ACTIVITY] Code Generated Successfully
{
  "task_id": "task_1723601722"
}
[ACTIVITY] Generating Task Metadata
{
  "task_id": "task_1723601722"
}
2024-08-13 22:15:31,947 - INFO - [ACTIVITY] Generating Task Metadata
{
  "task_id": "task_1723601722"
}
2024-08-13 22:15:33,633 - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
[ACTIVITY] Task Metadata Generated
{
  "task_id": "task_1723601722",
  "metadata": {
    "description": "A Filing Assistant that manages data entries for files, allowing users to add, retrieve, and delete entries while storing them in a JSON file. It features logging for tracking actions and error handling for data integrity.",
    "tags": [
      "filing",
      "data management",
      "JSON",
      "Python",
      "logging"
    ],
    "complexity": 5,
    "estimated_time": "2-3 hours",
    "poetic_description": "In a digital realm where files reside,  \nA trusty assistant to help them abide.  \nWith echoes of order, it keeps data near,  \nAdding, deleting, storing\u2014never to fear."
  }
}
2024-08-13 22:15:33,644 - INFO - [ACTIVITY] Task Metadata Generated
{
  "task_id": "task_1723601722",
  "metadata": {
    "description": "A Filing Assistant that manages data entries for files, allowing users to add, retrieve, and delete entries while storing them in a JSON file. It features logging for tracking actions and error handling for data integrity.",
    "tags": [
      "filing",
      "data management",
      "JSON",
      "Python",
      "logging"
    ],
    "complexity": 5,
    "estimated_time": "2-3 hours",
    "poetic_description": "In a digital realm where files reside,  \nA trusty assistant to help them abide.  \nWith echoes of order, it keeps data near,  \nAdding, deleting, storing\u2014never to fear."
  }
}
[ACTIVITY] Task Implemented
{
  "task_id": "task_1723601722"
}
2024-08-13 22:15:33,644 - INFO - [ACTIVITY] Task Implemented
{
  "task_id": "task_1723601722"
}

=== Task Details ===
ID: task_1723601722
Description: a filing assistant for my data
Complexity: 5
Estimated Time: 2-3 hours
Tags: filing, data management, JSON, Python, logging
Poetic Description: In a digital realm where files reside,  
A trusty assistant to help them abide.  
With echoes of order, it keeps data near,  
Adding, deleting, storing—never to fear.

Executing task...
[ACTIVITY] Executing Task
{
  "task_id": "task_1723601722",
  "filename": "autonomous_single_task_workspace/task_1723601722.py"
}
2024-08-13 22:15:33,644 - INFO - [ACTIVITY] Executing Task
{
  "task_id": "task_1723601722",
  "filename": "autonomous_single_task_workspace/task_1723601722.py"
}
[ACTIVITY] Task Execution Completed
{
  "task_id": "task_1723601722",
  "result": {
    "success": true,
    "output": "Current Entries: [{'name': 'Report', 'type': 'PDF', 'description': 'Annual financial report for 2023'}, {'name': 'Presentation', 'type': 'PPT', 'description': 'Sales presentation Q1 2023'}]\nCurrent Entries after deletion: [{'name': 'Presentation', 'type': 'PPT', 'description': 'Sales presentation Q1 2023'}]\n",
    "error": ""
  }
}
2024-08-13 22:15:33,707 - INFO - [ACTIVITY] Task Execution Completed
{
  "task_id": "task_1723601722",
  "result": {
    "success": true,
    "output": "Current Entries: [{'name': 'Report', 'type': 'PDF', 'description': 'Annual financial report for 2023'}, {'name': 'Presentation', 'type': 'PPT', 'description': 'Sales presentation Q1 2023'}]\nCurrent Entries after deletion: [{'name': 'Presentation', 'type': 'PPT', 'description': 'Sales presentation Q1 2023'}]\n",
    "error": ""
  }
}

✅ Task executed successfully!
Output:
Current Entries: [{'name': 'Report', 'type': 'PDF', 'description': 'Annual financial report for 2023'}, {'name': 'Presentation', 'type': 'PPT', 'description': 'Sales presentation Q1 2023'}]
Current Entries after deletion: [{'name': 'Presentation', 'type': 'PPT', 'description': 'Sales presentation Q1 2023'}]


=== Final Task Status ===
Status: completed

💾 Final task implementation saved to: autonomous_single_task_workspace/task_1723601722_final.py
📊 Task metadata saved to: autonomous_single_task_workspace/task_1723601722_metadata.json
📈 Execution result saved to: autonomous_single_task_workspace/task_1723601722_result.json

📝 Activity log saved to: autonomous_single_task_workspace/activity_log.json

=== Task Summary ===
Task ID: task_1723601722
Description: a filing assistant for my data
Final Status: completed
Complexity: 5
Estimated Time: 2-3 hours
Tags: filing, data management, JSON, Python, logging

Poetic Description:
In a digital realm where files reside,  
A trusty assistant to help them abide.  
With echoes of order, it keeps data near,  
Adding, deleting, storing—never to fear.

=== Activity Log Summary ===
2024-08-13T22:14:24.884683: Workspace Created
2024-08-13T22:15:22.980946: Task Created
2024-08-13T22:15:22.981209: Implementing Task
2024-08-13T22:15:22.981329: Generating Code
2024-08-13T22:15:31.947144: Code Generated Successfully
2024-08-13T22:15:31.947365: Generating Task Metadata
2024-08-13T22:15:33.643801: Task Metadata Generated
2024-08-13T22:15:33.644297: Task Implemented
2024-08-13T22:15:33.644762: Executing Task
2024-08-13T22:15:33.704977: Task Execution Completed

📝 Activity log saved to: autonomous_single_task_workspace/activity_log.json
"""