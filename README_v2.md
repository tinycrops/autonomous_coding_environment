# ACE v2 - Enhanced Autonomous Coding Environment

## Overview

ACE v2 is a comprehensive autonomous coding environment that uses LLM-powered code generation with enhanced error handling, dependency management, comprehensive testing, and intelligent task reuse. This version addresses the key improvements identified in the original ACE system analysis.

## Key Improvements from v1

### 🏗️ **Modular Architecture**
- **Base Task Processor**: Consolidated core task processing logic with improved error handling
- **Enhanced Task Management**: Advanced dependency resolution and project decomposition
- **Testing Framework**: Automated test generation and validation
- **Task Orchestration**: Intelligent project execution with dependency awareness

### 🔧 **Enhanced Error Handling**
- Retry mechanisms with exponential backoff
- Targeted error analysis for code improvement
- Comprehensive timeout management
- Graceful fallback implementations

### 📋 **Advanced Task Management**
- Structured task decomposition with dependencies
- Topological sorting for dependency resolution
- Priority-based task scheduling
- Parallel execution phases

### 🧪 **Comprehensive Testing**
- Automated unit test generation
- Static code analysis
- Test execution and reporting
- Code quality validation

### 📚 **Intelligent Task Library**
- Task similarity detection
- Code reuse and adaptation
- Performance tracking
- Learning from past implementations

## System Components

### Core Components

1. **BaseTaskProcessor** (`base_task_processor.py`)
   - Core task processing functionality
   - Enhanced error handling and retries
   - Code generation and improvement
   - Task validation

2. **EnhancedTaskManager** (`enhanced_task_management.py`)
   - Project decomposition into tasks
   - Dependency resolution
   - Task scheduling and orchestration
   - Duration estimation

3. **ACETestFramework** (`ace_testing_framework.py`)
   - Automated test generation
   - Test execution and reporting
   - Static code analysis
   - Quality assessment

4. **ACEv2** (`ace_v2_enhanced.py`)
   - Main application orchestrator
   - Project management
   - CLI interface
   - Comprehensive reporting

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd autonomous_coding_environment
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up OpenAI API key:**
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```
   
   Or create a `.env` file:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

## Usage

### Basic Usage

Run the enhanced ACE v2 system:

```bash
python ace_v2_enhanced.py
```

### CLI Commands

1. **Create a new project**
   - Decomposes project into tasks with dependencies
   - Checks task library for similar implementations
   - Sets up project workspace

2. **List projects**
   - Shows all projects with status
   - Displays task counts and creation dates

3. **Execute project**
   - Runs tasks in dependency order
   - Optional comprehensive testing
   - Generates detailed reports

4. **View project status**
   - Shows task breakdown by status
   - Displays ready-to-run tasks
   - Project progress overview

5. **View task library**
   - Browse completed tasks
   - Search for reusable implementations

### Programmatic Usage

```python
from ace_v2_enhanced import ACEv2

# Initialize ACE v2
ace = ACEv2(model="o4-mini", workspace="my_workspace")

# Create a project
project_id = ace.create_project(
    name="Web Scraper",
    description="Build a web scraper for e-commerce sites with data cleaning and storage"
)

# Execute with testing
results = ace.execute_project(project_id, run_tests=True)

