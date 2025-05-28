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
import sqlite3

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

class TaskGenerationResponse(BaseModel):
    task_description: str
    rationale: str

class AutonomousContinuousCodingEnvironment:
    def __init__(self, model: str = "o4-mini", workspace: str = "autonomous_continuous_workspace"):
        self.model = model
        self.workspace = workspace
        self.current_task: Optional[Task] = None
        self.activity_log: List[Dict[str, Any]] = []
        self.setup_workspace()
        self.init_database()

    def setup_workspace(self):
        """Set up a dedicated workspace for the autonomous coding environment."""
        try:
            if not os.path.exists(self.workspace):
                os.makedirs(self.workspace)
            self.log_activity("Workspace Setup", {"workspace": self.workspace})
        except Exception as e:
            error_msg = f"Error setting up workspace: {str(e)}"
            self.log_activity("Workspace Setup Failed", {"error": error_msg})
            raise

    def init_database(self):
        """Initialize the SQLite database for long-term memory."""
        db_path = os.path.join(self.workspace, "autonomous_system.db")
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                description TEXT,
                code TEXT,
                metadata TEXT,
                status TEXT,
                execution_result TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS learnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                learning TEXT
            )
        ''')
        self.conn.commit()
        self.log_activity("Database Initialized", {"path": db_path})

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

    def generate_task(self) -> Task:
        """Generate a new task using the AI model."""
        system_message = """
        You are an autonomous AI system capable of generating coding tasks and implementing them.
        Your goal is to create increasingly complex and interesting Python programming tasks.
        Consider the following when generating a task:
        1. Build upon previous tasks and learnings
        2. Explore new areas of programming and computer science
        3. Challenge yourself with tasks of varying complexity
        4. Create tasks that could potentially improve your own capabilities
        """

        try:
            self.log_activity("Generating New Task")
            response = client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": "Generate a new Python programming task."}
                ],
                response_format=TaskGenerationResponse,
            )
            task_gen = response.choices[0].message.parsed
            
            task_id = f"task_{int(time.time())}"
            new_task = Task(id=task_id, description=task_gen.task_description)
            self.log_activity("New Task Generated", {"task_id": task_id, "description": task_gen.task_description, "rationale": task_gen.rationale})
            return new_task
        except Exception as e:
            error_msg = f"Error generating task: {str(e)}"
            self.log_activity("Task Generation Failed", {"error": error_msg})
            raise

    def implement_task(self, task: Task) -> Task:
        """Implement the given task using the AI model."""
        system_message = """
        You are an expert Python developer tasked with implementing a specific coding task.
        Provide a complete and working implementation for the given task description.
        Include error handling, logging, and comments in your code.
        Also, add emojis in the comments to make the code more engaging and easier to understand.
        """
        
        user_message = f"Task: {task.description}\n\nImplement this task in Python."

        try:
            self.log_activity("Implementing Task", {"task_id": task.id})
            response = client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                response_format=ScriptResponse,
            )
            script_response = response.choices[0].message.parsed
            
            main_code_block = next((block for block in script_response.code_blocks if block.language.lower() == 'python'), None)
            
            if main_code_block:
                task.code = main_code_block.code
                task.metadata = self.generate_task_metadata(task)
                self.log_activity("Task Implemented", {"task_id": task.id})
                return task
            else:
                error_msg = f"No Python code block found in the response for task: {task.id}"
                self.log_activity("Task Implementation Failed", {"error": error_msg})
                task.status = "failed"
                return task
        except Exception as e:
            error_msg = f"Error implementing task: {str(e)}"
            self.log_activity("Task Implementation Failed", {"error": error_msg})
            task.status = "failed"
            return task

    def generate_task_metadata(self, task: Task) -> Metadata:
        """Generate metadata for the task, including a poetic description."""
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
            self.log_activity("Generating Task Metadata", {"task_id": task.id})
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
            self.log_activity("Task Metadata Generated", {"task_id": task.id, "metadata": generated_metadata.dict()})
            return generated_metadata
        except Exception as e:
            error_msg = f"Error generating task metadata: {str(e)}"
            self.log_activity("Metadata Generation Failed", {"error": error_msg})
            return Metadata(
                description=task.description,
                tags=["error"],
                complexity=5,
                estimated_time="unknown",
                poetic_description="A task shrouded in mystery, its true nature yet to be revealed."
            )

    def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute the given task and return the result."""
        task_filename = os.path.join(self.workspace, f"{task.id}.py")
        try:
            self.log_activity("Executing Task", {"task_id": task.id, "filename": task_filename})
            with open(task_filename, 'w') as f:
                f.write(task.code)
            
            result = subprocess.run(['python', task_filename], capture_output=True, text=True, timeout=30)
            
            execution_result = {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr
            }
            self.log_activity("Task Execution Completed", {"task_id": task.id, "result": execution_result})
            return execution_result
        except subprocess.TimeoutExpired:
            error_msg = f"Task execution timed out: {task.id}"
            self.log_activity("Task Execution Timed Out", {"error": error_msg})
            return {"success": False, "error": "Execution timed out"}
        except Exception as e:
            error_msg = f"Error executing task: {str(e)}"
            self.log_activity("Task Execution Failed", {"error": error_msg})
            return {"success": False, "error": str(e)}

    def improve_task(self, task: Task) -> Task:
        """Improve the task implementation based on execution results."""
        if task.execution_result["success"]:
            self.log_activity("Task Improvement Skipped", {"reason": "Task already successful"})
            return task

        system_message = """
        You are an expert Python developer tasked with improving code that failed to execute correctly.
        Analyze the error message and the original code, then provide an improved implementation that addresses the issues.
        Include error handling, logging, and comments in your code.
        Also, add emojis in the comments to make the code more engaging and easier to understand.
        """
        
        user_message = f"""
        Original task: {task.description}
        
        Original code:
        {task.code}
        
        Error message:
        {task.execution_result['error']}
        
        Improve the code to fix the error and implement the task correctly.
        """

        try:
            self.log_activity("Improving Task", {"task_id": task.id})
            response = client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                response_format=ScriptResponse,
            )
            script_response = response.choices[0].message.parsed
            
            main_code_block = next((block for block in script_response.code_blocks if block.language.lower() == 'python'), None)
            
            if main_code_block:
                task.code = main_code_block.code
                self.log_activity("Task Improved", {"task_id": task.id})
                return task
            else:
                error_msg = f"No Python code block found in the improved response for task: {task.id}"
                self.log_activity("Task Improvement Failed", {"error": error_msg})
                return task
        except Exception as e:
            error_msg = f"Error improving task: {str(e)}"
            self.log_activity("Task Improvement Failed", {"error": error_msg})
            return task

    def save_task_to_database(self, task: Task):
        """Save the task to the SQLite database."""
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO tasks (id, description, code, metadata, status, execution_result)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                task.id,
                task.description,
                task.code,
                json.dumps(task.metadata.dict() if task.metadata else None),
                task.status,
                json.dumps(task.execution_result) if task.execution_result else None
            ))
            self.conn.commit()
            self.log_activity("Task Saved to Database", {"task_id": task.id})
        except Exception as e:
            error_msg = f"Error saving task to database: {str(e)}"
            self.log_activity("Database Save Failed", {"error": error_msg})

    def add_learning(self, learning: str):
        """Add a new learning to the database."""
        try:
            self.cursor.execute('''
                INSERT INTO learnings (timestamp, learning)
                VALUES (?, ?)
            ''', (datetime.now().isoformat(), learning))
            self.conn.commit()
            self.log_activity("New Learning Added", {"learning": learning})
        except Exception as e:
            error_msg = f"Error adding learning to database: {str(e)}"
            self.log_activity("Learning Addition Failed", {"error": error_msg})

    def get_recent_learnings(self, limit: int = 5) -> List[str]:
        """Retrieve the most recent learnings from the database."""
        try:
            self.cursor.execute('''
                SELECT learning FROM learnings
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            return [row[0] for row in self.cursor.fetchall()]
        except Exception as e:
            error_msg = f"Error retrieving recent learnings: {str(e)}"
            self.log_activity("Learning Retrieval Failed", {"error": error_msg})
            return []

    def reflect_on_task(self, task: Task):
        """Reflect on the completed task and generate learnings."""
        system_message = """
        You are an AI system reflecting on a completed coding task.
        Analyze the task description, implementation, and execution result to generate insights and learnings.
        Focus on what went well, what could be improved, and any new concepts or techniques that were explored.
        """

        user_message = f"""
        Task Description: {task.description}
        
        Implementation:
        {task.code}
        
        Execution Result:
        {json.dumps(task.execution_result, indent=2)}
        
        Metadata:
        {json.dumps(task.metadata.dict(), indent=2)}
        
        Generate 1-3 key learnings from this task.
        """

        try:
            self.log_activity("Reflecting on Task", {"task_id": task.id})
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ]
            )
            learnings = response.choices[0].message.content.strip().split('\n')
            for learning in learnings:
                self.add_learning(learning)
            self.log_activity("Task Reflection Completed", {"task_id": task.id, "learnings": learnings})
        except Exception as e:
            error_msg = f"Error reflecting on task: {str(e)}"
            self.log_activity("Task Reflection Failed", {"error": error_msg})

    def run_continuous_loop(self):
        """Run the autonomous continuous coding environment."""
        try:
            print(f"{Fore.CYAN}=== Autonomous Continuous Coding Environment ===")
            print(f"{Fore.YELLOW}Press Ctrl+C to stop the environment at any time.")
            
            while True:
                # Generate a new task
                self.current_task = self.generate_task()
                print(f"\n{Fore.GREEN}New Task Generated: {self.current_task.description}")

                # Implement the task
                self.current_task = self.implement_task(self.current_task)
                print(f"\n{Fore.CYAN}Task Implemented:")
                print(f"{Fore.WHITE}{self.current_task.code}")

                # Execute the task
                self.current_task.execution_result = self.execute_task(self.current_task)

                if self.current_task.execution_result["success"]:
                    self.current_task.status = "completed"
                    print(f"\n{Fore.GREEN}✅ Task executed successfully!")
                    print(f"{Fore.WHITE}Output:\n{self.current_task.execution_result['output']}")
                else:
                    self.current_task.status = "failed"
                    print(f"\n{Fore.RED}❌ Task execution failed.")
                    print(f"{Fore.WHITE}Error:\n{self.current_task.execution_result['error']}")

                    print(f"\n{Fore.YELLOW}Attempting to improve the task...")
                    self.current_task = self.improve_task(self.current_task)

                    print(f"\n{Fore.YELLOW}Re-executing improved task...")
                    self.current_task.execution_result = self.execute_task(self.current_task)

                    if self.current_task.execution_result["success"]:
                        self.current_task.status = "completed"
                        print(f"\n{Fore.GREEN}✅ Improved task executed successfully!")
                        print(f"{Fore.WHITE}Output:\n{self.current_task.execution_result['output']}")
                    else:
                        print(f"\n{Fore.RED}❌ Improved task execution failed.")
                        print(f"{Fore.WHITE}Error:\n{self.current_task.execution_result['error']}")

                # Reflect on the task
                self.reflect_on_task(self.current_task)

                # Save the task to the database
                self.save_task_to_database(self.current_task)

                # Display recent learnings
                recent_learnings = self.get_recent_learnings()
                print(f"\n{Fore.CYAN}=== Recent Learnings ===")
                for learning in recent_learnings:
                    print(f"{Fore.WHITE}• {learning}")

                print(f"\n{Fore.YELLOW}Waiting for 10 seconds before starting the next task...")
                time.sleep(10)

        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Autonomous Continuous Coding Environment stopped by user.")
        except Exception as e:
            logger.critical(f"{Fore.RED}💥 Critical error: {str(e)}")
            logger.critical(traceback.format_exc())
        finally:
            self.conn.close()
            print(f"\n{Fore.CYAN}=== Final Statistics ===")
            print(f"{Fore.WHITE}Total tasks attempted: {len(self.activity_log)}")
            print(f"Database and logs saved in: {self.workspace}")

    def run(self):
        """Start the autonomous continuous coding environment."""
        try:
            self.run_continuous_loop()
        except Exception as e:
            logger.critical(f"{Fore.RED}💥 Critical error in main run loop: {str(e)}")
            logger.critical(traceback.format_exc())
        finally:
            self.conn.close()

