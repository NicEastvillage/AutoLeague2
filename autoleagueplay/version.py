# https://stackoverflow.com/questions/458550/standard-way-to-embed-version-into-python-package

__version__ = '0.3.1'

release_notes = {
    '0.3.1': '''
        - Working directory is now set once with a command. # NicEastvillage
        - Added a fetch command that fetches a ladder from Google Sheets. # NicEastvillage
        - Added a test command and option that checks for missing bots. # NicEastvillage
    ''',
    '0.2.1': '''
        - Added a --list and --results option to show matches that will be played and their results # NicEastvillage
        - Now places info about current match in a `current_match.json` which can be used for overlays # NicEastvillage 
    ''',
    '0.1.0': '''
        - Modified DomNomNom's AutoLeague script to run League Play matches # NicEastvillage
    '''
}


def get_current_release_notes():
    if __version__ in release_notes:
        return release_notes[__version__]
    return ''


def get_help_text():
    return 'Trouble? Ask on Discord at https://discord.gg/5cNbXgG ' \
           'or report an issue at https://github.com/RLBot/RLBotTraining/issues'


def print_current_release_notes():
    print(f'Version {__version__}')
    print(get_current_release_notes())
    print(get_help_text())
    print('')
