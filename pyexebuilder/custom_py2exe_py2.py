from distutils.dist import Distribution
import os

from py2exe.build_exe import Target
from py2exe.build_exe import py2exe as build_exe


# Subclass Target to specify these executables require Administrator
class AdminTarget(Target):
    uac_info = "requireAdministrator"


class custom_py2exe(build_exe):

    def __init__(self, exe_builder, *args, **kwargs):
        build_exe.__init__(self, Distribution())
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

""" + self.exe_builder.get_code_snippet_to_set_sys_prefixes() + self.exe_builder.get_code_snippet_to_set_sys_path() + src
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