import os
import yaml
import json


def check_surveys():
    # Define the base directory
    base_dir = "extensions/experiences"
    survey_specs = {}

    # List immediate subdirectories under experiences
    for dir_name in os.listdir(base_dir):
        dir_path = os.path.join(base_dir, dir_name)

        # Only process if it is a directory
        if os.path.isdir(dir_path):
            setup_path = os.path.join(dir_path, "setup.yml")

            # Check if setup.yaml exists in this directory
            if os.path.isfile(setup_path):
                # Read the YAML file
                with open(setup_path, "r") as file:
                    data = yaml.safe_load(file)

                    # Check if 'controller_templates' exists and process it
                    if "controller_templates" in data:
                        ghost_increment = 0
                        for item in data["controller_templates"]:
                            if "survey_spec" in item:
                                survey_specs[item["survey_spec"]] = dir_name
                            else:
                                ghost_increment += 1
                                survey_specs[f"IdontKnowSomeMagicHere_{ghost_increment}"] = dir_name
        if os.path.isdir(dir_path):
            read_json_surveys(dir_path, dir_name)
            # process_json_surveys(survey_specs)

    return survey_specs


def create_all_yaml():
    # Define the directory containing template files
    template_dir = "./templates"

    # List all YAML and YML files in the template directory
    template_files = [
        os.path.join(template_dir, f)
        for f in os.listdir(template_dir)
        if f.endswith(".yaml") or f.endswith(".yml")
    ]

    # Define the structure of the YAML data
    data = {
        "apiVersion": "backstage.io/v1alpha1",
        "kind": "Location",
        "metadata": {
            "name": "ansible-content-templates",
            "description": "A collection of all Ansible templates",
        },
        "spec": {"targets": template_files},
    }

    # Output file
    output_file = "generated_ansible_content_templates.yaml"

    # Write the data to a YAML file
    with open(output_file, "w") as f:
        yaml.dump(data, f, default_flow_style=False)

    print(f"YAML file '{output_file}' has been generated successfully.")


def read_json_surveys(base_path, dir_name):
    # Directory containing JSON files
    directory_path = f"{base_path}/playbooks/template_surveys"

    # List to store data from all JSON files
    all_data = []

    # Loop through each file in the directory
    if os.path.isdir(directory_path):
        for filename in os.listdir(directory_path):
            if filename.endswith(".json"):
                file_path = os.path.join(directory_path, filename)

                # Attempt to read and parse JSON file
                try:
                    with open(file_path, "r") as json_file:
                        data = json.load(json_file)
                        process_json_surveys(data, dir_name)
                        # all_data.append(data)
                except json.JSONDecodeError:
                    print(f"Warning: {filename} is not a valid JSON file and was skipped.")
                except Exception as e:
                    print(f"Error: Could not read {filename} due to {e}")


def process_json_surveys(json_data, dir_name):
    yaml_data = {}
    required_list = []

    name = json_data.get("name")
    description = json_data.get("description")
    name_of_survey = json_data.get("name").replace(" ", "_")

    yaml_final = {
        "apiVersion": "scaffolder.backstage.io/v1beta3",
        "kind": "Template",
        "metadata": {
            "name": name_of_survey,
            "title": name,
            "description": description,
            "tags": [
                "recommended",
                "ansible",
            ],
        },
        "spec": {
            "owner": "ansible-authors",
            "system": "ansible",
            "type": "service",
            "parameters": [
                {
                    "title": "Provide information about the new component",
                    "required": required_list,
                    "properties": yaml_data,
                }
            ],
            "steps": [
                {
                    "id": "ansible",
                    "name": "Generating the Ansible Source Code Component",
                    "action": "ansible:rhaap:sync",
                    "input": {
                        "repoOwner": "${{ parameters.repoOwner }}",
                        "repoName": "${{ parameters.repoName }}",
                        "description": "${{ parameters.description }}",
                        "collectionGroup": "${{ parameters.collectionGroup }}",
                        "collectionName": "${{ parameters.collectionName }}",
                        "applicationType": "collection-project",
                        "sourceControl": "${{ parameters.sourceControl }}",
                    },
                }
            ],
        },
    }

    for question in json_data.get("spec", {}):
        variable = question["variable"]
        yaml_data[variable] = {
            "title": question["question_name"],
            "description": question["question_description"],
            "type": question["type"],
            "default": question.get("default"),
            "maxLength": question.get("max"),
            "minLength": question.get("min"),
        }
        if question.get("required", False):
            required_list.append(variable)
        if question.get("choices"):
            yaml_data[variable]["enum"] = question["choices"]
            yaml_data[variable]["enumNames"] = question["choices"]

    # Create templates directory if it doesn't exist
    os.makedirs("templates", exist_ok=True)

    # Write YAML output to file in templates directory
    yaml_file_path = f"templates/{dir_name}_{name_of_survey}_output.yaml"
    with open(yaml_file_path, "w") as yaml_file:
        yaml.dump(yaml_final, yaml_file, sort_keys=False)

    print(f"YAML file created at {yaml_file_path}")


# Call the function to get survey specs
survey_specs = check_surveys()
create_all_yaml()
# Display the collected survey specs
print("Collected Survey Specs:", survey_specs)
