from conan import ConanFile
from conan.tools.files import copy
from conan.tools.cmake import CMake, cmake_layout
from conan.tools.scm import Git

import shutil
import os

class package(ConanFile):
	name = "stdexec"
	description = "std::execution"
	author = "Michał Dominiak, Lewis Baker, Lee Howes, Kirk Shoop, Michael Garland, Eric Niebler, Bryce Adelstein Lelbach"
	topics = ("WG21", "concurrency")
	homepage = "https://github.com/NVIDIA/stdexec"
	url = "https://github.com/NVIDIA/stdexec"
	license = "Apache 2.0"

	settings = "os", "arch", "compiler", "build_type"
	generators = "CMakeToolchain"

	def layout(self):
		cmake_layout(self)

	def source(self):
		data = self.conan_data["sources"][self.version]
		Git(self).fetch_commit(data["url"], data["commit"])

	def build(self):
		enable_test = not self.conf.get("tools.build:skip_test", default=False)
		cmake_enable_test = "ON" if enable_test else "OFF"

		cmake = CMake(self)
		cmake.configure(variables={
			"STDEXEC_BUILD_TESTS": cmake_enable_test,
			"STDEXEC_BUILD_EXAMPLES": cmake_enable_test,
		})
		cmake.build()

		if enable_test:
			cmake.test()

	def package(self):
		cmake = CMake(self)
		cmake.install()

	def package_info(self):
		self.cpp_info.components["stdexec"].includedirs = ["include"]
		self.cpp_info.components["exec"].libs = ["system_context"]
