cmake_minimum_required(VERSION 3.24)
project(package_test)
enable_testing()

find_package(vsm.cmake REQUIRED)

vsm_add_executable(
	test_executable
	SOURCES test.cpp
)

add_test(package_test test_executable)
