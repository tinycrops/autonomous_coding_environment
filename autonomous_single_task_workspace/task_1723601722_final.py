import json  # Importing json for data handling 📁
import logging  # Import logging for activity tracking 📊

# Configure logging settings 🛠️
logging.basicConfig(filename='filing_assistant.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Class to represent a Filing Assistant 📂
class FilingAssistant:
    def __init__(self, storage_file='storage.json'):
        self.storage_file = storage_file
        self.data = self.load_data()  # Load existing data 📊

    def load_data(self):
        # Load data from a JSON file 📥
        try:
            with open(self.storage_file, 'r') as file:
                logging.info('Loading existing data...')
                return json.load(file)
        except FileNotFoundError:
            logging.warning('Storage file not found. Starting with an empty dataset.')
            return []  # Return an empty list if file not found 📝
        except json.JSONDecodeError:
            logging.error('Error decoding JSON. Starting with an empty dataset.')
            return []  # Return an empty list on JSON errors

    def save_data(self):
        # Save the current data to the JSON file 💾
        try:
            with open(self.storage_file, 'w') as file:
                json.dump(self.data, file, indent=4)
                logging.info('Data saved successfully.')
        except Exception as e:
            logging.error(f'Error saving data: {str(e)}')

    def add_entry(self, name, file_type, description):
        # Add a new entry to the filing system ✍️
        new_entry = {'name': name, 'type': file_type, 'description': description}
        self.data.append(new_entry)  # Append new entry to the data
        logging.info(f'Added new entry: {new_entry}')
        self.save_data()  # Save updated data

    def get_entries(self):
        # Get the current entries in the filing system 📜
        return self.data

    def delete_entry(self, name):
        # Delete an entry by file name ❌
        initial_length = len(self.data)
        self.data = [entry for entry in self.data if entry['name'] != name]  # Remove the entry
        if len(self.data) < initial_length:
            logging.info(f'Deleted entry with name: {name}')
            self.save_data()  # Save changes if deletion occurred
        else:
            logging.warning(f'No entry found with name: {name}')


# Example usage of the FilingAssistant class 📚
if __name__ == '__main__':
    assistant = FilingAssistant()
    assistant.add_entry('Report', 'PDF', 'Annual financial report for 2023')  # Adding a report 📄
    assistant.add_entry('Presentation', 'PPT', 'Sales presentation Q1 2023')  # Adding a presentation 🎤
    print('Current Entries:', assistant.get_entries())  # Display current entries
    assistant.delete_entry('Report')  # Deleting the report
    print('Current Entries after deletion:', assistant.get_entries())  # Display entries after deletion