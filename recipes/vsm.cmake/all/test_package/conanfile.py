from conan import ConanFile
from conan.tools.cmake import CMake, cmake_layout
from conan.tools.build import can_run

class test_package(ConanFile):
	settings = "os", "compiler", "build_type", "arch"

	layout = cmake_layout
	generators = "CMakeDeps", "CMakeToolchain"

	def requirements(self):
		self.requires(self.tested_reference_str)

	def build(self):
		cmake = CMake(self)
		cmake.configure()
		cmake.build()

	def test(self):
		if can_run(self):
			CMake(self).test()