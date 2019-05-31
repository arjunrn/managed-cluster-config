#!/usr/bin/env python
import os
import sys
import yaml 
import argparse
import copy

def get_yaml_all(filename):
    with open(filename,'r') as input_file:
        return list(yaml.load_all(input_file))

def get_yaml(filename):
    with open(filename,'r') as input_file:
        return yaml.safe_load(input_file)

def get_all_yaml_files(path):
    file_paths = []
    for r,d,f in os.walk(path):
        for file in f:
            if file.endswith('.yml') or file.endswith('.yaml'):
                file_paths.append(os.path.join(r,file))
    file_paths = sorted(file_paths)
    return file_paths

def get_all_yaml_obj(file_paths):
    yaml_objs = []
    for file in file_paths:
        objects = get_yaml_all(file)
        for obj in objects:
            yaml_objs.append(obj)
    return yaml_objs

def process_yamls(name, directory, obj):
    o = copy.deepcopy(obj)
    # Get all yaml files as array of yaml objecys
    yamls = get_all_yaml_obj(get_all_yaml_files(directory))

    for y in yamls:
        if 'patch' in y:
            if not 'patches' in o['spec']:
                o['spec']['patches'] = []
            o['spec']['patches'].append(y)
        else:
            if not 'resources' in o['spec']:
                o['spec']['resources'] = []
            o['spec']['resources'].append(y)

    o['metadata']['name'] = name

    # append object to the template's objects
    template_data['objects'].append(o)


if __name__ == '__main__':
    #Argument parser
    parser = argparse.ArgumentParser(description="selectorsyncset generation tool", usage='%(prog)s [options]')
    parser.add_argument("--template-dir", "-t", required=True, help="Path to template directory [required]")
    parser.add_argument("--yaml-directory", "-y", required=True, help="Path to folder containing yaml files [required]")
    parser.add_argument("--destination", "-d", required=True, help="Destination for selectorsynceset file [required]")
    parser.add_argument("--repo-name", "-r", required=True, help="Name of the repository [required]")
    arguments = parser.parse_args()

    # Get the template data
    template_data = get_yaml(os.path.join(arguments.template_dir, "template.yaml"))
    selectorsyncset_data = get_yaml(os.path.join(arguments.template_dir, "selectorsyncset.yaml"))

    # Create required labels on SelectorSyncSet
    if not 'labels' in selectorsyncset_data['metadata']:
        selectorsyncset_data['metadata']['labels'] = {}

    selectorsyncset_data['metadata']['labels']['managed.openshift.io/osd'] = "true"
    selectorsyncset_data['metadata']['labels']['managed.openshift.io/gitRepoName'] = arguments.repo_name
    selectorsyncset_data['metadata']['labels']['managed.openshift.io/gitHash'] = "${IMAGE_TAG}"

    # for each subdir of yaml_directory append 'object' to template
    for (dirpath, dirnames, filenames) in os.walk(arguments.yaml_directory):
        if not dirnames:
            process_yamls(arguments.repo_name, dirpath, selectorsyncset_data)
        else:
            for dir in dirnames:
                process_yamls(dir, os.path.join(arguments.yaml_directory, dir), selectorsyncset_data)
            # break out of the loop because os.walk will walk through each sub-dir as well
            break

    # write template file
    with open(arguments.destination,'w') as outfile:
        yaml.dump(template_data,outfile)
