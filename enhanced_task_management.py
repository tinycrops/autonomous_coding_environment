import json
from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel, Field
import openai
from colorama import Fore
import logging
from base_task_processor import Task, BaseTaskProcessor

client = openai.OpenAI()

class TaskDependency(BaseModel):
    task_id: str
    dependency_type: str = "requires"  # requires, suggests, blocks
    description: str = ""

class EnhancedTask(Task):
    dependencies: List[TaskDependency] = Field(default_factory=list)
    priority: int = Field(default=5, ge=1, le=10)
    estimated_duration: Optional[int] = None  # in minutes
    category: str = "general"

class TaskData(BaseModel):
    """Structured task data for decomposition response."""
    description: str
    priority: int = Field(default=5, ge=1, le=10)
    category: str = "general"
    estimated_duration: int = Field(default=45, description="Estimated duration in minutes")

class DependencyData(BaseModel):
    """Structured dependency data for decomposition response."""
    task_id: str
    depends_on: str
    type: str = "requires"
    description: str = ""

class TaskDecompositionResponse(BaseModel):
    tasks: List[TaskData] = Field(default_factory=list)
    dependencies: List[DependencyData] = Field(default_factory=list)
    summary: str

    class Config:
        extra = "forbid"  # This sets additionalProperties to false

