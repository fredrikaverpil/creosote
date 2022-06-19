import sys

import click

import userpath as up
from userpath.shells import DEFAULT_SHELLS, SHELLS


CONTEXT_SETTINGS = {'help_option_names': ['-h', '--help']}


def echo_success(text, nl=True):
    click.secho(text, fg='cyan', bold=True, nl=nl)


def echo_failure(text, nl=True):
    click.secho(text, fg='red', bold=True, nl=nl, err=True)


def echo_warning(text, nl=True):
    click.secho(text, fg='yellow', bold=True, nl=nl)


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option()
def userpath():
    pass


@userpath.command(context_settings=CONTEXT_SETTINGS, short_help='Prepends to the user PATH')
@click.argument('locations', required=True, nargs=-1)
@click.option(
    '-s',
    '--shell',
    'shells',
    multiple=True,
    type=click.Choice(sorted(SHELLS)),
    help=(
        'The shell in which PATH will be modified. This can be selected multiple times and has no '
        'effect on Windows. The default shells are: {}'.format(', '.join(sorted(DEFAULT_SHELLS)))
    ),
)
@click.option(
    '-a',
    '--all-shells',
    is_flag=True,
    help=(
        'Update PATH of all supported shells. This has no effect on Windows as environment settings are already global.'
    ),
)
@click.option('--home', help='Explicitly set the home directory.')
@click.option('-f', '--force', is_flag=True, help='Update PATH even if it appears to be correct.')
@click.option('-q', '--quiet', is_flag=True, help='Suppress output for successful invocations.')
def prepend(locations, shells, all_shells, home, force, quiet):
    """Prepends to the user PATH. The shell must be restarted for the update to
    take effect.
    """
    if not force:
        for location in locations:
            if up.in_current_path(location):
                echo_warning((
                    'The directory `{}` is already in PATH! If you '
                    'are sure you want to proceed, try again with '
                    'the -f/--force flag.'.format(location)
                ))
                sys.exit(2)
            elif up.in_new_path(location, shells=shells, all_shells=all_shells, home=home):
                echo_warning((
                    'The directory `{}` is already in PATH, pending a shell '
                    'restart! If you are sure you want to proceed, try again '
                    'with the -f/--force flag.'.format(location)
                ))
                sys.exit(2)

    try:
        up.prepend(locations, shells=shells, all_shells=all_shells, home=home, check=True)
    except Exception as e:
        echo_failure(str(e))
        sys.exit(1)
    else:
        if not quiet:
            echo_success('Success!')


@userpath.command(context_settings=CONTEXT_SETTINGS, short_help='Appends to the user PATH')
@click.argument('locations', required=True, nargs=-1)
@click.option(
    '-s',
    '--shell',
    'shells',
    multiple=True,
    type=click.Choice(sorted(SHELLS)),
    help=(
        'The shell in which PATH will be modified. This can be selected multiple times and has no '
        'effect on Windows. The default shells are: {}'.format(', '.join(sorted(DEFAULT_SHELLS)))
    ),
)
@click.option(
    '-a',
    '--all-shells',
    is_flag=True,
    help=(
        'Update PATH of all supported shells. This has no effect on Windows as environment settings are already global.'
    ),
)
@click.option('--home', help='Explicitly set the home directory.')
@click.option('-f', '--force', is_flag=True, help='Update PATH even if it appears to be correct.')
@click.option('-q', '--quiet', is_flag=True, help='Suppress output for successful invocations.')
def append(locations, shells, all_shells, home, force, quiet):
    """Appends to the user PATH. The shell must be restarted for the update to
    take effect.
    """
    if not force:
        for location in locations:
            if up.in_current_path(location):
                echo_warning((
                    'The directory `{}` is already in PATH! If you '
                    'are sure you want to proceed, try again with '
                    'the -f/--force flag.'.format(location)
                ))
                sys.exit(2)
            elif up.in_new_path(location, shells=shells, all_shells=all_shells, home=home):
                echo_warning((
                    'The directory `{}` is already in PATH, pending a shell '
                    'restart! If you are sure you want to proceed, try again '
                    'with the -f/--force flag.'.format(location)
                ))
                sys.exit(2)

    try:
        up.append(locations, shells=shells, all_shells=all_shells, home=home, check=True)
    except Exception as e:
        echo_failure(str(e))
        sys.exit(1)
    else:
        if not quiet:
            echo_success('Success!')


@userpath.command(context_settings=CONTEXT_SETTINGS, short_help='Checks if locations are in the user PATH')
@click.argument('locations', required=True, nargs=-1)
@click.option(
    '-s',
    '--shell',
    'shells',
    multiple=True,
    type=click.Choice(sorted(SHELLS)),
    help=(
        'The shell in which PATH will be modified. This can be selected multiple times and has no '
        'effect on Windows. The default shells are: {}'.format(', '.join(sorted(DEFAULT_SHELLS)))
    ),
)
@click.option(
    '-a',
    '--all-shells',
    is_flag=True,
    help=(
        'Update PATH of all supported shells. This has no effect on Windows as environment settings are already global.'
    ),
)
@click.option('--home', help='Explicitly set the home directory.')
@click.option('-q', '--quiet', is_flag=True, help='Suppress output for successful invocations.')
def verify(locations, shells, all_shells, home, quiet):
    """Checks if locations are in the user PATH."""
    for location in locations:
        if up.in_current_path(location):
            if not quiet:
                echo_success('The directory `{}` is in PATH!'.format(location))
        elif up.in_new_path(location, shells=shells, all_shells=all_shells, home=home):
            echo_warning('The directory `{}` is in PATH, pending a shell restart!'.format(location))
            sys.exit(2)
        else:
            echo_failure('The directory `{}` is not in PATH!'.format(location))
            sys.exit(1)
