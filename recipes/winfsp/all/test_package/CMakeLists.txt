cmake_minimum_required(VERSION 3.24)
project(package_test)
enable_testing()

find_package(winfsp REQUIRED)

add_executable(test_executable test.cpp)
target_link_libraries(test_executable winfsp::winfsp)
add_test(package_test test_executable)
