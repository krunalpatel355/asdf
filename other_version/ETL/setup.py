import os

# Define the project structure
project_structure = {
    "reddit_analytics": [
        "config/__init__.py",
        "config/settings.py",
        "etl/__init__.py",
        "etl/extract.py",
        "etl/transform.py",
        "etl/load.py",
        "etl/embedding.py",
        "utils/__init__.py",
        "utils/connections.py",
        ".env",
        "requirements.txt",
        "main.py"
    ]
}

def create_project_structure(structure):
    for root, files in structure.items():
        # Create root directory
        os.makedirs(root, exist_ok=True)
        for file_path in files:
            # Create each file and necessary subdirectories
            full_path = os.path.join(root, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            # Create an empty file if it doesn't exist
            with open(full_path, 'w') as f:
                pass
            print(f"Created: {full_path}")

# Run the function to create the structure
create_project_structure(project_structure)