if __name__ == "__main__":
    try:
        env = AutonomousContinuousCodingEnvironment(workspace="autonomous_continuous_workspace")
        env.run()
    except Exception as e:
        logger.critical(f"{Fore.RED}💥 Critical error: {str(e)}")
        logger.critical(traceback.format_exc())


# [ACTIVITY] Workspace Setup
# {
#   "workspace": "autonomous_continuous_workspace"
# }
# 2024-08-14 00:28:34,630 - INFO - [ACTIVITY] Workspace Setup
# {
#   "workspace": "autonomous_continuous_workspace"
# }
# [ACTIVITY] Database Initialized
# {
#   "path": "autonomous_continuous_workspace/autonomous_system.db"
# }
# 2024-08-14 00:28:34,664 - INFO - [ACTIVITY] Database Initialized
# {
#   "path": "autonomous_continuous_workspace/autonomous_system.db"
# }
# === Autonomous Continuous Coding Environment ===
# Press Ctrl+C to stop the environment at any time.
# [ACTIVITY] Generating New Task
# 2024-08-14 00:28:34,664 - INFO - [ACTIVITY] Generating New Task
# 2024-08-14 00:28:40,783 - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
# [ACTIVITY] New Task Generated
# {
#   "task_id": "task_1723609720",
#   "description": "Create a Python program that implements a simple voting system for a fictional election. The program should allow users to create candidates, view the list of candidates, cast votes for them, and display the results. Implement features to ensure that each user can only vote once. Use classes to structure the candidates and voters, and store the votes in a dictionary. The program should also handle invalid inputs gracefully, such as when a user tries to vote for a candidate that does not exist or tries to vote twice.",
#   "rationale": "This task builds upon basic object-oriented programming concepts by requiring the implementation of classes and methods. It also introduces more advanced topics such as data structure usage (dictionaries), handling user input, and maintaining state (voter registration). It encourages thinking about user experience through input validation and error handling."
# }
# 2024-08-14 00:28:40,853 - INFO - [ACTIVITY] New Task Generated
# {
#   "task_id": "task_1723609720",
#   "description": "Create a Python program that implements a simple voting system for a fictional election. The program should allow users to create candidates, view the list of candidates, cast votes for them, and display the results. Implement features to ensure that each user can only vote once. Use classes to structure the candidates and voters, and store the votes in a dictionary. The program should also handle invalid inputs gracefully, such as when a user tries to vote for a candidate that does not exist or tries to vote twice.",
#   "rationale": "This task builds upon basic object-oriented programming concepts by requiring the implementation of classes and methods. It also introduces more advanced topics such as data structure usage (dictionaries), handling user input, and maintaining state (voter registration). It encourages thinking about user experience through input validation and error handling."
# }

