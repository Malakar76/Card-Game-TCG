import shutil
from os.path import exists, join

from pythonforandroid.recipe import Recipe


class PydanticCoreRecipe(Recipe):
    """Install pydantic-core from a pre-compiled ARM64 wheel (Eutalix)."""

    version = "2.41.5"
    url = (
        "https://github.com/Eutalix/android-pydantic-core/releases/"
        "download/v{version}/"
        "pydantic_core-{version}-cp311-cp311-linux_aarch64.whl"
    )
    depends = ["python3"]

    def build_arch(self, arch):
        # p4a auto-extracts the .whl (zip) into the build directory
        build_dir = self.get_build_dir(arch.arch)
        install_dir = self.ctx.get_python_install_dir(arch.arch)

        src = join(build_dir, "pydantic_core")
        dst = join(install_dir, "pydantic_core")

        if exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)


recipe = PydanticCoreRecipe()
