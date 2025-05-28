import json  # Importing JSON module for data serialization
import os  # Importing OS module for file path checks
import re  # Importing regular expression module for email validation

# Contact class to represent each contact entry
class Contact:
    def __init__(self, name, phone, email):
        self.name = name
        self.phone = phone
        self.email = email

    def __repr__(self):
        return f'{self.name} | {self.phone} | {self.email}'

# Function to load contacts from a JSON file
def load_contacts(filename):
    if not os.path.exists(filename):  # Check if file exists
        return []  # Return empty list if no contacts file
    with open(filename, 'r') as f:
        return json.load(f)  # Load and return contacts from file

# Function to save contacts to a JSON file
def save_contacts(filename, contacts):
    with open(filename, 'w') as f:
        json.dump([contact.__dict__ for contact in contacts], f, indent=4)  # Save contacts data to file

# Function to validate email format
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None  # Validate the email format with regex

# Function to check for duplicate contact
def is_duplicate(contacts, new_contact):
    return any(c.name == new_contact.name for c in contacts)  # Check if contact already exists by name

# Function to display all contacts
def display_contacts(contacts):
    if not contacts:
        print('No contacts available.')  # Message for no contacts
        return
    sorted_contacts = sorted(contacts, key=lambda c: c.name)  # Sort contacts by name
    print('\nList of Contacts:')
    print('Name | Phone | Email')
    print('----------------------')
    for contact in sorted_contacts:
        print(contact)

# Main function to drive the application
def main():
    filename = 'contacts.json'  # Filename for the contacts
    contacts = load_contacts(filename)  # Load existing contacts

    while True:
        print('\n--- Contact Management Application ---')  # Application title
        print('1. Add Contact')
        print('2. View Contacts')
        print('3. Search Contact')
        print('4. Delete Contact')
        print('5. Exit')

        choice = input('Choose an option (1-5): ')  # User menu

        if choice == '1':
            name = input('Enter name: ')  # Name input
            phone = input('Enter phone number: ')  # Phone number input
            email = input('Enter email address: ')  # Email input

            if not name or not phone or not email:
                print('Error: All fields must be filled. 🚫')  # Error for empty fields
                continue

            if not is_valid_email(email):
                print('Error: Invalid email format. 📧')  # Error for invalid email
                continue

            new_contact = Contact(name, phone, email)
            if is_duplicate(contacts, new_contact):
                print('Error: Contact already exists. ❌')  # Error for duplicate contact
                continue

            contacts.append(new_contact)  # Add new contact
            save_contacts(filename, contacts)  # Save to file
            print('Contact added successfully! ✔️')  # Success message

        elif choice == '2':
            display_contacts(contacts)  # Display all contacts

        elif choice == '3':
            search_name = input('Enter name to search: ')  # Search input
            found_contacts = [c for c in contacts if search_name.lower() in c.name.lower()]
            if found_contacts:
                print('Search Results:')
                for contact in found_contacts:
                    print(contact)  # Display search results
            else:
                print('No contacts found with that name. 🕵️‍♂️')  # No match found

        elif choice == '4':
            delete_name = input('Enter name to delete: ')  # Name to delete
            contacts = [c for c in contacts if c.name.lower() != delete_name.lower()]  # Remove contact if name matches
            save_contacts(filename, contacts)  # Save changes to file
            print(f'Contact {delete_name} deleted successfully! 🗑️')  # Success message

        elif choice == '5':
            print('Exiting the application. Goodbye! 👋')  # Exit message
            break  # Exit loop

        else:
            print('Invalid option. Please select a valid choice. ❓')  # Error for invalid option

# Entry point of the script
if __name__ == '__main__':
    main()  # Run the main function