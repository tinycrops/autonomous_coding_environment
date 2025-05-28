import os
import subprocess
import time
import openai
from typing import List, Dict, Any, Optional
import json
import logging
from pydantic import BaseModel, Field
from colorama import Fore, Style, init
from datetime import datetime
import traceback
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Initialize OpenAI client
client = openai.OpenAI()

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class BaseTaskProcessor:
    """Base class for task processing functionality shared across ACE variants."""
    
    def __init__(self, model: str = "o4-mini"):
        self.model = model
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def generate_code_for_task(self, task: Task, additional_context: str = "") -> str:
        """Generate code for a task using structured output with improved error handling."""
        system_message = """
        You are an expert Python developer tasked with implementing a specific coding task.
        Provide a complete and working implementation for the given task description.
        
        IMPORTANT REQUIREMENTS:
        - Include error handling, logging, and comments in your code
        - Make the code production-ready with proper structure and documentation
        - The code should run successfully when executed directly
        - Do NOT include command-line argument parsing in the main block
        - If including a main block, make it demonstrate the functionality with example values
        - Use simple examples that don't require user input or external files
        - Focus on implementing the core functionality requested
        
        The code should be self-contained and executable without any external dependencies beyond standard library.
        """
        
        user_message = f"Task: {task.description}"
        if additional_context:
            user_message += f"\n\nAdditional Context: {additional_context}"
        user_message += "\n\nImplement this task in Python."

        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.logger.info(f"{Fore.BLUE}🔄 Generating code for task {task.id} (attempt {attempt + 1})")
                response = client.beta.chat.completions.parse(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message}
                    ],
                    response_format=ScriptResponse,
                )
                
                if not response.choices or not response.choices[0].message.parsed:
                    raise ValueError("Empty response from OpenAI API")
                    
                script_response = response.choices[0].message.parsed
                
                # Extract the main Python code block
                main_code_block = next(
                    (block for block in script_response.code_blocks if block.language.lower() == 'python'), 
                    None
                )
                
                if main_code_block:
                    self.logger.info(f"{Fore.GREEN}✅ Code generated successfully for task {task.id}")
                    return main_code_block.code
                else:
                    raise ValueError("No Python code block found in the response")
                    
            except Exception as e:
                self.logger.warning(f"{Fore.YELLOW}⚠️ Attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    error_code = f"""# Error generating code: {str(e)}
# Fallback implementation for task: {task.description}

def main():
    '''
    Fallback implementation - requires manual completion
    Task: {task.description}
    '''
    raise NotImplementedError(f'Task implementation failed: {str(e)}')

if __name__ == "__main__":
    main()
"""
                    self.logger.error(f"{Fore.RED}❌ All code generation attempts failed for task {task.id}")
                    return error_code
                    
                # Wait before retry
                time.sleep(2 ** attempt)
                
        return error_code  # This shouldn't be reached, but just in case

    def generate_task_metadata(self, task: Task) -> Metadata:
        """Generate metadata for a task with improved error handling."""
        system_message = """
        You are an AI expert in software development and poetry. Analyze the given task and its code to generate metadata.
        Provide a concise description, relevant tags, estimate the complexity (1-10), and estimated time to complete.
        Create a poetic description that captures the essence of the task using coding metaphors and imagery.
        """
        
        user_message = f"""
        Task: {task.description}
        
        Code:
        {task.code}
        
        Generate metadata including a concise description, relevant tags, complexity (1-10), 
        estimated time to complete, and a poetic description with coding metaphors.
        """

        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.logger.info(f"{Fore.BLUE}🔄 Generating metadata for task {task.id} (attempt {attempt + 1})")
                response = client.beta.chat.completions.parse(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message}
                    ],
                    response_format=MetadataResponse,
                )
                
                if not response.choices or not response.choices[0].message.parsed:
                    raise ValueError("Empty metadata response from OpenAI API")
                    
                metadata_response = response.choices[0].message.parsed
                
                generated_metadata = Metadata(
                    description=metadata_response.description,
                    tags=metadata_response.tags,
                    complexity=metadata_response.complexity,
                    estimated_time=metadata_response.estimated_time,
                    poetic_description=metadata_response.poetic_description
                )
                
                self.logger.info(f"{Fore.GREEN}✅ Metadata generated successfully for task {task.id}")
                return generated_metadata
                
            except Exception as e:
                self.logger.warning(f"{Fore.YELLOW}⚠️ Metadata generation attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_retries - 1:
                    fallback_metadata = Metadata(
                        description=task.description,
                        tags=["auto-generated", "fallback"],
                        complexity=5,
                        estimated_time="unknown",
                        poetic_description="A task wrapped in digital mystery, awaiting its moment to shine in the code."
                    )
                    self.logger.error(f"{Fore.RED}❌ All metadata generation attempts failed for task {task.id}")
                    return fallback_metadata
                
                time.sleep(2 ** attempt)
                
        return fallback_metadata  # This shouldn't be reached

    def execute_task_code(self, task: Task, workspace_path: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute task code with enhanced error handling and timeout management."""
        task_filename = os.path.join(workspace_path, f"{task.id}.py")
        
        try:
            # Ensure workspace directory exists
            os.makedirs(workspace_path, exist_ok=True)
            
            # Write code to file
            with open(task_filename, 'w', encoding='utf-8') as f:
                f.write(task.code)
            
            self.logger.info(f"{Fore.BLUE}🚀 Executing task {task.id} with timeout {timeout}s")
            self.logger.debug(f"Task file: {task_filename}")
            self.logger.debug(f"File exists: {os.path.exists(task_filename)}")
            
            # Execute with timeout - use just the filename since cwd is set to workspace_path
            result = subprocess.run(
                ['python', f"{task.id}.py"], 
                capture_output=True, 
                text=True, 
                timeout=timeout,
                cwd=workspace_path
            )
            
            execution_result = {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode,
                "execution_time": time.time(),  # Could be improved to measure actual execution time
                "task_file": task_filename
            }
            
            if execution_result["success"]:
                self.logger.info(f"{Fore.GREEN}✅ Task {task.id} executed successfully")
            else:
                self.logger.warning(f"{Fore.YELLOW}⚠️ Task {task.id} execution failed with return code {result.returncode}")
                self.logger.debug(f"STDOUT: {result.stdout}")
                self.logger.debug(f"STDERR: {result.stderr}")
            
            return execution_result
            
        except subprocess.TimeoutExpired:
            self.logger.warning(f"{Fore.YELLOW}⏳ Task {task.id} execution timed out after {timeout}s")
            return {
                "success": False, 
                "error": f"Execution timed out after {timeout} seconds",
                "timeout": True,
                "execution_time": timeout
            }
        except Exception as e:
            self.logger.error(f"{Fore.RED}❌ Error executing task {task.id}: {str(e)}")
            return {
                "success": False, 
                "error": str(e),
                "exception": True
            }
        finally:
            # Clean up temporary file
            try:
                if os.path.exists(task_filename):
                    os.remove(task_filename)
            except Exception as e:
                self.logger.warning(f"{Fore.YELLOW}⚠️ Failed to clean up task file {task_filename}: {str(e)}")

    def improve_task_code(self, task: Task, execution_result: Dict[str, Any]) -> str:
        """Improve task code based on execution results with targeted error analysis."""
        system_message = """
        You are an expert Python debugger and code optimizer. 
        Analyze the failed code execution and provide an improved version.
        Focus on fixing specific errors, improving performance, and adding robustness.
        Provide a complete, working implementation.
        """
        
        error_analysis = []
        if execution_result.get("timeout"):
            error_analysis.append("CODE TIMED OUT - Focus on performance optimization and efficiency")
        if execution_result.get("error"):
            error_analysis.append(f"EXECUTION ERROR: {execution_result['error']}")
        if execution_result.get("return_code", 0) != 0:
            error_analysis.append(f"Non-zero exit code: {execution_result['return_code']}")
            
        user_message = f"""
        Task: {task.description}
        
        Original Code:
        {task.code}
        
        Execution Issues:
        {chr(10).join(error_analysis)}
        
        Error Output:
        {execution_result.get('error', 'No error output')}
        
        Provide an improved version of the code that fixes these issues.
        """

        try:
            self.logger.info(f"{Fore.BLUE}🔧 Improving code for task {task.id}")
            response = client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                response_format=ScriptResponse,
            )
            
            script_response = response.choices[0].message.parsed
            main_code_block = next(
                (block for block in script_response.code_blocks if block.language.lower() == 'python'), 
                None
            )
            
            if main_code_block:
                self.logger.info(f"{Fore.GREEN}✅ Code improved for task {task.id}")
                return main_code_block.code
            else:
                raise ValueError("No Python code block found in improvement response")
                
        except Exception as e:
            self.logger.error(f"{Fore.RED}❌ Error improving task code: {str(e)}")
            # Return original code with error comments
            return f"""# ERROR: Failed to improve code - {str(e)}
# Original code returned as fallback

{task.code}
"""

    def update_task_status(self, task: Task, status: str) -> Task:
        """Update task status and timestamp."""
        task.status = status
        task.updated_at = datetime.now().isoformat()
        return task

    def validate_task(self, task: Task) -> List[str]:
        """Validate task completeness and return list of issues."""
        issues = []
        
        if not task.description.strip():
            issues.append("Task description is empty")
            
        if not task.code.strip():
            issues.append("Task code is empty")
            
        if task.metadata and task.metadata.complexity < 1:
            issues.append("Task complexity is invalid")
            
        # Basic Python syntax check
        try:
            compile(task.code, f"<task_{task.id}>", "exec")
        except SyntaxError as e:
            issues.append(f"Python syntax error: {str(e)}")
            
        return issues 