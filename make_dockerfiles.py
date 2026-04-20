import yaml
import os
import shutil
from pathlib import Path

# Here are reported the templated Dockerfiles, for each tool
# If you want to update them, please pay attention in escaping brackets {{}} and backslashes \\
DOCKERFILES = {
    
    # For Cactus we use the ready image, no cloning from the repository
    'cactus': '''\
FROM quay.io/comparative-genomics-toolkit/cactus:{}

RUN mkdir results
RUN mkdir input_data

CMD ["/bin/bash"]

    '''
}

def main():
    # Open the tools_config.yml file and read tools' configuration
    with open('tools_config.yml', 'r') as file:
        config = yaml.safe_load(file)

    # Create the Dockerfiles folder, if it doesn't exist yet
    if not os.path.exists('Dockerfiles'):
        os.makedirs('Dockerfiles')

    # Select Dockerfiles as working directory
    DOCKERFILES_FOLDER = os.path.join(os.getcwd(), 'Dockerfiles')
    os.chdir(DOCKERFILES_FOLDER)

    # Eventually, remove previously existing folders
    folder_list = [f for f in Path(DOCKERFILES_FOLDER).glob('**/*') if not f.is_file()]
    for dir in folder_list:
        shutil.rmtree(os.path.join(DOCKERFILES_FOLDER, dir))

    # Create subfolders in Dockerfiles, one for each tested tool
    for tool in config:
        os.makedirs(tool)

    # For each tool, create a Dockerfile in its subfolder
    for tool in config:
        os.chdir(os.path.join(DOCKERFILES_FOLDER, tool))
        file_tmp = open('Dockerfile', 'w')
        file_tmp.write(DOCKERFILES[tool.lower()].format(config[tool]['version']))
        file_tmp.close()

    # Print a success message
    print('\nSuccessfully created dockerfiles for the following tools:')
    for tool in config:
        print(f'\t{tool}')
    print()

if __name__ == '__main__':
    main()