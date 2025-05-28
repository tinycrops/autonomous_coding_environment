import logging
import time

# Configuring logging 📝
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Candidate:
    """Represents a candidate in the voting system."""
    def __init__(self, name):
        self.name = name
        self.votes = 0

    def __str__(self):
        return f'{self.name}: {self.votes} votes'  # Display candidate name and votes 🎨

class VotingSystem:
    """Manages the voting process and ensures that users can only vote once."""  
    def __init__(self):
        self.candidates = {}  # Dictionary to store candidates
        self.voters = set()   # Set to track who has voted

    def add_candidate(self, name):  
        """Adds a new candidate to the voting system."""
        if name in self.candidates:
            logging.warning('Candidate %s already exists!', name)  # Log warning 🚨
            raise ValueError('Candidate already exists')
        self.candidates[name] = Candidate(name)
        logging.info('Added candidate: %s', name)  # Log info message 🗳️

    def vote(self, voter_name, candidate_name):
        """Records a vote for a candidate from a voter."""
        if voter_name in self.voters:
            logging.error('Voter %s has already voted!', voter_name)  # Log error ❌
            raise ValueError('You already voted')
        if candidate_name not in self.candidates:
            logging.error('Candidate %s does not exist!', candidate_name)  # Log error ❌
            raise ValueError('Candidate does not exist')

        self.candidates[candidate_name].votes += 1
        self.voters.add(voter_name)  # Mark this voter as having voted
        logging.info('Voter %s voted for %s', voter_name, candidate_name)  # Log info message 🗳️

    def display_results(self):
        """Displays the voting results for all candidates."""
        logging.info('Displaying voting results...')  # Log info message 📊
        for candidate in self.candidates.values():
            print(candidate)  # Output each candidate's votes 🎆

def main():
    system = VotingSystem()
    while True:
        print('\nWelcome to the Voting System! Please choose an action:')
        print('1. Add a candidate')
        print('2. Vote')
        print('3. Display results')
        print('4. Exit')
        action = input('Enter action number: ')  # User input for action

        try:
            if action == '1':
                candidate_name = input('Enter the candidate name: ')
                system.add_candidate(candidate_name)
            elif action == '2':
                voter_name = input('Enter your name: ')  # Voter's name
                candidate_name = input('Enter the candidate name to vote for: ')
                system.vote(voter_name, candidate_name)
            elif action == '3':
                system.display_results()
            elif action == '4':
                logging.info('Exiting voting system.')  # Log info message 🚪
                break  # Exit the loop safely
            else:
                print('Invalid action! Please choose a valid option.')  # Invalid action
        except ValueError as e:
            print(e)  # Display the error to the user
            time.sleep(1)  # Pause for a moment to let the user absorb the message ⏳

if __name__ == '__main__':
    main()  # Start the voting system application 🎉