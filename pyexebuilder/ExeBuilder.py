__author__ = 'matth'
import ctypes.util
import os
import shutil
import subprocess
import sys
import tempfile

if sys.version_info[0] == 2:
    from .custom_py2exe_py2 import custom_py2exe
else:
    from .custom_py2exe_py3 import custom_py2exe


def in_directory(f, directory):
    #make both absolute
    directory = os.path.join(os.path.abspath(directory), '')
    f = os.path.abspath(f)

    if sys.platform.startswith('win'):
        directory = directory.lower()
        f = f.lower()

    #return true, if the common prefix of both is equal to directory
    #e.g. /a/b/c/d.rst and directory is /a/b, the common prefix is /a/b
    return os.path.commonprefix([f, directory]) == directory


class ExeBuilder(object):

    def __init__(self, dest_dir, script=None, module_name=None, module_exe_name=None, service_module=None, needs_admin=False, icon=None, console=True):
        self.dest_dir = dest_dir
        self.script = script
        self.service_module = service_module
        self.module_name = module_name
        if service_module or module_name:
            self.module_exe_base_name = os.path.splitext(module_exe_name)[0] if module_exe_name else (service_module or module_name).split('.')[-1]
        else:
            self.module_exe_base_name = None
        self.needs_admin = needs_admin
        self.icon = icon
        self.console = console
        self._tdir = None

    def include_cwd_in_pythonpath(self):
        return True

    def include_pythoncom_and_pywintypes_in_pythonpath(self):
        return True

    def create_tmp_dir(self):
        tdir = tempfile.mkdtemp(prefix="pyexebuild")
        return tdir

    def clean_up_tmp_dir(self, tdir):
        pass

    def get_extra_relative_path_elements(self):
        e = []
        # pywintypes and pythoncom have weird contortions to find DLLs: (look at the source in pywintypes.py)
        # They also do something different if 'frozen' - which is the case when running from the exe
        # We need to add the pywin32_system32 folder to the pythonpath:
        if self.include_pythoncom_and_pywintypes_in_pythonpath():
            e.append("Lib\\site-packages\\pywin32_system32")
        return e

    def build(self):
        self._tdir = self.create_tmp_dir()
        try:
            custom_py2exe(self).build_exe()
            python_dll_name = "Python%d%d.dll" % sys.version_info[:2]
            self._copy_dll(python_dll_name)
            if sys.version_info[0] == 3:
                self._copy_dll("Python3.dll")
            python_dll = ctypes.util.find_library(python_dll_name)
            if not python_dll or not os.path.exists(python_dll):
                raise Exception("Cannot find " + python_dll_name)
            shutil.copy2(python_dll, self.dest_dir)
        finally:
            self.clean_up_tmp_dir(self._tdir)
            self._tdir = None

    def _copy_dll(self, dll_name):
        dll = ctypes.util.find_library(dll_name)
        if not dll or not os.path.exists(dll):
            raise Exception("Cannot find " + dll_name)
        shutil.copy2(dll, self.dest_dir)

    def get_relative_built_in_python_path(self):
        p = subprocess.check_output([self.get_python_executable(), "-S", "-s", "-E", "-c", "import sys; print(sys.path)"])
        pythonpath = eval(p)

        pythonpath = filter(
            lambda p: os.path.isabs(p),
            pythonpath)

        pythonpath = filter(
            lambda p: os.path.exists(p),
            pythonpath)

        pythonpath = filter(
            lambda p: p.lower().rstrip('\\') == sys.prefix.lower().rstrip('\\') or in_directory(p, sys.prefix),
            pythonpath)

        pythonpath = [os.path.relpath(p, sys.prefix) for p in pythonpath]

        return pythonpath

    def get_python_executable(self):
        return sys.executable

    def get_code_snippet_to_set_sys_prefixes(self):
        return r"""
sys.prefix = %r
sys.exec_prefix = %r
""" % (sys.prefix, sys.exec_prefix)

    def get_relative_lib_path(self):
        """Returns path to python library files (usually <sys.prefix>/Lib/) relative to the executable"""
        lib_path = os.path.join(sys.prefix, "Lib")
        exe_path = self.dest_dir
        relative_lib_path = os.path.relpath(lib_path, exe_path)
        return relative_lib_path

    def get_code_snippet_to_set_sys_path(self):
        return r"""
sys.path = %s[(sys.prefix if p == '.' else sys.prefix + "\\" + p) for p in %r]
import site
site.main() # Needed for Python 3.3 and up. Called automatically in 3.2 and below
""" % (
            ("[''] + " if self.include_cwd_in_pythonpath() else ""),
            self.get_relative_built_in_python_path() + self.get_extra_relative_path_elements())


if __name__ == '__main__':
    default_dest_dir = os.path.join(os.path.dirname(sys.prefix), "bin")
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--script',help='Define a script to be made into an executable')
    parser.add_argument('--module-name',help='Specify a module that should be run using runpy (i.e. like python -m)')
    parser.add_argument('--module-exe-name',help='Specify name of the exe to produce for a module based exe (service-module or module-name)')
    parser.add_argument('--service-module', help='A module to make into a Windows service')
    parser.add_argument('--dest-dir', help='Destination directory', default=default_dest_dir)
    parser.add_argument('--icon', help='Icon to use for the executable', default=None)
    parser.add_argument('--admin', action="store_true", default=False, help="If specified, the created exe will request Administrator privileges")
    options = parser.parse_args(sys.argv[1:])
    if not options.script and not options.service_module and not options.module_name:
        parser.error("Must provide either a script, a module name or a service module name")
    ExeBuilder(options.dest_dir, options.script, options.module_name, options.module_exe_name, options.service_module, options.admin, options.icon).build()

