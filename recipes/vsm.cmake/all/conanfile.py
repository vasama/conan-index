from conan import ConanFile
from conan.tools.files import copy, get, trim_conandata

import os

class Package(ConanFile):
	name = "vsm.cmake"

	license = "MIT"
	author = "Lauri Vasama"
	url = "https://github.com/vasama/vsm"

	requires = (
		"catch2/[^3.4]",
	)

	def export(self):
		trim_conandata(self)

	def source(self):
		sources = self.conan_data["sources"][self.version]
		get(self, **sources, strip_root=True)

	def package(self):
		source_folder = os.path.join(self.source_folder, "cmake")

		copy(
			self,
			"*.cmake",
			os.path.join(source_folder, "cmake"),
			os.path.join(self.package_folder, "cmake"))

	def package_info(self):
		self.cpp_info.includedirs = []
		self.cpp_info.libdirs = []
		self.cpp_info.builddirs.append("cmake")
		self.cpp_info.set_property("cmake_file_name", "vsm.cmake")
		#TODO: Should not define a CMake target at all.
		self.cpp_info.set_property("cmake_target_name", "vsm::cmake")
		self.cpp_info.set_property("cmake_build_modules", ["cmake/vsm.cmake"])
