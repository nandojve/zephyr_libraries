.. _zephyr_generic_library:

Zephyr Generic Library
######################

This repository is used as Zephyr RTOS playground. It have all necessary source
code, samples and tests. This repository allows to use of QEMU for emulation
purposes.

Directory Structure
*******************

   .. code-block:: console

      .
      ├── bootloader
      ├── zgenlib (The playground)
      │   ├── boards
      │   ├── cmake
      │   ├── components
      │   ├── drivers
      │   ├── dts/bindings
      │   ├── include/zephyr
      │   ├── samples
      │   ├── scripts
      │   ├── tests
      │   ├── zephyr
      │   ├── └── module.yml
      │   ├── .clang-tidy
      │   ├── .gitignore
      │   ├── CMakeLists.txt
      │   ├── Kconfig
      │   ├── LICENSE
      │   ├── README.rst
      │   └── west.yml
      ├── modules
      └── zephyr

It is recommended develop in the playground folder. As general rule the
bootloader, modules and zephyr directory should not be touched. The ``west``
can be invoked from ``zgenlib`` most of time. However, to build zephyr
samples you must run west from project root directory and reference
``zephyr/sample/<desired sample>``.

How to clone
************

   First create your `root` directory, for instance:

   .. code-block:: console

      $ mkdir $HOME/playground-root-dir
      $ cd $HOME/playground-root-dir

   Than initialize `playground-root-dir` with the project:

   .. code-block:: console

      $ west init -m git@github.com:nandojve/zephyr_libraries
      $ west update

   After success clone and update, make sure you are in the correct branch.

   .. code-block:: console

      $ git checkout main

How to use QEMU
***************

   Cortex-M33 QEMU is enabled using `mps2_an521` board. Usually samples can run
   as following:

   .. code-block:: console

      $ west build -b mps2_an521 <sample> -t run

   Go to look sample folder and read README file for more instructions.

How to run tests
****************

   At root directory run twister pointing testcase-root as ``zgenlib`` and
   --board-root as ``zgenlib/boards``. Twister will scan by tests.yaml files
   and run one by one. The report can be checked at ./twister-out directory.

   .. code-block:: console

      $ ./zephyr/scripts/twister --testcase-root zgenlib --board-root zgenlib/boards
