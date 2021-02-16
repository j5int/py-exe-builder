import os
import signal
import subprocess
import sys
import time

import pytest

from ..ExeBuilder import ExeBuilder


@pytest.fixture()
def tmp_folder(tmp_path):
    yield str(tmp_path)


def test_script(tmp_folder):
    ExeBuilder(tmp_folder, script=os.path.join(os.path.dirname(__file__), "sample", "helloworld.py")).build()
    output = subprocess.check_output(os.path.join(tmp_folder, "helloworld.exe"))
    assert output.decode().rstrip() == "helloworld"


def test_module(tmp_folder):
    ExeBuilder(tmp_folder, module_name="pyexebuilder.test.sample.helloworld").build()
    output = subprocess.check_output(os.path.join(tmp_folder, "helloworld.exe"))
    assert output.decode().rstrip() == "helloworld"


def test_module_exe_name(tmp_folder):
    ExeBuilder(tmp_folder, module_name="pyexebuilder.test.sample.helloworld", module_exe_name="greetingspeople.exe").build()
    output = subprocess.check_output(os.path.join(tmp_folder, "greetingspeople.exe"))
    assert output.decode().rstrip() == "helloworld"


def test_service_exe():
    pytest.xfail("Not Implemented")


def compile_check_ouput(tmp_folder, script_name):
    ExeBuilder(tmp_folder, script=os.path.join(os.path.dirname(__file__), 'sample', script_name + '.py')).build()
    output = subprocess.check_output(os.path.join(tmp_folder, script_name))
    return output.decode()


@pytest.mark.xfail(reason="Not actually sure what the sys path should be")
def test_syspath(tmp_folder):
    assert compile_check_ouput(tmp_folder, "syspath").rstrip() == str(sys.path)


@pytest.mark.xfail(run=False)
def test_console():
    pass


def test_pywintypes(tmp_folder):
    try:
        import pywintypes
    except ImportError:
        pytest.mark.skip(reason="pywintypes not installed")
    assert compile_check_ouput(tmp_folder, "import_pywintypes").rstrip() == "True"


def test_is_frozen(tmp_folder):
    assert compile_check_ouput(tmp_folder, "is_frozen").rstrip() == "True"


def test_sys_prefix_set(tmp_folder):
    assert compile_check_ouput(tmp_folder, "sysprefix").rstrip() == sys.prefix


def test_import_pygit2(tmp_folder):
    # pygit2 is special in that it needs to load the python3.dll
    try:
        import pygit2
    except ImportError:
        pytest.skip("pygit2 not installed")
    else:
        assert compile_check_ouput(tmp_folder, "import_pygit2").rstrip() == pygit2.__version__


def test_win_service(tmp_folder):
    ExeBuilder(tmp_folder, service_module='pyexebuilder.test.sample.win_service').build()
    p = subprocess.Popen([os.path.join(tmp_folder, 'win_service'), 'debug'])
    time.sleep(5)
    p.send_signal(signal.CTRL_C_EVENT)
    p.wait()
    assert p.returncode == 0
