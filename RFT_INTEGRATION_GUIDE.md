# Reinforcement Fine-Tuning (RFT) Integration Guide

## Overview

This guide explains how the reinforcement fine-tuning methodology from OpenAI's medical grading cookbook has been integrated into the autonomous coding environment to create a self-improving system that can enhance code generation quality through structured feedback and continuous learning.

## Architecture Overview

The RFT integration consists of three main components:

### 1. RFT Grading System (`rft_grading_system.py`)
- **Purpose**: Sophisticated evaluation of code quality and correctness
- **Key Features**:
  - Multi-criteria grading (functionality, quality, performance, error handling, documentation)
  - Both heuristic and model-based grading approaches
  - Support for domain-specific grader configurations
  - RFT training data preparation and job management

### 2. RFT Enhanced Task Processor (`rft_enhanced_task_processor.py`)
- **Purpose**: Enhanced task processing with continuous improvement capabilities
- **Key Features**:
  - Automatic task improvement through iterative refinement
  - Batch processing with performance evaluation
  - Performance analytics and trend tracking
  - Automatic RFT training data collection and job launching

### 3. Demonstration System (`rft_demo.py`)
- **Purpose**: Comprehensive demonstration of RFT capabilities
- **Key Features**:
  - Sample task creation and processing
  - Multi-stage evaluation demonstrations
  - Performance analytics visualization
  - Training data export capabilities

## Key Benefits

### 1. Intelligent Code Evaluation
```python
# Multi-criteria grading system
grader = RFTGradingSystem()
score = grader.combined_code_grader(sample, item, weights=[0.6, 0.4])
```

The system evaluates code based on:
- **Functionality** (60%): Does it work correctly?
- **Code Quality** (40%): Is it well-structured and maintainable?

### 2. Automatic Improvement
```python
# Automatic task improvement
processor = RFTEnhancedTaskProcessor()
improved_task = processor.process_task_with_rft(task, workspace_path)
```

When code scores below threshold (default 0.75):
- System automatically attempts improvements
- Iterative refinement with up to 3 attempts
- Keeps the best version found

### 3. Continuous Learning
```python
# Batch processing with learning
processed_tasks = processor.batch_process_with_rft(tasks, workspace_path)
```

The system:
- Collects performance data from all tasks
- Automatically prepares RFT training data
- Can launch fine-tuning jobs when sufficient data is available

## Integration Points with Existing System

### Enhanced BaseTaskProcessor
The `RFTEnhancedTaskProcessor` extends the existing `BaseTaskProcessor` while maintaining full compatibility:

```python
# Drop-in replacement
# OLD: processor = BaseTaskProcessor()
# NEW: processor = RFTEnhancedTaskProcessor()

# All existing methods still work
task.code = processor.generate_code_for_task(task)
result = processor.execute_task_code(task, workspace_path)
```

### Seamless ACE Integration
The RFT system can be integrated into any ACE variant:

```python
class RFTEnhancedACE(ACEFramework):
    def __init__(self):
        super().__init__()
        self.processor = RFTEnhancedTaskProcessor()
        self.processor.set_grader_config("general_programming")
    
    def process_task(self, task):
        return self.processor.process_task_with_rft(task, self.workspace_path)
```

## Configuration and Setup

### Environment Variables
```bash
# Required for RFT API access
export OPENAI_API_KEY="your_api_key_here"

# Optional: Enable automatic RFT training
export AUTO_RFT_TRAINING="true"
```

### Grader Configuration
```python
# Set domain-specific grader
processor.set_grader_config("general_programming")  # Default
processor.set_grader_config("data_science")         # Future extension
processor.set_grader_config("web_development")      # Future extension
```

### Performance Thresholds
```python
# Customize improvement triggers
processor.performance_threshold = 0.80  # Higher threshold = more improvements
processor.performance_threshold = 0.60  # Lower threshold = fewer improvements
```

## Usage Examples

### Basic RFT Task Processing
```python
from rft_enhanced_task_processor import RFTEnhancedTaskProcessor
from base_task_processor import Task

# Create processor
processor = RFTEnhancedTaskProcessor(model="o4-mini")
processor.set_grader_config("general_programming")

# Create and process task
task = Task(
    id="example_task",
    description="Create a function that calculates factorial"
)

# Process with RFT enhancement
result = processor.process_task_with_rft(task, "workspace/")
print(f"Task score: {result.metadata.tags[-1]}")  # Shows RFT score
```

### Batch Processing with Analytics
```python
# Process multiple tasks
tasks = [task1, task2, task3, task4, task5]
processed_tasks = processor.batch_process_with_rft(tasks, "workspace/")

# Get performance analytics
analytics = processor.get_performance_analytics()
print(f"Average improvement: {analytics['average_improvement']:.3f}")
print(f"Improvement rate: {analytics['improvement_rate']:.1%}")
```

### RFT Training Management
```python
# Check for available training jobs
jobs = processor.list_rft_jobs()

# Monitor job status
if jobs:
    status = processor.check_rft_job_status(jobs[0]['job_id'])
    print(f"Job status: {status['status']}")
    
    # Update model when training completes
    if status['status'] == 'succeeded':
        processor.update_model_after_rft(jobs[0]['job_id'])
```

## Advanced Features

### Custom Grader Development
```python
def custom_security_grader(sample, item):
    """Custom grader focused on security aspects."""
    code = sample.get("output_text", "")
    
    security_score = 0.5  # Base score
    
    # Check for security best practices
    if "input(" not in code:  # No unsafe input
        security_score += 0.2
    if "eval(" not in code:   # No eval usage
        security_score += 0.2
    if "exec(" not in code:   # No exec usage
        security_score += 0.1
    
    return min(1.0, security_score)

# Use custom grader
processor.rft_grader.custom_grader = custom_security_grader
```