# New Task Generated: Create a Python program that implements a simple voting system for a fictional election. The program should allow users to create candidates, view the list of candidates, cast votes for them, and display the results. Implement features to ensure that each user can only vote once. Use classes to structure the candidates and voters, and store the votes in a dictionary. The program should also handle invalid inputs gracefully, such as when a user tries to vote for a candidate that does not exist or tries to vote twice.
# [ACTIVITY] Implementing Task
# {
#   "task_id": "task_1723609720"
# }
# 2024-08-14 00:28:40,854 - INFO - [ACTIVITY] Implementing Task
# {
#   "task_id": "task_1723609720"
# }
# 2024-08-14 00:28:43,035 - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 500 Internal Server Error"
# 2024-08-14 00:28:43,035 - INFO - Retrying request to /chat/completions in 0.819104 seconds
# 2024-08-14 00:28:53,457 - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
# [ACTIVITY] Generating Task Metadata
# {
#   "task_id": "task_1723609720"
# }
# 2024-08-14 00:28:53,475 - INFO - [ACTIVITY] Generating Task Metadata
# {
#   "task_id": "task_1723609720"
# }
# 2024-08-14 00:29:01,052 - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
# [ACTIVITY] Task Metadata Generated
# {
#   "task_id": "task_1723609720",
#   "metadata": {
#     "description": "This Python program implements a simple voting system for a fictional election, allowing users to create candidates, cast votes, and display results while ensuring each voter can only vote once and handling invalid inputs gracefully.",
#     "tags": [
#       "Python",
#       "Voting System",
#       "Election",
#       "Object-Oriented Programming",
#       "User Input Handling",
#       "Logging"
#     ],
#     "complexity": 4,
#     "estimated_time": "2-3 hours",
#     "poetic_description": "In the realm of choices, fair and bright,  \nA system unfolds to guide the vote's light.  \nCandidates arise, names in the air,  \nAs ballots are cast, hope and dreams laid bare."
#   }
# }
# 2024-08-14 00:29:01,069 - INFO - [ACTIVITY] Task Metadata Generated
# {
#   "task_id": "task_1723609720",
#   "metadata": {
#     "description": "This Python program implements a simple voting system for a fictional election, allowing users to create candidates, cast votes, and display results while ensuring each voter can only vote once and handling invalid inputs gracefully.",
#     "tags": [
#       "Python",
#       "Voting System",
#       "Election",
#       "Object-Oriented Programming",
#       "User Input Handling",
#       "Logging"
#     ],
#     "complexity": 4,
#     "estimated_time": "2-3 hours",
#     "poetic_description": "In the realm of choices, fair and bright,  \nA system unfolds to guide the vote's light.  \nCandidates arise, names in the air,  \nAs ballots are cast, hope and dreams laid bare."
#   }
# }
# [ACTIVITY] Task Implemented
# {
#   "task_id": "task_1723609720"
# }
# 2024-08-14 00:29:01,069 - INFO - [ACTIVITY] Task Implemented
# {
#   "task_id": "task_1723609720"
# }

