import sh
from pythonforandroid.logger import shprint
from pythonforandroid.recipe import PythonRecipe


class PydanticRecipe(PythonRecipe):
    """Pydantic v2 recipe using pip (pyproject.toml, no setup.py)."""

    version = "2.10.6"
    url = "https://github.com/pydantic/pydantic/archive/refs/tags/v{version}.zip"
    depends = ["python3", "setuptools"]
    call_hostpython_via_targetpython = False
    site_packages_name = "pydantic"

    def install_python_package(self, arch, name=None, env=None, is_dir=True):
        env = env or self.get_recipe_env(arch)
        hostpython = sh.Command(self.hostpython_location)
        install_dir = self.ctx.get_python_install_dir(arch.arch)
        # Install from PyPI wheel (pure Python, no compilation needed)
        shprint(
            hostpython,
            "-m",
            "pip",
            "install",
            "--no-deps",
            "--target",
            install_dir,
            f"pydantic=={self.version}",
            _env=env,
        )


recipe = PydanticRecipe()
