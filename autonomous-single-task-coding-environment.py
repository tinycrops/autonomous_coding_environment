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

    def create_task(self, description: str) -> str:
        """Create a new task based on the given description."""
        try:
            task_id = f"task_{int(time.time())}"
            self.task = Task(id=task_id, description=description)
            logger.info(f"{Fore.CYAN}📝 Created task: {description} (ID: {task_id})")
            return task_id
        except Exception as e:
            logger.error(f"{Fore.RED}❌ Error creating task: {str(e)}")
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
                logger.info(f"{Fore.GREEN}💻 Generated code for task: {self.task.id}")
                return main_code_block.code
            else:
                logger.warning(f"{Fore.YELLOW}⚠️ No Python code block found in the response for task: {self.task.id}")
                return f"# Error: No Python code block found in the AI response\n\ndef error_function():\n    raise NotImplementedError('Task implementation failed')"
        except Exception as e:
            logger.error(f"{Fore.RED}❌ Error generating code for task: {str(e)}")
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
            self.task.code = self.generate_code_for_task()
            self.task.metadata = self.generate_task_metadata()
            return self.task
        except Exception as e:
            logger.error(f"{Fore.RED}❌ Error implementing task: {str(e)}")
            self.task.status = "failed"
            self.task.execution_result = {"success": False, "error": str(e)}
            return self.task

    def execute_task(self) -> Dict[str, Any]:
        """Execute the task and return the result."""
        if not self.task:
            raise ValueError("No task has been created yet.")

        task_filename = os.path.join(self.workspace, f"{self.task.id}.py")
        try:
            with open(task_filename, 'w') as f:
                f.write(self.task.code)
            
            result = subprocess.run(['python', task_filename], capture_output=True, text=True, timeout=30)
            
            execution_result = {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr
            }
            logger.info(f"{Fore.CYAN}🚀 Executed task: {self.task.id}")
            return execution_result
        except subprocess.TimeoutExpired:
            logger.warning(f"{Fore.YELLOW}⏳ Task execution timed out: {self.task.id}")
            return {"success": False, "error": "Execution timed out"}
        except Exception as e:
            logger.error(f"{Fore.RED}❌ Error executing task: {str(e)}")
            return {"success": False, "error": str(e)}

    def improve_task(self) -> Task:
        """Improve the task implementation based on execution results."""
        if not self.task or not self.task.execution_result:
            raise ValueError("No task has been executed yet.")

        if self.task.execution_result["success"]:
            logger.info(f"{Fore.GREEN}✅ Task executed successfully. No improvements needed.")
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
                logger.info(f"{Fore.GREEN}🔧 Improved code for task: {self.task.id}")
                return self.task
            else:
                logger.warning(f"{Fore.YELLOW}⚠️ No Python code block found in the improved response for task: {self.task.id}")
                return self.task
        except Exception as e:
            logger.error(f"{Fore.RED}❌ Error improving task: {str(e)}")
            return self.task

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

        except Exception as e:
            logger.critical(f"{Fore.RED}💥 Critical error: {str(e)}")
            logger.critical(traceback.format_exc())

if __name__ == "__main__":
    try:
        env = AutonomousSingleTaskCodingEnvironment(workspace="autonomous_single_task_workspace")
        env.run()
    except Exception as e:
        logger.critical(f"{Fore.RED}💥 Critical error: {str(e)}")
        logger.critical(traceback.format_exc())
