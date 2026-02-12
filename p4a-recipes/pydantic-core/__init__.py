import os
import shutil
import zipfile
from os.path import exists, join

from pythonforandroid.recipe import Recipe


class PydanticCoreRecipe(Recipe):
    """Install pydantic-core from a pre-compiled ARM64 wheel."""

    version = "2.41.5"
    url = (
        "https://github.com/Eutalix/android-pydantic-core/releases/"
        "download/v{version}/"
        "pydantic_core-{version}-cp311-cp311-linux_aarch64.whl"
    )
    depends = ["python3"]

    def unpack(self, arch):
        """Extract .whl into build dir, keeping pydantic_core/ subdir intact.

        The default unpack renames the top-level extracted folder
        (pydantic_core) to the recipe name (pydantic-core), which makes
        build_arch unable to find pydantic_core/ inside. We extract
        directly into the build dir to preserve the original layout.
        """
        build_dir = self.get_build_dir(arch)
        os.makedirs(build_dir, exist_ok=True)

        filename = self.versioned_url.split("/")[-1]
        whl_path = join(self.ctx.packages_path, self.name, filename)

        with zipfile.ZipFile(whl_path, "r") as whl:
            whl.extractall(build_dir)

    def build_arch(self, arch):
        build_dir = self.get_build_dir(arch.arch)
        install_dir = self.ctx.get_python_install_dir(arch.arch)

        src = join(build_dir, "pydantic_core")
        dst = join(install_dir, "pydantic_core")

        if exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)


recipe = PydanticCoreRecipe()
