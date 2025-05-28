import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(filename='self_improvement.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

class GoalManager:
    def __init__(self):
        self.goals_file = 'goals.json'
        self.load_goals()

    def load_goals(self):
        """Load goals from a JSON file"""
        try:
            with open(self.goals_file, 'r') as file:
                self.goals = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            self.goals = []  # Start with an empty list if the file doesn't exist or is empty
            logging.info('Initialized new goals list.')

    def save_goals(self):
        """Save goals to a JSON file"""
        with open(self.goals_file, 'w') as file:
            json.dump(self.goals, file)
        logging.info('Goals saved to file.')

    def add_goal(self, goal):
        """Add a new goal"""
        self.goals.append({'goal': goal, 'completed': False, 'created_at': datetime.now().isoformat()})
        self.save_goals()  # Save the new goal to the file
        logging.info(f'Added goal: {goal}')

    def view_goals(self):
        """View all goals"""
        return self.goals

    def complete_goal(self, index):
        """Mark a goal as complete"""
        try:
            self.goals[index]['completed'] = True
            self.save_goals()  # Save the updated goal list to the file
            logging.info(f'Completed goal at index: {index}')
        except IndexError:
            logging.error(f'Attempted to complete a goal at invalid index: {index}')
            raise ValueError(f'Goal at index {index} does not exist.')

    def print_goals(self):
        """Print all goals in a formatted way"""
        for idx, goal in enumerate(self.goals):
            status = "[x]" if goal['completed'] else "[ ]"
            print(f'{idx}: {status} {goal[