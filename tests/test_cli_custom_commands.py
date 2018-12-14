import os
from inspect import cleandoc

from bocadillo.cli import create_cli


def test_can_init_custom_commands(runner, tmpdir):
    cli = create_cli()

    result = runner.invoke(cli, ["init:custom", "-d", str(tmpdir)])

    assert result.exit_code == 0
    output = result.output.lower()
    for item in "generated", "open the file":
        assert item in output


def test_can_provide_custom_commands(runner, tmpdir):
    boca_dot_py = tmpdir.join("boca.py")

    boca_dot_py.write(
        cleandoc(
            """
    import click

    @click.group()
    def cli():
        pass

    @cli.command()
    def hello():
        click.echo("Hello!")
    """
        )
    )

    os.environ["BOCA_CUSTOM_COMMANDS_FILE"] = str(boca_dot_py)

    cli = create_cli()
    result = runner.invoke(cli, ["hello"])

    assert result.exit_code == 0
    assert result.output == "Hello!\n"
