import os
from tempfile import TemporaryDirectory


# BEWARE this will import ExeBuilder from the pip installed package instead of
# from the source tree. Always run `pip install .` before running this test
from pyexebuilder.ExeBuilder import ExeBuilder


if __name__ == '__main__':
    with TemporaryDirectory() as tmp_folder:
        ExeBuilder(tmp_folder, module_name="pyexebuilder.test.sample.helloworld_sleep", needs_admin=True).build()
        file_name = os.path.join(tmp_folder, "helloworld_sleep.exe")
        print("Manually run", file_name, "it should pop-up a UAC dialog and then print helloworld")
        input("Hit enter when you are done")
