# Copyright (c) 2022 Gerson Fernando Budke <nandojve@gmail.com>
#
# SPDX-License-Identifier: Apache-2.0
#

option(ENABLE_CLANG_TIDY "Enable static analysis with clang-tidy" OFF)
option(ENABLE_CLANG_TIDY_RELAXED "Instruct script to run clang-tidy changing compiler flags" OFF)
option(ENABLE_CLANG_TIDY_TRY_ALL "Instruct script to try diagnose all files" OFF)

# Additional target to perform clang-format/clang-tidy run
# Requires clang-format and clang-tidy

# Get all project files
file(GLOB_RECURSE CLANG_ALL_SRC_FILES
        ${PROJECT_SOURCE_DIR}/components/*.cpp
#        ${PROJECT_SOURCE_DIR}/components/*.c
        ${PROJECT_SOURCE_DIR}/drivers/*.cpp
#        ${PROJECT_SOURCE_DIR}/drivers/*.c
        ${PROJECT_SOURCE_DIR}/samples/*.cpp
#        ${PROJECT_SOURCE_DIR}/samples/*.c
        ${PROJECT_SOURCE_DIR}/tests/*.cpp
#        ${PROJECT_SOURCE_DIR}/tests/*.c
)

if(ENABLE_CLANG_TIDY)
        set(CLANG_TIDY_RELAXED "--no-relax")
        set(CLANG_TIDY_TRY_ALL "--no-all-files")

        if(ENABLE_CLANG_TIDY_RELAXED)
                set(CLANG_TIDY_RELAXED "--relax")

                # WHITELIST
                list(REMOVE_ITEM CLANG_ALL_SRC_FILES
                        ${PROJECT_SOURCE_DIR}/src/cxa_handlers.cpp
                )
        endif()

        if(ENABLE_CLANG_TIDY_TRY_ALL)
                set(CLANG_TIDY_TRY_ALL "--all-files")
        endif()

        find_program(CLANGTIDY clang-tidy)
        if(CLANGTIDY)
                add_custom_target(
                        clang-tidy ALL
                        COMMAND ${PYTHON_EXECUTABLE} "${PROJECT_SOURCE_DIR}/scripts/run_clang_tidy.py"
                        -p ${APPLICATION_BINARY_DIR}
                        -c ${CLANGTIDY}
                        -a \"--export-fixes=diagnose.yaml --config-file=${PROJECT_SOURCE_DIR}/.clang-tidy --use-color -extra-arg=-Wno-unknown-warning-option --extra-arg-before=--driver-mode=g++\"
                        -s \"${CLANG_ALL_SRC_FILES}\"
                        ${CLANG_TIDY_RELAXED}
                        ${CLANG_TIDY_TRY_ALL}
                )
        else()
                message(SEND_ERROR "clang-tidy requested but executable not found")
        endif()
endif()