# Task Implemented:
# import logging

# # Configuring logging 📝
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# class Candidate:
#     """Represents a candidate in the voting system."""
#     def __init__(self, name):
#         self.name = name
#         self.votes = 0

#     def __str__(self):
#         return f'{self.name}: {self.votes} votes'

# class VotingSystem:
#     """Manages the voting process and ensures that users can only vote once."""
#     def __init__(self):
#         self.candidates = {}  # Dictionary to store candidates
#         self.voters = set()   # Set to track who has voted

#     def add_candidate(self, name):
#         """Adds a new candidate to the voting system."""
#         if name in self.candidates:
#             logging.warning('Candidate %s already exists!', name)  # Log warning 🚨
#             raise ValueError('Candidate already exists')
#         self.candidates[name] = Candidate(name)
#         logging.info('Added candidate: %s', name)  # Log info message 🗳️

#     def vote(self, voter_name, candidate_name):
#         """Records a vote for a candidate from a voter."""
#         if voter_name in self.voters:
#             logging.error('Voter %s has already voted!', voter_name)  # Log error ❌
#             raise ValueError('You already voted')
#         if candidate_name not in self.candidates:
#             logging.error('Candidate %s does not exist!', candidate_name)  # Log error ❌
#             raise ValueError('Candidate does not exist')

#         self.candidates[candidate_name].votes += 1
#         self.voters.add(voter_name)  # Mark this voter as having voted
#         logging.info('Voter %s voted for %s', voter_name, candidate_name)  # Log info message 🗳️

#     def display_results(self):
#         """Displays the voting results for all candidates."""
#         logging.info('Displaying voting results...')  # Log info message 📊
#         for candidate in self.candidates.values():
#             print(candidate)

# def main():
#     system = VotingSystem()
#     while True:
#         print('\nWelcome to the Voting System! Please choose an action:')
#         print('1. Add a candidate')
#         print('2. Vote')
#         print('3. Display results')
#         print('4. Exit')
#         action = input('Enter action number: ')  # User input for action

#         try:
#             if action == '1':
#                 candidate_name = input('Enter the candidate name: ')
#                 system.add_candidate(candidate_name)
#             elif action == '2':
#                 voter_name = input('Enter your name: ')  # Voter's name
#                 candidate_name = input('Enter the candidate name to vote for: ')
#                 system.vote(voter_name, candidate_name)
#             elif action == '3':
#                 system.display_results()
#             elif action == '4':
#                 logging.info('Exiting voting system.')  # Log info message 🚪
#                 break
#             else:
#                 print('Invalid action! Please choose a valid option.')  # Invalid action
#         except ValueError as e:
#             print(e)  # Display the error to the user

# if __name__ == '__main__':
#     main()  # Start the voting system application 🎉
# [ACTIVITY] Executing Task
# {
#   "task_id": "task_1723609720",
#   "filename": "autonomous_continuous_workspace/task_1723609720.py"
# }
# 2024-08-14 00:29:01,070 - INFO - [ACTIVITY] Executing Task
# {
#   "task_id": "task_1723609720",
#   "filename": "autonomous_continuous_workspace/task_1723609720.py"
# }
# [ACTIVITY] Task Execution Timed Out
# {
#   "error": "Task execution timed out: task_1723609720"
# }
# 2024-08-14 00:29:31,102 - INFO - [ACTIVITY] Task Execution Timed Out
# {
#   "error": "Task execution timed out: task_1723609720"
# }

# ❌ Task execution failed.
# Error:
# Execution timed out