### Model Comparison and A/B Testing
```python
# Compare base model vs fine-tuned model
base_processor = RFTEnhancedTaskProcessor(model="o4-mini")
rft_processor = RFTEnhancedTaskProcessor(
    model="o4-mini", 
    rft_model="ft:o4-mini-ace-rft-123"
)

# Process same tasks with both
base_results = base_processor.batch_process_with_rft(tasks, "base_workspace/")
rft_results = rft_processor.batch_process_with_rft(tasks, "rft_workspace/")

# Compare performance
base_analytics = base_processor.get_performance_analytics()
rft_analytics = rft_processor.get_performance_analytics()
```

## Data Flow and Learning Cycle

### 1. Task Processing
```
Task Input → Code Generation → Execution → Grading → Improvement (if needed)
```

### 2. Data Collection
```
Graded Tasks → Performance Metrics → Training Data Preparation
```

### 3. Model Enhancement
```
Training Data → RFT Job Launch → Fine-tuned Model → Updated Processor
```

### 4. Continuous Improvement
```
Enhanced Model → Better Code Generation → Higher Scores → Better Training Data
```

## Performance Monitoring

### Key Metrics Tracked
- **Task Scores**: Individual task performance ratings
- **Improvement Rates**: Percentage of tasks successfully improved
- **Average Improvements**: Mean score increase after improvement attempts
- **Training Data Quality**: Distribution of scores in collected data

### Analytics Dashboard
```python
analytics = processor.get_performance_analytics()

# Key performance indicators
print(f"Total improvement attempts: {analytics['total_improvement_attempts']}")
print(f"Success rate: {analytics['improvement_rate']:.1%}")
print(f"Average score improvement: {analytics['average_improvement']:.3f}")
print(f"Recent performance trend: {analytics['recent_performance']}")
```

## Integration with Existing Workflows

### ACE Framework Integration
```python
# Minimal changes to existing ACE implementations
class EnhancedACE(ACEFramework):
    def __init__(self):
        super().__init__()
        # Replace processor with RFT-enhanced version
        self.task_processor = RFTEnhancedTaskProcessor()
        self.task_processor.set_grader_config("general_programming")
    
    def process_task(self, task_description):
        task = Task(id=self.generate_task_id(), description=task_description)
        return self.task_processor.process_task_with_rft(task, self.workspace_path)
```

### Debugging and Development
```python
# Enhanced debugging with quality metrics
debug_processor = RFTEnhancedTaskProcessor()
debug_processor.performance_threshold = 0.5  # Lower threshold for debugging

# Process problematic tasks
problematic_task = Task(id="debug_001", description="Complex algorithm implementation")
result = debug_processor.process_task_with_rft(problematic_task, "debug_workspace/")

# Analyze improvement attempts
if hasattr(result.metadata, 'tags'):
    for tag in result.metadata.tags:
        if 'improved_attempt' in tag:
            print(f"Improvement made: {tag}")
```

## Best Practices

### 1. Grader Configuration
- Set domain-specific graders for better evaluation accuracy
- Regularly review and update grader prompts based on performance
- Use multiple grading criteria for comprehensive evaluation

### 2. Performance Thresholds
- Start with conservative thresholds (0.75) for production systems
- Lower thresholds (0.6) for experimentation and learning
- Monitor improvement rates and adjust accordingly

### 3. Training Data Management
- Regularly export high-quality samples for training
- Maintain diverse task types in training data
- Monitor for reward hacking and adjust graders as needed

### 4. Model Management
- Keep track of fine-tuned model performance
- A/B test new models before full deployment
- Maintain fallback to base models if fine-tuned models underperform

## Troubleshooting

### Common Issues

1. **Low Improvement Rates**
   - Check grader configuration alignment with task types
   - Verify performance thresholds are appropriate
   - Review improvement attempt logs for patterns

2. **RFT Training Failures**
   - Ensure sufficient training data (minimum 20 samples)
   - Verify API key permissions for fine-tuning
   - Check grader validation before job submission

3. **Performance Degradation**
   - Compare fine-tuned model performance with base model
   - Check for reward hacking in training data
   - Review grader prompt effectiveness

### Debug Mode
```python
# Enable detailed logging
import logging
logging.getLogger('RFTEnhancedTaskProcessor').setLevel(logging.DEBUG)
logging.getLogger('RFTGradingSystem').setLevel(logging.DEBUG)

# Process with verbose output
processor = RFTEnhancedTaskProcessor()
processor.logger.setLevel(logging.DEBUG)
```

## Future Enhancements

### Planned Features
1. **Domain-Specific Graders**: Specialized evaluation for different programming domains
2. **Multi-Model Ensemble**: Combine multiple fine-tuned models for better performance
3. **Adaptive Thresholds**: Automatically adjust performance thresholds based on task complexity
4. **Real-time Monitoring**: Dashboard for live performance tracking
5. **Collaborative Learning**: Share improvements across multiple ACE instances

### Research Directions
1. **Advanced Reward Functions**: More sophisticated grading mechanisms
2. **Few-Shot Learning**: Rapid adaptation to new task types
3. **Curriculum Learning**: Progressive difficulty adjustment
4. **Meta-Learning**: Learning to learn more efficiently

## Conclusion

The RFT integration transforms the autonomous coding environment from a static code generator into a continuously improving system that learns from its mistakes and successes. By combining sophisticated evaluation mechanisms with automated improvement processes, the system can achieve higher code quality while reducing manual intervention.

The modular design ensures seamless integration with existing workflows while providing powerful new capabilities for self-improvement and learning. As the system processes more tasks, it becomes increasingly effective at generating high-quality code solutions. 