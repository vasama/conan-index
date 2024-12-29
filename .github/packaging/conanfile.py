# VSM-CONANFILE-1.0

from conan import ConanFile
from conan.errors import ConanException
from conan.tools.cmake import CMake, cmake_layout
from conan.tools.files import get, load, save

import os
import yaml

class Conandata:
	def __init__(self, conanfile):
		self._all_data = conanfile.conan_data["common_attributes"]
		self._ver_data = conanfile.conan_data.get("attributes", {}).get(conanfile.version, {})

	def get(self, attr, default=None):
		value = self._ver_data.get(attr)
		if value is None:
			value = self._all_data.get(attr)
		if value is None:
			value = default
		return value

class Package(ConanFile):
	url = "https://github.com/vasama/conan-index"

	settings = "os", "arch", "compiler", "build_type"
	generators = "CMakeDeps", "CMakeToolchain"

	def set_name(self):
		self.name = self.conan_data["name"]

	def export(self):
		conandata_path = os.path.join(self.export_folder, "conandata.yml")

		if not os.path.isfile(conandata_path):
			raise ConanException("conandata.yml not found")

		conandata = yaml.safe_load(load(self, conandata_path))

		version = str(self.version)

		# Remove unused version attributes:
		attributes = conandata.get("attributes")
		if attributes is not None:
			if not isinstance(attributes, dict):
				raise ConanException("conandata.yml attributes is not a mapping")

			version_attributes = attributes.get(version)
			if version_attributes is None: del conandata["attributes"]
			else: conandata["attributes"] = { version: version_attributes }

		sources = conandata.get("sources")
		if sources is None or not isinstance(sources, dict):
			raise ConanException("conandata.yml sources is not a mapping")

		# Remove unused version sources:
		conandata["sources"] = { version: sources[version] }

		conandata = yaml.safe_dump(conandata, default_flow_style=False, sort_keys=False)

		# Overwrite the conandata.yml file:
		save(self, conandata_path, conandata)

	def configure(self):
		data = Conandata(self)

		def set_attr(attr):
			value = data.get(attr)
			if value is not None:
				setattr(self, attr, value)

		set_attr("package_type")
		set_attr("author")
		set_attr("url")
		set_attr("homepage")
		set_attr("license")
		set_attr("description")

	def requirements(self):
		#TODO: Do we need an explicit CMake dependency?

		for require in Conandata(self).get("requirements", []):
			self.requires(require["reference"], **require.get("arguments", {}))

	def layout(self):
		cmake_layout(self)

	def source(self):
		sources = self.conan_data["sources"][self.version]
		get(self, **sources, strip_root=True)

	def build(self):
		do_test = not self.conf.get("tools.build:skip_test", default=False)

		configure_vars = {
			"BUILD_TESTING": "ON" if do_test else "OFF",
		}

		configure_args = {
			"variables": configure_vars,
		}

		relative_path = self.conan_data.get("path")
		if relative_path is not None:
			source_path = os.path.join(self.source_folder, relative_path)
			configure_args["build_script_folder"] = source_path

		cmake = CMake(self)
		cmake.configure(**configure_args)
		cmake.build()

		if do_test:
			cmake.ctest(cli_args=["--output-on-failure"])

	def package(self):
		cmake = CMake(self)
		cmake.install()

		if os.path.isfile(os.path.join(self.package_folder, f"{self.name}-setup.cmake")):
			config = str(self.settings.build_type).upper()
			setup_script = "".join([
				f'set(VSM_PKG_{self.name}_DIR "${{{self.name}_PACKAGE_FOLDER_{config}}}")\n',
				f'include(${{CMAKE_CURRENT_LIST_DIR}}/{self.name}-setup.cmake)\n',
			])
			save(conanfile, os.path.join(self.package_folder, f"{conanfile.name}-setup-conan.cmake"), setup_script)

	def package_info(self):
		package_type = str(self.package_type)

		target_name = self.name.replace(".", "::")
		if "::" not in target_name:
			target_name = f"{target_name}::{target_name}"

		if "library" in package_type:
			self.cpp_info.set_property("cmake_target_name", target_name)

			if package_type != "header-library":
				self.cpp_info.libs.append(self.name.replace(".", "_"))

		setup_path = os.path.join("cmake", f"{self.name}-setup-conan.cmake")
		if os.path.isfile(os.path.join(self.package_folder, setup_path)):
			self.cpp_info.set_property("cmake_build_modules", [setup_path])
