__author__ = 'matth'
import sys
import os
from py2exe.build_exe import py2exe as build_exe
from py2exe.build_exe import Target
import tempfile
import subprocess
from distutils.dist import Distribution
import ctypes.util
import shutil

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

    def create_tmp_dir(self):
        tdir = tempfile.mkdtemp(prefix="pyexebuild")
        return tdir

    def clean_up_tmp_dir(self, tdir):
        pass

    def build(self):
        self._tdir = self.create_tmp_dir()
        try:
            _custom_py2exe(self, Distribution()).build_exe()
            python_dll = ctypes.util.find_library("Python27.dll")
            if not python_dll or not os.path.exists(python_dll):
                raise Exception("Cannot find Python27.dll")
            shutil.copy2(python_dll, self.dest_dir)
        finally:
            self.clean_up_tmp_dir(self._tdir)
            self._tdir = None

    def get_relative_built_in_python_path(self):
        p = subprocess.check_output([self.get_python_executable(), "-S", "-s", "-E", "-c", "import sys; print sys.path"])
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

    def get_code_snippet_to_set_sys_path(self):
        return r"""
sys.path = %s[(sys.prefix if p == '.' else sys.prefix + "\\" + p) for p in %r]
import site
sys.path += [(sys.prefix + "\\" + p) for p in %r]
""" % (
            ("[''] + " if self.include_cwd_in_pythonpath() else ""),
            self.get_relative_built_in_python_path(),
            self.get_extra_relative_path_elements())

    def get_extra_relative_path_elements(self):
        e = []

        #pywintypes and pythoncom have weird contortions to find DLLs: (look at the source in pywintypes.py)
        #They also do something different if 'frozen' - which is the case when running from the exe
        #We need to find the pywin32_system32 folder in our python tree and add it to the pythonpath:
        try:
            import win32com
            pywin32_system32 = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(win32com.__file__)), 'pywin32_system32'))
            if not os.path.exists(pywin32_system32):
                raise Exception("Expected to find 'pywin32_system32' directory here: %s" % pywin32_system32)
            if not in_directory(pywin32_system32, sys.prefix):
                raise Exception("Expected 'pywin32_system32' directory to be a subdirectory of sys.prefix (%s): %s" %( sys.prefix, pywin32_system32))
            e.append(os.path.relpath(pywin32_system32, sys.prefix))
        except ImportError as e:
            pass

        return e

# Subclass Target to specify these executables require Administrator
class AdminTarget(Target):
    uac_info = "requireAdministrator"

class _custom_py2exe(build_exe):

    def __init__(self, exe_builder, *args, **kwargs):
        build_exe.__init__(self, *args, **kwargs)
        self._tmp_file_list = []
        self.exe_builder = exe_builder

    def get_boot_script(self, boot_type):
        bootscript = build_exe.get_boot_script(self, boot_type)
        if boot_type == 'common':

            with open(bootscript, 'r') as f:
                src = f.read()

            src = r"""
# Fix up the system path so that we can run off a normal python install:

import sys

""" + \
                  self.exe_builder.get_code_snippet_to_set_sys_prefixes() + self.exe_builder.get_code_snippet_to_set_sys_path() + src

            name = os.path.join(self.exe_builder._tdir, 'exe-builder-boot.py')
            self._tmp_file_list.append(name)
            with open(name, "w") as f:
                f.write(src)

            return name
        return bootscript

    def build_exe(self):
        target_class = AdminTarget if self.exe_builder.needs_admin else Target
        try:
            self.dist_dir = self.exe_builder.dest_dir
            self.lib_dir = self.dist_dir
            self.distribution.zipfile = 'Dummy'
            self.bundle_files = 3
            self.skip_archive = True
            arcname = '.'
            args = {}
            if self.exe_builder.icon:
                args['icon_resources'] = [(1, self.exe_builder.icon)]
            if self.exe_builder.script or self.exe_builder.module_name:
                if self.exe_builder.module_name:
                    src = r"""
import runpy
runpy.run_module(%r, run_name='__main__', alter_sys=True)
""" % self.exe_builder.module_name
                    name = os.path.join(self.exe_builder._tdir, '%s.py' % self.exe_builder.module_exe_base_name)
                    self._tmp_file_list.append(name)
                    with open(name, "w") as f:
                        f.write(src)
                    script = name
                else:
                    script = self.exe_builder.script

                target = target_class(script=script, **args)
                target.validate()
                self.build_executable(target,
                                      self.get_console_template() if self.exe_builder.console else self.get_windows_template(),
                                      arcname, target.script)
            elif self.exe_builder.service_module:
                target = target_class(
                    modules=[self.exe_builder.service_module],
                    cmdline_style='custom',
                    dest_base=self.exe_builder.module_exe_base_name,
                    **args)
                target.validate()
                self.build_service(target, self.get_service_template(),
                               arcname)
        finally:
            for f in self._tmp_file_list:
                if os.path.exists(f):
                    try:
                        os.remove(f)
                    except:
                        pass

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

