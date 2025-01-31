#!/usr/bin/env python3

import argparse
import os
import yaml

if __name__ == "__main__":
	parser = argparse.ArgumentParser(prog='get-recipe-directory')

	parser.add_argument("--root")
	parser.add_argument("--name")
	parser.add_argument("--version")

	args = parser.parse_args()

	root = os.getcwd() if args.root is None else args.root
	recipe_dir = os.path.join(root, "recipes", args.name)

	with open(os.path.join(recipe_dir, "config.yml"), "r") as file:
		recipe_config = yaml.safe_load(file)

	print(os.path.join(recipe_dir, recipe_config["versions"][args.version]["folder"]))
