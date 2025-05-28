from enhanced_autonomous_coding_environment import EnhancedAutonomousCodingEnvironment

def main():
    ace = EnhancedAutonomousCodingEnvironment(workspace="enhanced_ace_self_improvement_workspace")
    
    # Create a self-improvement project
    project_name = "Enhanced ACE Self-Improvement"
    project_description = """
    Improve the Enhanced Autonomous Coding Environment's core functionalities:
    1. Implement advanced code similarity comparison using abstract syntax trees
    2. Create a system for tracking task execution performance and optimization suggestions
    3. Develop a method for generating unit tests for implemented tasks
    4. Enhance the poetic description generation to include coding-related metaphors
    5. Implement a basic version control system for tracking changes to the ACE itself
    """
    
    project_id = ace.create_project(project_name, project_description)
    
    # Execute the self-improvement project
    ace.execute_project(project_id)
    
    print("Enhanced self-improvement project completed. Check the project report for details.")

if __name__ == "__main__":
    main()