# Attempting to improve the task...
# [ACTIVITY] Improving Task
# {
#   "task_id": "task_1723609720"
# }
# 2024-08-14 00:29:31,103 - INFO - [ACTIVITY] Improving Task
# {
#   "task_id": "task_1723609720"
# }
# 2024-08-14 00:29:39,551 - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
# [ACTIVITY] Task Improved
# {
#   "task_id": "task_1723609720"
# }
# 2024-08-14 00:29:39,558 - INFO - [ACTIVITY] Task Improved
# {
#   "task_id": "task_1723609720"
# }

# Re-executing improved task...
# [ACTIVITY] Executing Task
# {
#   "task_id": "task_1723609720",
#   "filename": "autonomous_continuous_workspace/task_1723609720.py"
# }
# 2024-08-14 00:29:39,559 - INFO - [ACTIVITY] Executing Task
# {
#   "task_id": "task_1723609720",
#   "filename": "autonomous_continuous_workspace/task_1723609720.py"
# }
# [ACTIVITY] Task Execution Timed Out
# {
#   "error": "Task execution timed out: task_1723609720"
# }
# 2024-08-14 00:30:09,597 - INFO - [ACTIVITY] Task Execution Timed Out
# {
#   "error": "Task execution timed out: task_1723609720"
# }

