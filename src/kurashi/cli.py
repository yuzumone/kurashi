import click

from kurashi.stock import stock


@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
def main() -> None:
    pass


main.add_command(stock)


if __name__ == "__main__":
    main()
