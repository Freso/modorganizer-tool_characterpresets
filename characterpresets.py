#!/usr/bin/env python3
"""
LooksMenu Missing Plugins plugin

Goes through LooksMenu preset files and checks for references to
missing or non-active plugins and makes warnings for these.
"""

# Copyright © 2018 Frederik “Freso” S. Olesen <https://freso.dk/>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import json
import os.path

from collections import namedtuple

from PyQt5.QtCore import QCoreApplication, qCritical, qDebug

try:
    import mobase
except ModuleNotFoundError:
    #import mock_mobase as mobase
    mobase = type('', (), {
        'IPlugin': type('', (), {})(),
        'IPluginDiagnose': type('', (), {})(),
        'IPluginTool': type('', (), {})(),
        'ReleaseType': type('', (), {
            'prealpha': 0,
            'alpha': 1,
            'beta': 2,
            'candidate': 3,
            'final': 4,
        })(),
    })()


def is_json_file(filename):
    """Returns whether the specified filename indicates a JSON file."""
    return filename[-5:] == '.json'


class LooksMenuMissingPlugins(mobase.IPluginDiagnose):
    """"""

    def __tr(self, str):
        return QCoreApplication.translate('LooksMenuMissingPlugins', str)

    def __init__(self):
        super(LooksMenuMissingPlugins, self).__init__()
        self.__organizer = None
        self.NAME = 'LooksMenu Missing Plugins'
        self.AUTHOR = 'Freso'
        self.VERSION = mobase.VersionInfo(0, 0, 1, mobase.ReleaseType.prealpha)
        self.DESCRIPTION = 'Looks over LooksMenu preset files and checks ' \
                           'for any references to plugins that are either ' \
                           'completely missing or currently not active.'
        self.presets_with_missing_plugins = {}

    def init(self, organizer):
        self.__organizer = organizer

        organizer.modList().onModStateChanged(lambda modName, modState: self._invalidate())

        return True

    def name(self):
        return self.__tr(self.NAME)

    def displayName(self):
        return self.name()

    def author(self):
        return self.AUTHOR

    def description(self):
        return self.__tr(self.DESCRIPTION)

    def tooltip(self):
        return self.description()

    def version(self):
        return self.VERSION

    def settings(self):
        return [
            mobase.PluginSetting('enabled', self.__tr('Enable this plugin'), True)
        ]

    def isActive(self):
        return bool(self.__organizer.pluginSetting(self.NAME, 'enabled'))

    def shortDescription(self, key):
        preset = self.presets_with_missing_plugins[key]
        return self.__tr(
            'LooksMenu preset "{}" is missing one or more plugins.').format(
                preset.preset,
            )

    def fullDescription(self, key):
        preset = self.presets_with_missing_plugins[key]
        return self.__tr(
            'The LooksMenu preset "{preset}" from the "{source}" mod is '
            'missing one or more plugins: {missing_plugins}'
        ).format(
            preset=preset.preset,
            missing_plugins=', '.join(preset.missing_plugins),
            source=preset.source,
        )

    def activeProblems(self):
        PresetTuple = namedtuple('Preset', 'preset missing_plugins source')
        presets_with_missing_plugins = {}
        counter = 0
        plugin_list = self.__organizer.pluginList()
        plugin_list = plugin_list.pluginNames()

        # TODO: Try using .findFileInfos() instead of findFiles()
        looksmenu_presets = self.__organizer.findFiles(
            'F4SE/Plugins/F4EE/Presets', is_json_file)
        if looksmenu_presets == []:
            qDebug('No LooksMenu presets found.')
            return []

        for preset in looksmenu_presets:
            preset = LooksMenuPreset(preset)
            missing_plugins = preset.missing_plugins(plugin_list)
            if len(missing_plugins) > 0:
                presets_with_missing_plugins[counter] = PresetTuple(
                    preset=os.path.basename(preset.file_path),
                    missing_plugins=missing_plugins,
                    source=self.__organizer.getFileOrigins(preset.file_path),
                )
                counter += 1

        qDebug('presets_with_missing_plugins: {}'.format(presets_with_missing_plugins))  # TODO: Remove
        self.presets_with_missing_plugins = presets_with_missing_plugins
        return list(self.presets_with_missing_plugins.keys())

    def hasGuidedFix(self, key):
        return False


class LooksMenuPreset:
    """"""

    def __tr(self, str):
        return QCoreApplication.translate('LooksMenuPreset', str)

    def __init__(self, file_path):
        self.file_path = file_path
        qDebug('LMPreset file_path: {}'.format(file_path))  # TODO: Remove

    @property
    def is_valid(self):
        return self.preset_data is not False

    @property
    def preset_data(self):
        """Get preset data."""
        with open(self.file_path) as preset_file:
            try:
                return json.load(preset_file)
            except json.JSONDecodeError:
                qCritical(self.__tr('{} is not a valid LooksMenu preset.'))
                return False

    @property
    def used_plugins(self):
        """Get plugins used by the preset."""
        qDebug('preset_data: {}'.format(self.preset_data))  # TODO: Remove
        plugins = []

        # HairColor plugin
        try:
            plugins += [self.preset_data['HairColor'].split('|')[0]]
        except AttributeError:
            qDebug('{} has no HairColor attribute.'.format(self.file_path))
            pass

        # HeadParts plugin(s)
        try:
            for part in self.preset_data['HeadParts']:
                part_plugin = part.split('|')[0]
                if part_plugin not in plugins:
                    plugins += [part_plugin]
        except AttributeError:
            qDebug('{} has no HeadParts attribute.'.format(self.file_path))
            pass

        # Casting to tuple to make it immutable
        return tuple(plugins)

    def missing_plugins(self, available_plugins):
        """Compare available plugins with plugins used by the preset and return any missing ones."""
        # TODO: Make the comparison case insensitive
        missing_plugins = []
        for plugin in self.used_plugins:
            if plugin not in available_plugins:
                missing_plugins += [plugin]
        # Casting to tuple to make it immutable
        return tuple(missing_plugins)


def createPlugin():
    """Register plugin with Mod Organizer."""
    return LooksMenuMissingPlugins()


def main():
    return False


if __name__ == '__main__':
    main()