# ❌ Improved task execution failed.
# Error:
# Execution timed out
# [ACTIVITY] Reflecting on Task
# {
#   "task_id": "task_1723609720"
# }
# 2024-08-14 00:30:09,598 - INFO - [ACTIVITY] Reflecting on Task
# {
#   "task_id": "task_1723609720"
# }
# 2024-08-14 00:30:14,926 - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
# [ACTIVITY] New Learning Added
# {
#   "learning": "1. **Effective Use of Object-Oriented Programming**: The implementation successfully utilized classes to structure the voting system. The `Candidate` class neatly encapsulates candidate-related data, while the `VotingSystem` class manages the overall voting logic. This approach enhances code organization, making it easier to maintain and scale if new features were to be introduced in the future."
# }
# 2024-08-14 00:30:14,939 - INFO - [ACTIVITY] New Learning Added
# {
#   "learning": "1. **Effective Use of Object-Oriented Programming**: The implementation successfully utilized classes to structure the voting system. The `Candidate` class neatly encapsulates candidate-related data, while the `VotingSystem` class manages the overall voting logic. This approach enhances code organization, making it easier to maintain and scale if new features were to be introduced in the future."
# }
# [ACTIVITY] New Learning Added
# {
#   "learning": ""
# }
# 2024-08-14 00:30:14,955 - INFO - [ACTIVITY] New Learning Added
# {
#   "learning": ""
# }
# [ACTIVITY] New Learning Added
# {
#   "learning": "2. **Robust Input Validation and Error Handling**: The program showcased a comprehensive way of handling invalid inputs. By checking whether a candidate exists and ensuring that each voter can only vote once, the system prevented common issues that could lead to incorrect voting results. The use of exception handling with `try` and `except` blocks ensures that users are informed of mistakes gracefully without crashing the program, enhancing user experience."
# }
# 2024-08-14 00:30:14,966 - INFO - [ACTIVITY] New Learning Added
# {
#   "learning": "2. **Robust Input Validation and Error Handling**: The program showcased a comprehensive way of handling invalid inputs. By checking whether a candidate exists and ensuring that each voter can only vote once, the system prevented common issues that could lead to incorrect voting results. The use of exception handling with `try` and `except` blocks ensures that users are informed of mistakes gracefully without crashing the program, enhancing user experience."
# }
# [ACTIVITY] New Learning Added
# {
#   "learning": ""
# }
# 2024-08-14 00:30:14,978 - INFO - [ACTIVITY] New Learning Added
# {
#   "learning": ""
# }
# [ACTIVITY] New Learning Added
# {
#   "learning": "3. **Logging for Transparency and Debugging**: Implementing the logging module added a layer of transparency to the program's operations. Each major action, such as adding candidates or casting votes, is accompanied by an appropriate log message. This not only aids in debugging by providing a trail of actions taken but also allows for future performance monitoring or system audits, as logs can be reviewed to understand user interactions and identify any issues that arise during operation. However, careful setup of the logger level is critical to avoid flooding logs with excessive information. "
# }
# 2024-08-14 00:30:14,990 - INFO - [ACTIVITY] New Learning Added
# {
#   "learning": "3. **Logging for Transparency and Debugging**: Implementing the logging module added a layer of transparency to the program's operations. Each major action, such as adding candidates or casting votes, is accompanied by an appropriate log message. This not only aids in debugging by providing a trail of actions taken but also allows for future performance monitoring or system audits, as logs can be reviewed to understand user interactions and identify any issues that arise during operation. However, careful setup of the logger level is critical to avoid flooding logs with excessive information. "
# }
# [ACTIVITY] New Learning Added
# {
#   "learning": ""
# }
# 2024-08-14 00:30:15,005 - INFO - [ACTIVITY] New Learning Added
# {
#   "learning": ""
# }
# [ACTIVITY] New Learning Added
# {
#   "learning": "### Improvement Opportunities:"
# }
# 2024-08-14 00:30:15,016 - INFO - [ACTIVITY] New Learning Added
# {
#   "learning": "### Improvement Opportunities:"
# }
# [ACTIVITY] New Learning Added
# {
#   "learning": "- **Timeout Error Handling**: The execution timed out, suggesting that there might have been an infinite loop or excessive waiting in the code. Adding conditions to break out of loops or refining user input handling could help mitigate this issue, ensuring the program runs efficiently without getting stuck."
# }
# 2024-08-14 00:30:15,028 - INFO - [ACTIVITY] New Learning Added
# {
#   "learning": "- **Timeout Error Handling**: The execution timed out, suggesting that there might have been an infinite loop or excessive waiting in the code. Adding conditions to break out of loops or refining user input handling could help mitigate this issue, ensuring the program runs efficiently without getting stuck."
# }
# [ACTIVITY] New Learning Added
# {
#   "learning": ""
# }
# 2024-08-14 00:30:15,039 - INFO - [ACTIVITY] New Learning Added
# {
#   "learning": ""
# }
# [ACTIVITY] New Learning Added
# {
#   "learning": "- **Improved User Interface**: While a command-line interface is sufficient for basic interaction, enhancing the user prompts and outputs could further improve user experience. Implementing clear instructions and feedback after each action could guide users more effectively, particularly when input errors occur."
# }
# 2024-08-14 00:30:15,051 - INFO - [ACTIVITY] New Learning Added
# {
#   "learning": "- **Improved User Interface**: While a command-line interface is sufficient for basic interaction, enhancing the user prompts and outputs could further improve user experience. Implementing clear instructions and feedback after each action could guide users more effectively, particularly when input errors occur."
# }
# [ACTIVITY] New Learning Added
# {
#   "learning": ""
# }
# 2024-08-14 00:30:15,065 - INFO - [ACTIVITY] New Learning Added
# {
#   "learning": ""
# }
# [ACTIVITY] New Learning Added
# {
#   "learning": "- **Unit Testing**: To ensure the reliability of the voting system, adding unit tests would be beneficial. These tests can verify the correctness of individual components, such as vote counting and candidate addition, reducing the risk of undetected bugs in future code updates."
# }
# 2024-08-14 00:30:15,079 - INFO - [ACTIVITY] New Learning Added
# {
#   "learning": "- **Unit Testing**: To ensure the reliability of the voting system, adding unit tests would be beneficial. These tests can verify the correctness of individual components, such as vote counting and candidate addition, reducing the risk of undetected bugs in future code updates."
# }
# [ACTIVITY] Task Reflection Completed
# {
#   "task_id": "task_1723609720",
#   "learnings": [
#     "1. **Effective Use of Object-Oriented Programming**: The implementation successfully utilized classes to structure the voting system. The `Candidate` class neatly encapsulates candidate-related data, while the `VotingSystem` class manages the overall voting logic. This approach enhances code organization, making it easier to maintain and scale if new features were to be introduced in the future.",
#     "",
#     "2. **Robust Input Validation and Error Handling**: The program showcased a comprehensive way of handling invalid inputs. By checking whether a candidate exists and ensuring that each voter can only vote once, the system prevented common issues that could lead to incorrect voting results. The use of exception handling with `try` and `except` blocks ensures that users are informed of mistakes gracefully without crashing the program, enhancing user experience.",
#     "",
#     "3. **Logging for Transparency and Debugging**: Implementing the logging module added a layer of transparency to the program's operations. Each major action, such as adding candidates or casting votes, is accompanied by an appropriate log message. This not only aids in debugging by providing a trail of actions taken but also allows for future performance monitoring or system audits, as logs can be reviewed to understand user interactions and identify any issues that arise during operation. However, careful setup of the logger level is critical to avoid flooding logs with excessive information. ",
#     "",
#     "### Improvement Opportunities:",
#     "- **Timeout Error Handling**: The execution timed out, suggesting that there might have been an infinite loop or excessive waiting in the code. Adding conditions to break out of loops or refining user input handling could help mitigate this issue, ensuring the program runs efficiently without getting stuck.",
#     "",
#     "- **Improved User Interface**: While a command-line interface is sufficient for basic interaction, enhancing the user prompts and outputs could further improve user experience. Implementing clear instructions and feedback after each action could guide users more effectively, particularly when input errors occur.",
#     "",
#     "- **Unit Testing**: To ensure the reliability of the voting system, adding unit tests would be beneficial. These tests can verify the correctness of individual components, such as vote counting and candidate addition, reducing the risk of undetected bugs in future code updates."
#   ]
# }
# 2024-08-14 00:30:15,081 - INFO - [ACTIVITY] Task Reflection Completed
# {
#   "task_id": "task_1723609720",
#   "learnings": [
#     "1. **Effective Use of Object-Oriented Programming**: The implementation successfully utilized classes to structure the voting system. The `Candidate` class neatly encapsulates candidate-related data, while the `VotingSystem` class manages the overall voting logic. This approach enhances code organization, making it easier to maintain and scale if new features were to be introduced in the future.",
#     "",
#     "2. **Robust Input Validation and Error Handling**: The program showcased a comprehensive way of handling invalid inputs. By checking whether a candidate exists and ensuring that each voter can only vote once, the system prevented common issues that could lead to incorrect voting results. The use of exception handling with `try` and `except` blocks ensures that users are informed of mistakes gracefully without crashing the program, enhancing user experience.",
#     "",
#     "3. **Logging for Transparency and Debugging**: Implementing the logging module added a layer of transparency to the program's operations. Each major action, such as adding candidates or casting votes, is accompanied by an appropriate log message. This not only aids in debugging by providing a trail of actions taken but also allows for future performance monitoring or system audits, as logs can be reviewed to understand user interactions and identify any issues that arise during operation. However, careful setup of the logger level is critical to avoid flooding logs with excessive information. ",
#     "",
#     "### Improvement Opportunities:",
#     "- **Timeout Error Handling**: The execution timed out, suggesting that there might have been an infinite loop or excessive waiting in the code. Adding conditions to break out of loops or refining user input handling could help mitigate this issue, ensuring the program runs efficiently without getting stuck.",
#     "",
#     "- **Improved User Interface**: While a command-line interface is sufficient for basic interaction, enhancing the user prompts and outputs could further improve user experience. Implementing clear instructions and feedback after each action could guide users more effectively, particularly when input errors occur.",
#     "",
#     "- **Unit Testing**: To ensure the reliability of the voting system, adding unit tests would be beneficial. These tests can verify the correctness of individual components, such as vote counting and candidate addition, reducing the risk of undetected bugs in future code updates."
#   ]
# }
# [ACTIVITY] Task Saved to Database
# {
#   "task_id": "task_1723609720"
# }
# 2024-08-14 00:30:15,096 - INFO - [ACTIVITY] Task Saved to Database
# {
#   "task_id": "task_1723609720"
# }

