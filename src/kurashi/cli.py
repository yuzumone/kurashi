import click

from kurashi.zaim import zaim


@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
def main() -> None:
    pass


main.add_command(zaim)


if __name__ == "__main__":
    main()
