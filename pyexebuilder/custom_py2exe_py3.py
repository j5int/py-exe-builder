import marshal
import os
from argparse import Namespace
from distutils.dist import Distribution

from py2exe.distutils_buildexe import py2exe as build_exe
from py2exe.runtime import Target, Runtime, RT_MANIFEST

# Copied from http://docwiki.embarcadero.com/RADStudio/Sydney/en/Customizing_the_Windows_Application_Manifest_File
runAsAdminManifest = '''\
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
 <dependency>
   <dependentAssembly>
     <assemblyIdentity
       type="win32"
       name="Microsoft.Windows.Common-Controls"
       version="6.0.0.0"
       publicKeyToken="6595b64144ccf1df"
       language="*"
       processorArchitecture="*"/>
   </dependentAssembly>
 </dependency>
 <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
   <security>
     <requestedPrivileges>
       <requestedExecutionLevel
         level="requireAdministrator"
         uiAccess="false"/>
       </requestedPrivileges>
   </security>
 </trustInfo>
</assembly>
'''

class _custom_Runtime(Runtime):
    def __init__(self, exe_builder, *args, **kwargs):
        super(_custom_Runtime, self).__init__(*args, **kwargs)
        self.exe_builder = exe_builder

    def _create_script_data(self, target):
        code_objects = marshal.loads(super(_custom_Runtime, self)._create_script_data(target))
        src = "# Fix up the system path so that we can run off a normal python install:\n"
        src += "import sys\n"
        src += self.exe_builder.get_code_snippet_to_set_sys_prefixes()
        src += self.exe_builder.get_code_snippet_to_set_sys_path()
        # code_objects[0] also sets sys.prefix so we need to put this after it
        code_objects.insert(1, compile(src, "<pyexebuilder sys.prefix sys.path fixup>", "exec", optimize=self.options.optimize))
        return marshal.dumps(code_objects)


class custom_py2exe(build_exe):

    def __init__(self, exe_builder, *args, **kwargs):
        build_exe.__init__(self, Distribution())
        self._tmp_file_list = []
        self.exe_builder = exe_builder

    def build_exe(self):
        try:
            args = {}
            if self.exe_builder.needs_admin:
                args['other_resources'] = [(RT_MANIFEST, 1, runAsAdminManifest)]
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
                exe_type = 'console_exe' if self.exe_builder.console else 'windows_exe'
                target = Target(script=script, exe_type=exe_type, **args)
                target.validate()
                r = _custom_Runtime(self.exe_builder, self.get_options(self.exe_builder.dest_dir))
                r.analyze()
                exe_path = os.path.join(self.exe_builder.dest_dir, target.get_dest_base() + '.exe')
                r.build_exe(target, exe_path, self.exe_builder.get_relative_lib_path())
            elif self.exe_builder.service_module:
                target = Target(
                    exe_type='service',
                    modules=[self.exe_builder.service_module],
                    cmdline_style='custom',
                    dest_base=self.exe_builder.module_exe_base_name,
                    **args
                )
                target.validate()
                r = _custom_Runtime(self.exe_builder, self.get_options(self.exe_builder.dest_dir))
                r.analyze()
                exe_path = os.path.join(self.exe_builder.dest_dir, target.get_dest_base() + '.exe')
                r.build_exe(target, exe_path, self.exe_builder.get_relative_lib_path())
        finally:
            for f in self._tmp_file_list:
                if os.path.exists(f):
                    try:
                        os.remove(f)
                    except:
                        pass

    def get_options(self, destdir):
        options = Namespace(
            unbuffered=self.unbuffered,
            optimize=self.optimize,
            includes=self.includes,
            excludes=self.excludes,
            ignores=self.ignores,
            packages=self.packages,
            dist_dist=self.exe_builder.dest_dir,
            dll_excludes=self.dll_excludes,
            typelibs=self.typelibs,
            bundle_files=3,
            skip_archive=True,
            ascii=self.ascii,
            verbose=0,
            report=False,
            summary=False,
            show_from=None,
            compress=self.compressed,
            use_assembly=self.use_assembly,
            script=[],
            service=[],
            com_servers=[],
            destdir=destdir,
        )
        return options