# === Recent Learnings ===
# • - **Unit Testing**: To ensure the reliability of the voting system, adding unit tests would be beneficial. These tests can verify the correctness of individual components, such as vote counting and candidate addition, reducing the risk of undetected bugs in future code updates.
# • 
# • - **Improved User Interface**: While a command-line interface is sufficient for basic interaction, enhancing the user prompts and outputs could further improve user experience. Implementing clear instructions and feedback after each action could guide users more effectively, particularly when input errors occur.
# • 
# • - **Timeout Error Handling**: The execution timed out, suggesting that there might have been an infinite loop or excessive waiting in the code. Adding conditions to break out of loops or refining user input handling could help mitigate this issue, ensuring the program runs efficiently without getting stuck.

# Waiting for 10 seconds before starting the next task...
# [ACTIVITY] Generating New Task
# 2024-08-14 00:30:25,098 - INFO - [ACTIVITY] Generating New Task
# 2024-08-14 00:30:33,244 - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
# [ACTIVITY] New Task Generated
# {
#   "task_id": "task_1723609833",
#   "description": "Create a command-line-based contact management application in Python. The application should allow users to add, view, search, and delete contacts. Each contact should have a name, phone number, and email address. Store the contacts in a JSON file and ensure that all data is persisted across sessions. Implement error handling for invalid inputs such as duplicate contacts, incorrect email formats, and missing fields when adding a new contact. Additionally, include a feature to list all contacts sorted by name.",
#   "rationale": "This task builds upon prior knowledge of handling data structures, file I/O, and input validation in Python. It challenges the developer to implement a complete CLI application with basic CRUD (Create, Read, Update, Delete) functionality while also reinforcing skills in data persistence and validation. The use of JSON introduces the developer to serialization and deserialization concepts, enhancing their understanding of data management in programming."
# }
# 2024-08-14 00:30:33,251 - INFO - [ACTIVITY] New Task Generated
# {
#   "task_id": "task_1723609833",
#   "description": "Create a command-line-based contact management application in Python. The application should allow users to add, view, search, and delete contacts. Each contact should have a name, phone number, and email address. Store the contacts in a JSON file and ensure that all data is persisted across sessions. Implement error handling for invalid inputs such as duplicate contacts, incorrect email formats, and missing fields when adding a new contact. Additionally, include a feature to list all contacts sorted by name.",
#   "rationale": "This task builds upon prior knowledge of handling data structures, file I/O, and input validation in Python. It challenges the developer to implement a complete CLI application with basic CRUD (Create, Read, Update, Delete) functionality while also reinforcing skills in data persistence and validation. The use of JSON introduces the developer to serialization and deserialization concepts, enhancing their understanding of data management in programming."
# }

# New Task Generated: Create a command-line-based contact management application in Python. The application should allow users to add, view, search, and delete contacts. Each contact should have a name, phone number, and email address. Store the contacts in a JSON file and ensure that all data is persisted across sessions. Implement error handling for invalid inputs such as duplicate contacts, incorrect email formats, and missing fields when adding a new contact. Additionally, include a feature to list all contacts sorted by name.
# [ACTIVITY] Implementing Task
# {
#   "task_id": "task_1723609833"
# }
# 2024-08-14 00:30:33,252 - INFO - [ACTIVITY] Implementing Task
# {
#   "task_id": "task_1723609833"
# }
# 2024-08-14 00:30:46,387 - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
# [ACTIVITY] Generating Task Metadata
# {
#   "task_id": "task_1723609833"
# }
# 2024-08-14 00:30:46,389 - INFO - [ACTIVITY] Generating Task Metadata
# {
#   "task_id": "task_1723609833"
# }
# 2024-08-14 00:30:48,311 - INFO - HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
# [ACTIVITY] Task Metadata Generated
# {
#   "task_id": "task_1723609833",
#   "metadata": {
#     "description": "A command-line-based contact management application in Python that allows users to add, view, search, and delete contacts, while handling errors and ensuring data persistence with JSON.",
#     "tags": [
#       "Python",
#       "Command-Line",
#       "Contact Management",
#       "JSON",
#       "Error Handling"
#     ],
#     "complexity": 5,
#     "estimated_time": "4-6 hours",
#     "poetic_description": "In a world where names and numbers bloom,  \nA keeper of contacts dispels all gloom.  \nWith each input, a story to spin,  \nA digital friend, let the search begin."
#   }
# }
# 2024-08-14 00:30:48,318 - INFO - [ACTIVITY] Task Metadata Generated
# {
#   "task_id": "task_1723609833",
#   "metadata": {
#     "description": "A command-line-based contact management application in Python that allows users to add, view, search, and delete contacts, while handling errors and ensuring data persistence with JSON.",
#     "tags": [
#       "Python",
#       "Command-Line",
#       "Contact Management",
#       "JSON",
#       "Error Handling"
#     ],
#     "complexity": 5,
#     "estimated_time": "4-6 hours",
#     "poetic_description": "In a world where names and numbers bloom,  \nA keeper of contacts dispels all gloom.  \nWith each input, a story to spin,  \nA digital friend, let the search begin."
#   }
# }
# [ACTIVITY] Task Implemented
# {
#   "task_id": "task_1723609833"
# }
# 2024-08-14 00:30:48,318 - INFO - [ACTIVITY] Task Implemented
# {
#   "task_id": "task_1723609833"
# }

