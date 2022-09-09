#!/usr/bin/env python3
#
# Copyright (c) 2022 Gerson Fernando Budke <nandojve@gmail.com>
#
# SPDX-License-Identifier: Apache-2.0
#

"""Execute clang-tidy from console

This executes clang-tidy from console. It is necessary pass a list of parameters
to configure runner. This requires that west build complete executes before run
script. This is necessary because some files and configurations are generated
during build phase.

"""

import argparse
import re
import subprocess
import json
import sys

from pyparsing import empty

def parse_args():
    global args

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument("-a", "--args", required=True, help="Clang-Tidy arguments")
    parser.add_argument("-c", "--clang_tidy", required=True, help="Clang-Tidy path")
    parser.add_argument("-p", "--path", required=True, help="Build path")
    parser.add_argument("-s", "--src_files", required=True, help="Source Files")
    parser.add_argument("--relax", action=argparse.BooleanOptionalAction, help="Relax diagnose")
    parser.add_argument("--all-files", action=argparse.BooleanOptionalAction, help="Try run diagnose on all project files")
    args = parser.parse_args()

def parse_gcc_option(path, option):
    ret = subprocess.Popen(path + " " + option,
                           shell=True,
                           stdout=subprocess.PIPE)
    return ret.stdout.readline().decode('utf-8').strip()

def extract_dir_prefix(line):
    inc_file_list = ""
    pos = line.find("=")
    if pos != -1: inc_file_list = line[pos + 1:].strip()
    return inc_file_list

def convert_gcc_to_incdir(path, machine, version):
    gcc_includes = []
    prefix = path.find("/bin")
    if prefix != -1:
        gcc_root = path[:prefix] + "/lib/gcc/" + machine + "/" + version
        gcc_includes.append(gcc_root  + "/include")
        gcc_includes.append(gcc_root  + "/include-fixed")
    return gcc_includes

def convert_gxx_to_incdir(path, machine, version):
    gcc_includes = []
    prefix = path.find("/bin")
    if prefix != -1:
        gxx_root = path[:prefix]
        if machine: gxx_root += "/" + machine
        gxx_root += "/include/c++/" + version
        gcc_includes.append(gxx_root)
        if machine: gcc_includes.append(gxx_root + "/" + machine)
    return gcc_includes

def parse_gcc_incdir(path):
    gcc_path = extract_dir_prefix(path)
    gcc_machine = parse_gcc_option(gcc_path, "-dumpmachine")
    gcc_lib = parse_gcc_option(gcc_path, "-dumpversion")
    return convert_gcc_to_incdir(gcc_path, gcc_machine, gcc_lib)

def parse_gxx_incdir(path):
    gcc_path = extract_dir_prefix(path)
    gcc_version = parse_gcc_option(gcc_path, "--version")
    gcc_machine = gcc_version.split()[0][:-4]
    gcc_lib = parse_gcc_option(gcc_path, "-dumpversion")
    return convert_gxx_to_incdir(gcc_path, gcc_machine, gcc_lib)

def parse_gcc():
    with open(args.path + "/CMakeCache.txt", "r") as file:
        for line in file:
            if line.find("CMAKE_C_COMPILER") != -1:
                return parse_gcc_incdir(line.strip())
    return []

def parse_gxx():
    with open(args.path + "/CMakeCache.txt", "r") as file:
        for line in file:
            if line.find("CMAKE_CXX_COMPILER") != -1:
                return parse_gxx_incdir(line.strip())
    return []

def load_json():
    data = []
    with open(args.path + "/compile_commands.json", "r") as file:
        data = json.load(file)
    return data

def find_cmd_line(data, src_file):
    for entry in data:
        if entry["file"] == src_file:
            entry["command"] = entry["command"].replace("\\", "")
            return entry
    return []

def find_cmd_line_generic(data, src_list):
    for entry in data:
        if entry["file"] in src_list:
            entry["command"] = entry["command"].replace("\\", "")
            return entry
    return []

def cleanup_command(cmd):
    unsupported_list = [
                  "-fno-defer-pop",
                  "-fno-freestanding",
                  "-fno-reorder-functions",
                  "-mcpu=cortex-m4",
                  "-mcpu=cortex-m7",
                  "-mthumb",
                  "-specs=nano.specs",
                  "-mfp16-format=ieee",
                 ]
    for elem in unsupported_list:
        if elem in cmd:
            cmd.remove(elem)

    if not args.relax:
        return

    relax_list = [
                    "-Wall",
                    "-Wextra",
#                    "-Wshadow",
#                    "-pedantic",
                 ]
    for elem in relax_list:
        if elem in cmd:
            cmd.remove(elem)

