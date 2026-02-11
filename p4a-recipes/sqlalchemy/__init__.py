from pythonforandroid.recipe import CompiledComponentsPythonRecipe


class SQLAlchemyRecipe(CompiledComponentsPythonRecipe):
    name = "sqlalchemy"
    version = "2.0.36"
    url = "https://files.pythonhosted.org/packages/50/65/9cbc9c4c3287bed2499e05033e207473504dc4df999ce49385fb1f8b058a/sqlalchemy-{version}.tar.gz"
    call_hostpython_via_targetpython = False
    depends = ["setuptools"]


recipe = SQLAlchemyRecipe()