# Task Implemented:
# import json  # Importing JSON module for data serialization
# import os  # Importing OS module for file path checks
# import re  # Importing regular expression module for email validation

# # Contact class to represent each contact entry
# class Contact:
#     def __init__(self, name, phone, email):
#         self.name = name
#         self.phone = phone
#         self.email = email

#     def __repr__(self):
#         return f'{self.name} | {self.phone} | {self.email}'

# # Function to load contacts from a JSON file
# def load_contacts(filename):
#     if not os.path.exists(filename):  # Check if file exists
#         return []  # Return empty list if no contacts file
#     with open(filename, 'r') as f:
#         return json.load(f)  # Load and return contacts from file

# # Function to save contacts to a JSON file
# def save_contacts(filename, contacts):
#     with open(filename, 'w') as f:
#         json.dump([contact.__dict__ for contact in contacts], f, indent=4)  # Save contacts data to file

# # Function to validate email format
# def is_valid_email(email):
#     pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
#     return re.match(pattern, email) is not None  # Validate the email format with regex

# # Function to check for duplicate contact
# def is_duplicate(contacts, new_contact):
#     return any(c.name == new_contact.name for c in contacts)  # Check if contact already exists by name

# # Function to display all contacts
# def display_contacts(contacts):
#     if not contacts:
#         print('No contacts available.')  # Message for no contacts
#         return
#     sorted_contacts = sorted(contacts, key=lambda c: c.name)  # Sort contacts by name
#     print('\nList of Contacts:')
#     print('Name | Phone | Email')
#     print('----------------------')
#     for contact in sorted_contacts:
#         print(contact)

# # Main function to drive the application
# def main():
#     filename = 'contacts.json'  # Filename for the contacts
#     contacts = load_contacts(filename)  # Load existing contacts

#     while True:
#         print('\n--- Contact Management Application ---')  # Application title
#         print('1. Add Contact')
#         print('2. View Contacts')
#         print('3. Search Contact')
#         print('4. Delete Contact')
#         print('5. Exit')

#         choice = input('Choose an option (1-5): ')  # User menu

#         if choice == '1':
#             name = input('Enter name: ')  # Name input
#             phone = input('Enter phone number: ')  # Phone number input
#             email = input('Enter email address: ')  # Email input

#             if not name or not phone or not email:
#                 print('Error: All fields must be filled. 🚫')  # Error for empty fields
#                 continue

#             if not is_valid_email(email):
#                 print('Error: Invalid email format. 📧')  # Error for invalid email
#                 continue

#             new_contact = Contact(name, phone, email)
#             if is_duplicate(contacts, new_contact):
#                 print('Error: Contact already exists. ❌')  # Error for duplicate contact
#                 continue

#             contacts.append(new_contact)  # Add new contact
#             save_contacts(filename, contacts)  # Save to file
#             print('Contact added successfully! ✔️')  # Success message

#         elif choice == '2':
#             display_contacts(contacts)  # Display all contacts

#         elif choice == '3':
#             search_name = input('Enter name to search: ')  # Search input
#             found_contacts = [c for c in contacts if search_name.lower() in c.name.lower()]
#             if found_contacts:
#                 print('Search Results:')
#                 for contact in found_contacts:
#                     print(contact)  # Display search results
#             else:
#                 print('No contacts found with that name. 🕵️‍♂️')  # No match found

#         elif choice == '4':
#             delete_name = input('Enter name to delete: ')  # Name to delete
#             contacts = [c for c in contacts if c.name.lower() != delete_name.lower()]  # Remove contact if name matches
#             save_contacts(filename, contacts)  # Save changes to file
#             print(f'Contact {delete_name} deleted successfully! 🗑️')  # Success message

#         elif choice == '5':
#             print('Exiting the application. Goodbye! 👋')  # Exit message
#             break  # Exit loop

#         else:
#             print('Invalid option. Please select a valid choice. ❓')  # Error for invalid option

# # Entry point of the script
# if __name__ == '__main__':
#     main()  # Run the main function
# [ACTIVITY] Executing Task
# {
#   "task_id": "task_1723609833",
#   "filename": "autonomous_continuous_workspace/task_1723609833.py"
# }
# 2024-08-14 00:30:48,321 - INFO - [ACTIVITY] Executing Task
# {
#   "task_id": "task_1723609833",
#   "filename": "autonomous_continuous_workspace/task_1723609833.py"
# }
# ^C
# Autonomous Continuous Coding Environment stopped by user.

# === Final Statistics ===
# Total tasks attempted: 36
# Database and logs saved in: autonomous_continuous_workspace
