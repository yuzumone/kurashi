import click

from kurashi.sbi import sbi
from kurashi.zaim import zaim


@click.group(context_settings=dict(help_option_names=['-h', '--help']))
def main():
    pass


main.add_command(sbi)
main.add_command(zaim)


if __name__ == '__main__':
    main()
