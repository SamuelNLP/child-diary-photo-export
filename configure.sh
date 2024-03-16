#!/bin/bash

# project configuration script

usage() {
    echo "Usage: $0 --name <project_name> --description <project_description>"
    exit 1
}

if [ "$#" -lt 4 ]; then
    usage
fi

while [ "$#" -gt 0 ]; do
    case "$1" in
        --name)
            project_name="$2"
            shift 2
            ;;
        --description)
            project_description="$2"
            shift 2
            ;;
        *)
            usage
            ;;
    esac
done

if [ -z "$project_name" ] || [ -z "$project_description" ]; then
    usage
fi

# turn the project name - into _ for pythons sake
project_name_underscore=$(echo "$project_name" | sed 's/-/_/g')

# 1. rename the module and actions folders
mv module "${project_name_underscore}_server"
mv .github_template .github

# 2. Define the files to be modified
files_to_replace=(
    "Makefile"
    "pyproject.toml"
)

# 3. Replace the placeholders in each file
for file in "${files_to_replace[@]}"; do
    sed -i "s/<name-placeholder>/$project_name/g" "$file"
    sed -i "s/<name-placeholder-underscore>/$project_name_underscore/g" "$file"
    sed -i "s/<description-placeholder>/$project_description/g" "$file"
done

# 4. Remove the instructions_file and configure.sh
rm instructions_after_clone.txt
rm configure.sh