class EnhancedTaskManager(BaseTaskProcessor):
    """Enhanced task management with dependency resolution and smart decomposition."""
    
    def __init__(self, model: str = "o4-mini"):
        super().__init__(model)
        self.logger = logging.getLogger(__name__)
    
    def decompose_project_to_tasks(self, project_name: str, project_description: str) -> List[EnhancedTask]:
        """Decompose a project into structured tasks with dependencies."""
        system_message = """
        You are an expert project manager and software architect.
        Break down the given project into specific, actionable coding tasks that focus on implementing the actual functionality.
        
        IMPORTANT: Focus on pure coding tasks only. Do NOT include:
        - Git repository setup
        - Package manager initialization  
        - Installing dependencies
        - Environment setup
        - CI/CD configuration
        
        DO include:
        - Core algorithm implementation
        - Function and class definitions
        - Data structure creation
        - Business logic implementation
        - Testing and validation code
        - Error handling
        - Documentation within code
        
        For each task, provide:
        - A clear, specific description of what code to implement
        - An estimated priority (1-10, where 10 is highest)
        - Category (core, feature, testing, documentation, utility)
        - Dependencies on other coding tasks
        
        Make tasks granular enough to be completed in 30-60 minutes each.
        Focus on building working, runnable Python code.
        """
        
        user_message = f"""
        Project: {project_name}
        Description: {project_description}
        
        Break this project down into specific coding tasks with:
        1. Clear task descriptions
        2. Priority levels (1-10)
        3. Categories (setup, core, feature, testing, documentation, etc.)
        4. Dependencies between tasks
        
        Return the response as a structured format with tasks and dependencies.
        """
        
        try:
            response = client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                response_format=TaskDecompositionResponse,
            )
            
            decomposition = response.choices[0].message.parsed
            tasks = []
            
            # Create tasks from response
            for i, task_data in enumerate(decomposition.tasks):
                task_id = f"task_{i+1:03d}"
                task = EnhancedTask(
                    id=task_id,
                    description=task_data.description,
                    priority=task_data.priority,
                    category=task_data.category,
                    estimated_duration=task_data.estimated_duration
                )
                tasks.append(task)
            
            # Add dependencies
            for dep_data in decomposition.dependencies:
                task_id = dep_data.task_id
                depends_on = dep_data.depends_on
                
                # Find the task and add dependency
                task = next((t for t in tasks if t.id == task_id), None)
                if task and depends_on:
                    dependency = TaskDependency(
                        task_id=depends_on,
                        dependency_type=dep_data.type,
                        description=dep_data.description
                    )
                    task.dependencies.append(dependency)
            
            self.logger.info(f"{Fore.GREEN}✅ Decomposed project into {len(tasks)} tasks")
            return tasks
            
        except Exception as e:
            self.logger.error(f"{Fore.RED}❌ Error decomposing project: {str(e)}")
            # Return a basic fallback task
            return [EnhancedTask(
                id="task_001",
                description=f"Implement: {project_description}",
                priority=5,
                category="general"
            )]
    
    def resolve_task_dependencies(self, tasks: List[EnhancedTask]) -> List[EnhancedTask]:
        """Resolve and validate task dependencies using topological sort."""
        # Create a mapping of task IDs to tasks
        task_map = {task.id: task for task in tasks}
        
        # Build dependency graph
        in_degree = {task.id: 0 for task in tasks}
        adj_list = {task.id: [] for task in tasks}
        
        for task in tasks:
            for dep in task.dependencies:
                if dep.task_id in task_map:
                    adj_list[dep.task_id].append(task.id)
                    in_degree[task.id] += 1
                else:
                    self.logger.warning(f"{Fore.YELLOW}⚠️ Invalid dependency: {task.id} -> {dep.task_id}")
        
        # Topological sort
        queue = [task_id for task_id, degree in in_degree.items() if degree == 0]
        sorted_tasks = []
        
        while queue:
            current_id = queue.pop(0)
            current_task = task_map[current_id]
            sorted_tasks.append(current_task)
            
            # Update in-degrees
            for neighbor in adj_list[current_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Check for circular dependencies
        if len(sorted_tasks) != len(tasks):
            remaining_tasks = [task for task in tasks if task not in sorted_tasks]
            self.logger.warning(f"{Fore.YELLOW}⚠️ Circular dependencies detected in tasks: {[t.id for t in remaining_tasks]}")
            # Add remaining tasks to the end
            sorted_tasks.extend(remaining_tasks)
        
        self.logger.info(f"{Fore.GREEN}✅ Resolved dependencies for {len(sorted_tasks)} tasks")
        return sorted_tasks
    
    def get_ready_tasks(self, tasks: List[EnhancedTask]) -> List[EnhancedTask]:
        """Get tasks that are ready to be executed (all dependencies completed)."""
        completed_tasks = {task.id for task in tasks if task.status == "completed"}
        ready_tasks = []
        
        for task in tasks:
            if task.status == "pending":
                # Check if all dependencies are completed
                required_deps = [dep.task_id for dep in task.dependencies if dep.dependency_type == "requires"]
                if all(dep_id in completed_tasks for dep_id in required_deps):
                    ready_tasks.append(task)
        
        # Sort by priority (highest first)
        ready_tasks.sort(key=lambda t: t.priority, reverse=True)
        return ready_tasks
    
    def get_task_execution_order(self, tasks: List[EnhancedTask]) -> List[List[EnhancedTask]]:
        """Get tasks grouped by execution phases (tasks that can run in parallel)."""
        resolved_tasks = self.resolve_task_dependencies(tasks)
        execution_phases = []
        remaining_tasks = resolved_tasks.copy()
        
        while remaining_tasks:
            current_phase = self.get_ready_tasks(remaining_tasks)
            if not current_phase:
                # Handle circular dependencies by adding all remaining tasks
                current_phase = [task for task in remaining_tasks if task.status == "pending"]
                if not current_phase:
                    break
            
            execution_phases.append(current_phase)
            
            # Mark current phase tasks as ready for next iteration
            for task in current_phase:
                task.status = "ready"
                remaining_tasks.remove(task)
        
        # Reset status
        for task in resolved_tasks:
            if task.status == "ready":
                task.status = "pending"
        
        return execution_phases
    
    def estimate_project_duration(self, tasks: List[EnhancedTask]) -> Dict[str, Any]:
        """Estimate project completion time considering dependencies."""
        execution_phases = self.get_task_execution_order(tasks)
        
        total_duration = 0
        parallel_duration = 0
        
        for phase in execution_phases:
            phase_duration = max(task.estimated_duration or 45 for task in phase)
            total_duration += phase_duration
            parallel_duration = max(parallel_duration, phase_duration)
        
        sequential_duration = sum(task.estimated_duration or 45 for task in tasks)
        
        return {
            "sequential_estimate_minutes": sequential_duration,
            "parallel_estimate_minutes": total_duration,
            "estimated_phases": len(execution_phases),
            "tasks_per_phase": [len(phase) for phase in execution_phases],
            "critical_path_duration": total_duration
        }

class ProjectOrchestrator:
    """Orchestrates project execution with dependency management."""
    
    def __init__(self, task_manager: EnhancedTaskManager, base_processor: BaseTaskProcessor):
        self.task_manager = task_manager
        self.base_processor = base_processor
        self.logger = logging.getLogger(__name__)
    
    def execute_project_with_dependencies(self, tasks: List[EnhancedTask], workspace_path: str) -> Dict[str, Any]:
        """Execute a project respecting task dependencies."""
        execution_phases = self.task_manager.get_task_execution_order(tasks)
        results = {"phases": [], "summary": {}}
        
        for phase_num, phase_tasks in enumerate(execution_phases):
            self.logger.info(f"{Fore.CYAN}🚀 Executing Phase {phase_num + 1}: {len(phase_tasks)} tasks")
            phase_results = []
            
            for task in phase_tasks:
                self.logger.info(f"{Fore.BLUE}▶️ Starting task: {task.id} - {task.description}")
                
                # Generate code if not present
                if not task.code:
                    task.code = self.base_processor.generate_code_for_task(task)
                
                # Execute task
                task.status = "in_progress"
                self.logger.debug(f"Executing task {task.id} in workspace: {workspace_path}")
                execution_result = self.base_processor.execute_task_code(task, workspace_path)
                
                # Handle results
                if execution_result["success"]:
                    task.status = "completed"
                    self.logger.info(f"{Fore.GREEN}✅ Task {task.id} completed successfully")
                else:
                    task.status = "failed"
                    self.logger.warning(f"{Fore.YELLOW}⚠️ Task {task.id} failed, attempting improvement")
                    
                    # Try to improve the task
                    improved_code = self.base_processor.improve_task_code(task, execution_result)
                    task.code = improved_code
                    
                    # Retry execution
                    retry_result = self.base_processor.execute_task_code(task, workspace_path)
                    if retry_result["success"]:
                        task.status = "completed"
                        self.logger.info(f"{Fore.GREEN}✅ Task {task.id} completed after improvement")
                        execution_result = retry_result
                    else:
                        self.logger.error(f"{Fore.RED}❌ Task {task.id} failed even after improvement")
                
                task.execution_result = execution_result
                phase_results.append({
                    "task_id": task.id,
                    "status": task.status,
                    "execution_result": execution_result
                })
            
            results["phases"].append({
                "phase_number": phase_num + 1,
                "tasks_executed": len(phase_tasks),
                "successful_tasks": len([r for r in phase_results if r["status"] == "completed"]),
                "failed_tasks": len([r for r in phase_results if r["status"] == "failed"]),
                "results": phase_results
            })
        
        # Generate summary
        all_tasks = [task for phase in execution_phases for task in phase]
        results["summary"] = {
            "total_tasks": len(all_tasks),
            "completed_tasks": len([t for t in all_tasks if t.status == "completed"]),
            "failed_tasks": len([t for t in all_tasks if t.status == "failed"]),
            "success_rate": len([t for t in all_tasks if t.status == "completed"]) / len(all_tasks) if all_tasks else 0,
            "total_phases": len(execution_phases)
        }
        
        return results 