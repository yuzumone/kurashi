import click
from kurashi.tepco import tepco
from kurashi.water import water


@click.group(context_settings=dict(help_option_names=['-h', '--help']))
def main():
    pass


main.add_command(tepco)
main.add_command(water)


if __name__ == '__main__':
    main()
