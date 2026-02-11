import shutil
from os.path import exists, join

from pythonforandroid.recipe import PythonRecipe


class PydanticRecipe(PythonRecipe):
    """Pydantic v2 recipe: pure Python, copy source directly."""

    version = "2.10.6"
    url = "https://github.com/pydantic/pydantic/archive/refs/tags/v{version}.zip"
    depends = ["python3"]
    call_hostpython_via_targetpython = False
    site_packages_name = "pydantic"

    def install_python_package(self, arch, name=None, env=None, is_dir=True):
        # Pydantic v2 is pure Python - copy the package directly
        src_dir = join(self.get_build_dir(arch.arch), "pydantic")
        install_dir = self.ctx.get_python_install_dir(arch.arch)
        dst_dir = join(install_dir, "pydantic")
        if exists(dst_dir):
            shutil.rmtree(dst_dir)
        shutil.copytree(src_dir, dst_dir)


recipe = PydanticRecipe()
