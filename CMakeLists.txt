# Copyright (c) 2022 Gerson Fernando Budke <nandojve@gmail.com>
#
# SPDX-License-Identifier: Apache-2.0
#

cmake_minimum_required(VERSION 3.13 FATAL_ERROR)

list(APPEND CMAKE_MODULE_PATH ${CMAKE_CURRENT_SOURCE_DIR}/cmake)

include(ClangAnalyzers)

# Inspect for syscalls at ${module}/include directory and expose proprietary
# Zephyr Drivers APIs.
list(APPEND SYSCALL_INCLUDE_DIRS ${CMAKE_CURRENT_SOURCE_DIR}/include)
set(SYSCALL_INCLUDE_DIRS ${SYSCALL_INCLUDE_DIRS} PARENT_SCOPE)

zephyr_include_directories(include)

add_subdirectory(drivers)
add_subdirectory(components)
