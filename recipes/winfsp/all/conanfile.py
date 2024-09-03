from conan import ConanFile
from conan.tools.files import get, copy, trim_conandata
from conan.tools.microsoft import vs_layout, MSBuild

import os

def get_platform_name(arch):
	match arch:
		case "x86":
			return "x86"
		case "x86_64":
			return "x64"
		case "arm64ec":
			return "a64"

class Package(ConanFile):
	name = "winfsp"

	url = "https://github.com/vasama/conan-index"
	homepage = "https://winfsp.dev"
	license = "GPL-3.0-only"
	description = "Windows File System Proxy"

	package_type = "shared-library"
	settings = "os", "arch", "compiler", "build_type"

	layout = vs_layout
	generators = "MSBuildToolchain"

	def validate(self):
		if self.settings.os != "Windows":
			raise ConanInvalidConfiguration("Only Windows is supported")

	def export(self):
		trim_conandata(self)

	def source(self):
		get(self, **self.conan_data["sources"][self.version], strip_root=True)

	def build(self):
		msbuild = MSBuild(self)
		msbuild.build(os.path.join(self.source_folder, "build/VStudio/winfsp_dll.vcxproj"))

	def package(self):
		platform_name = get_platform_name(self.settings.arch)

		copy(self, "License.txt", dst=self.package_folder, src=self.source_folder)
		copy(
			self,
			"*.h",
			dst=os.path.join(self.package_folder, "include"),
			src=os.path.join(self.source_folder, "inc"))
		copy(
			self,
			"*.hpp",
			dst=os.path.join(self.package_folder, "include"),
			src=os.path.join(self.source_folder, "inc"))
		copy(
			self,
			f"winfsp-{platform_name}.lib",
			dst=os.path.join(self.package_folder, "lib"),
			src=os.path.join(self.source_folder, f"build/VStudio/build/{self.settings.build_type}"))
		copy(
			self,
			f"winfsp-{platform_name}.dll",
			dst=os.path.join(self.package_folder, "bin"),
			src=os.path.join(self.source_folder, f"build/VStudio/build/{self.settings.build_type}"))

	def package_info(self):
		self.cpp_info.set_property("cmake_file_name", "winfsp")
		self.cpp_info.set_property("cmake_target_name", "winfsp::winfsp")
		self.cpp_info.libs = [f"winfsp-{get_platform_name(self.settings.arch)}"]
