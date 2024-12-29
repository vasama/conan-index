#!/usr/bin/python3

import argparse
import itertools
import json
import os
import sys
import yaml

from frozendict import frozendict, deepfreeze


attribute_keys = {
	"license": "license",
	"authors": "author",
	"src_url": "url",
	"doc_url": "homepage",
	"description": "description",
	"package_type": "package_type",
}

attribute_sort = {k:i for i, k in enumerate(attribute_keys.values())}
attribute_sort["requirements"] = len(attribute_sort)


def split_path(path):
	parts = []

	while True:
		path, tail = os.path.split(path)

		if tail:
			parts.append(tail)
		else:
			if path:
				parts.append(path)

			parts.reverse()
			return parts

def read_package_json(repository_path, component_path):
	package = dict()

	read_any_json = False
	def read_json_file(path):
		path = os.path.join(path, "package_info.json")

		if os.path.isfile(path):
			with open(path, "r") as file:
				json_data = json.load(file)

			for key, value in json_data.items():
				if not isinstance(value, list): package[key] = value
				else: package.setdefault(key, []).extend(value)

			nonlocal read_any_json
			read_any_json = True

	read_json_file(repository_path)
	for path_part in split_path(component_path):
		repository_path = os.path.join(repository_path, path_part)
		read_json_file(repository_path)

	if not read_any_json:
		raise RuntimeError("package_info.json not found")

	return package

def make_package_conandata(package):
	data = dict()

	for package_key, data_key in attribute_keys.items():
		value = package.get(package_key)
		if value is not None: data[data_key] = value

	data_requirements = []
	for require in package.get("requirements", ()):
		reference = f"{require["package"]}/{require["version"]}"
		arguments = {}

		def set_require_bool(name, data_name=None):
			if data_name is None:
				data_name = name

			value = require.get(name)
			if value is not None:
				if not isinstance(value, bool):
					raise RuntimeError(f"Mistyped requirement option: {name}")

				arguments[data_name] = value

		set_require_bool("host", "build")
		set_require_bool("test")
		set_require_bool("visible")

		data_require = { "reference": reference }

		if len(arguments) != 0:
			data_require["arguments"] = arguments

		data_requirements.append(data_require)

	if len(data_requirements) != 0:
		data["requirements"] = data_requirements

	return data

def get_package_conandata(repository_path, component_path):
	make_package_conandata(read_package_json(repository_path, component_path))


def get_ver_data(conandata, version):
	all_data = dict(conandata.get("common_attributes", {}))
	ver_data = conandata.get("attributes", {}).get(version, {})

	for key, value in ver_data:
		all_value = all_data.get(key)

		if all_value is None:
			all_data[key] = value
			continue

		if type(all_value) != type(value):
			raise RuntimeError(f"Mismatched type for '{key}' in version attributes")

		all_data[key] = list(set(all_data[key]).union(value)) if value is list else value

	return all_data

def merge_ver_data(ver_data):
	ver_data_dict = ver_data
	ver_data = list(ver_data.values())

	common_attributes = {}

	ver_keys_set = [frozenset(x.keys()) for x in ver_data]
	ver_keys_set = list(frozenset.intersection(*ver_keys_set))
	ver_keys_set.sort(key=lambda x: attribute_sort[x])

	for key in ver_keys_set:
		values = set(deepfreeze(x.get(key)) for x in ver_data)

		if len(values) == 1:
			shared_value = ver_data[0][key]
			if shared_value is not None:
				common_attributes[key] = shared_value
				for ver in ver_data: ver.pop(key, None)
		else:
			types = set(type(x.get(key)) for x in ver_data)

			if len(types) != 1:
				raise RuntimeError(f"Mismatched type for '{key}' in version attributes")

			if types.pop() is list:
				shared_list = set.intersection(x.get(key, []) for x in ver_data)

				if len(shared_list) != 0:
					common_attributes[key] = list(shared_list)

					for ver in ver_data:
						ver_list = ver.get(key)

						if ver_list is None:
							continue

						ver_list = set(ver_list).difference(shared_list)

						if len(ver_list) == 0: del ver[key]
						else: ver[key] = list(ver_list)

	for k, v in list(ver_data_dict.items()):
		if len(v) == 0:
			del ver_data_dict[k]

	return common_attributes


if __name__ == "__main__":
	parser = argparse.ArgumentParser(prog='update-conandata')

	parser.add_argument('--root')
	parser.add_argument('--path')

	parser.add_argument('--name')
	parser.add_argument('--version')

	parser.add_argument('--src-url')
	parser.add_argument('--src-hash')

	parser.add_argument('conandata')

	args = parser.parse_args()


	data = None
	if os.path.isfile(args.conandata):
		with open(args.conandata, "r") as file:
			data = yaml.safe_load(file)
	if data is None: data = {}

	if args.name is not None:
		if data.setdefault("name", args.name) != args.name:
			raise RuntimeError(f"Mismatched package name: '{data["name"]}'")

	if args.path is not None:
		if data.setdefault("path", args.path) != args.path:
			raise RuntimeError(f"Mismatched component path: '{data["path"]}'")

	repository_path = os.getcwd() if args.root is None else args.root
	ver_data = { v: get_ver_data(data, v) for v in data.get("sources", {}).keys() }
	ver_data[args.version] = get_package_json(repository_path, args.path)

	all_data = merge_ver_data(ver_data)

	if len(all_data) != 0:
		data["common_attributes"] = all_data
	else:
		data.pop("common_attributes", None)

	if len(ver_data) != 0:
		data["attributes"] = ver_data
	else:
		all_ver_data = data.get("attributes", {})
		all_ver_data.pop(args.version, None)

		if len(all_ver_data) == 0:
			data.pop("attributes", None)

	data_sources = data.setdefault("sources", {})
	data_sources[args.version] = { "url": args.src_url, "sha256": args.src_hash }

	with open(args.conandata, "w") as file:
		yaml.safe_dump(data, stream=file, default_flow_style=False, sort_keys=False)
