import click
from kurashi.tepco import tepco
from kurashi.water import water
from kurashi.aeon_bank import aeon_bank


@click.group(context_settings=dict(help_option_names=['-h', '--help']))
def main():
    pass


main.add_command(tepco)
main.add_command(water)
main.add_command(aeon_bank)


if __name__ == '__main__':
    main()