# Check results
print(f"Success rate: {results['summary']['success_rate']:.1%}")
```

## Project Structure

```
ace_v2_workspace/
├── projects/           # Individual project workspaces
│   ├── project_001/   # Generated code for project 001
│   └── project_002/   # Generated code for project 002
├── library/           # Task library storage
│   └── task_library.json
├── reports/           # Generated project reports
│   ├── project_001_report.md
│   └── project_002_report.md
└── tests/            # Generated test files
```

## Features

### Task Decomposition
- **Smart Breakdown**: AI-powered project decomposition into manageable tasks
- **Dependency Detection**: Automatic identification of task dependencies
- **Priority Assignment**: Task prioritization for optimal execution order
- **Category Classification**: Tasks organized by type (setup, core, feature, testing, etc.)

### Dependency Management
- **Topological Sorting**: Ensures tasks execute in correct dependency order
- **Circular Dependency Detection**: Identifies and handles circular dependencies
- **Parallel Execution**: Groups independent tasks for parallel execution
- **Duration Estimation**: Predicts project completion time

### Code Quality Assurance
- **Automated Testing**: Generates comprehensive test suites for each task
- **Static Analysis**: Validates code structure and quality
- **Error Recovery**: Intelligent code improvement based on execution results
- **Quality Metrics**: Tracks code quality across projects

### Task Library and Reuse
- **Similarity Detection**: Finds similar tasks in the library
- **Code Adaptation**: Adapts existing code for new requirements
- **Performance Tracking**: Monitors task execution success rates
- **Learning System**: Improves over time with more completed tasks

## Configuration

### Model Selection
```python
# Use different OpenAI models
ace = ACEv2(model="gpt-4")           # More capable, slower
ace = ACEv2(model="o4-mini")     # Faster, good balance
ace = ACEv2(model="gpt-3.5-turbo")   # Fastest, less capable
```

### Workspace Management
```python
# Custom workspace location
ace = ACEv2(workspace="/custom/path/workspace")

# Multiple workspaces for different projects
ace_web = ACEv2(workspace="web_projects")
ace_ml = ACEv2(workspace="ml_projects")
```

## Advanced Features

### Custom Task Processors
```python
from base_task_processor import BaseTaskProcessor

class CustomTaskProcessor(BaseTaskProcessor):
    def generate_code_for_task(self, task, additional_context=""):
        # Custom code generation logic
        return super().generate_code_for_task(task, additional_context)
```

### Extended Testing
```python
from ace_testing_framework import ACETestFramework

# Generate tests for specific task
test_framework = ACETestFramework()
test_suite = test_framework.generate_tests_for_task(task)
results = test_framework.run_tests_for_task(task, test_suite, workspace)
```

### Task Library Integration
```python
# Find similar tasks
similar_tasks = ace.task_library.find_similar_tasks(
    "create a REST API",
    threshold=0.8
)

# Add custom tasks to library
ace.task_library.add_task(completed_task)
```

## Monitoring and Reporting

### Execution Reports
Each project execution generates a comprehensive report including:
- Task execution summary
- Test results and coverage
- Code quality metrics
- Performance statistics
- Failure analysis

### Quality Metrics
- **Success Rate**: Percentage of tasks completed successfully
- **Test Coverage**: Automated test generation and execution
- **Code Quality**: Static analysis scores
- **Reuse Rate**: Percentage of tasks using library code

## Troubleshooting

### Common Issues

1. **OpenAI API Errors**
   - Verify API key is set correctly
   - Check API rate limits
   - Ensure sufficient credits

2. **Task Execution Timeouts**
   - Increase timeout values in configuration
   - Review generated code for infinite loops
   - Check for blocking operations

3. **Dependency Resolution Errors**
   - Review task descriptions for clarity
   - Check for circular dependencies
   - Manually adjust task dependencies if needed

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

ace = ACEv2()  # Will show detailed debug information
```

## Contributing

### Development Setup
1. Fork the repository
2. Create a development branch
3. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   pip install pytest black flake8
   ```

### Running Tests
```bash
# Run basic tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=.
```

### Code Style
```bash
# Format code
black *.py

# Check style
flake8 *.py
```

## Roadmap

### Planned Enhancements

1. **Advanced Similarity Detection**
   - Semantic code similarity using AST analysis
   - Vector embeddings for task descriptions
   - Machine learning-based similarity scoring

2. **Enhanced Context Management**
   - Retrieval-Augmented Generation (RAG) for large codebases
   - Context summarization for long project histories
   - Dynamic context selection

3. **Performance Optimization**
   - Caching for repeated operations
   - Parallel LLM calls for independent tasks
   - Optimized workspace management

4. **Integration Features**
   - Git integration for version control
   - CI/CD pipeline integration
   - IDE plugins and extensions

5. **Advanced Testing**
   - Property-based testing generation
   - Performance test generation
   - Integration test orchestration

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for providing the LLM capabilities
- The Python community for excellent libraries
- Contributors and testers

---

**Note**: This is an enhanced version of the original ACE system with significant improvements in error handling, testing, dependency management, and code reusability. For migration from v1, see the migration guide in `MIGRATION.md`. 