def add_command(cmd):
    # System Directories
    if "-isystem" in cmd:
        last_isystem_entry = len(cmd) -1 - cmd[::-1].index("-isystem") + 2
    else:
        # create a list with indexes which start with -I, then pick last one
        # and move to next position
        last_isystem_entry = [cmd.index(i) for i in cmd if i.startswith('-I')][-1] + 1
    gxx_inc_dirs = parse_gxx()
    for dir in gxx_inc_dirs:
        cmd.insert(last_isystem_entry, dir)
        cmd.insert(last_isystem_entry, "-isystem")
    gcc_inc_dirs = parse_gcc()
    for dir in gcc_inc_dirs:
        cmd.insert(last_isystem_entry, dir)
        cmd.insert(last_isystem_entry, "-isystem")

    if cmd.count("-o") > 0:
        dash_oc = cmd.index("-o")
    else:
        dash_oc = cmd.index("-c")

    # FLAGS
    mandatory_flags_list = [
                                "-ferror-limit=0",
                           ]
    for elem in mandatory_flags_list:
        cmd.insert(dash_oc, elem)

    if not args.relax:
        return

    flags_list = [
                    "-Wno-error=pedantic",      # compound literals are a C99-specific feature
                                                # delayableWork.m_cycle = K_NO_WAIT;
                    "-Wno-shorten-64-to-32",    # implicit conversion loses integer precision: 'unsigned long' to 'gpio_port_pins_t' (aka 'unsigned int')
                                                # pio_init_callback(&m_callbackContainer.m_cbData, intPinHandler, BIT(m_dt.pin));
                    "-Wno-cast-align",          # cast from 'char *' to 'Mcu::GpioIntIn::CallbackContainer *' increases required alignment from 1 to 8
                                                # CallbackContainer* cb_cont = CONTAINER_OF(cb, CallbackContainer, m_cbData);
                    "-fms-extensions",          # cast from pointer to smaller type 'uint32_t'
                                                # const __IO uint32_t *preg = __ADC_PTR_REG_OFFSET(ADCx->SQR1, ((Rank & ADC_REG_SQRX_REGOFFSET_MASK) >> ADC_SQRX_REGOFFSET_POS));
#                    "-Wno-string-conversion",
                 ]
    for elem in flags_list:
        cmd.insert(dash_oc, elem)

def main():
    parse_args()

    ret = 0
    cmd_line = []
    json_cmds = load_json()
    tidy_cmd = args.clang_tidy + " " + args.args + " "

    if args.all_files:
        src_list = re.split(' +', args.src_files)
        cmd_line = find_cmd_line_generic(json_cmds, src_list)
        if not cmd_line:
            print("---- Not found any files in the current configuration. Aboting process.")
            sys.exit(-2)
        arguments_pos = cmd_line["command"].find("-o ")
        if arguments_pos != -1:
            cmd_line["command"] = cmd_line["command"][:arguments_pos -1]

    if args.relax:
        print("---- Relax mode enabled", flush=True)
    else:
        print("---- Normal mode enabled", flush=True)

    for src_file in re.split(' +', args.src_files):
        if not args.all_files:
            cmd_line = find_cmd_line(json_cmds, src_file)
        if cmd_line:
            print("---- Looking at: " + src_file, flush=True)
            cmd_line_lst = re.split(' +', tidy_cmd + src_file +
                                    " -- " + cmd_line["command"])
            if args.all_files:
                cmd_line_lst.append("-c")
                cmd_line_lst.append(src_file)
            cleanup_command(cmd_line_lst)
            add_command(cmd_line_lst)
            with open(args.path + "/clang-tidy-cmd_invoke.txt", "w") as file:
                for param in cmd_line_lst:
                    file.write(param)
                    if param in ["-isystem", "-imacros", "-o", "-c"]:
                        file.write(" ")
                    else:
                        file.write("\n")
                file.write("\n\n")
                for param in cmd_line_lst:
                    file.write(param)
                    file.write(" ")
                file.write("\n")
            rets = subprocess.run(cmd_line_lst,
                                  stderr=subprocess.PIPE,
                                  cwd=cmd_line["directory"])
            if rets.returncode != 0:
                ret = rets.returncode
    if ret != 0:
        print("run-clang-tidy.py error code: " + str(ret))
    sys.exit(ret)

if __name__ == "__main__":
    main()
