from mesonwrap import ini

_SECTION = 'wrap-file'


class WrapFile(ini.IniFile):

    directory = ini.IniField(_SECTION)
    lead_directory_missing = ini.IniField(_SECTION)
    source_url = ini.IniField(_SECTION)
    source_filename = ini.IniField(_SECTION)
    source_hash = ini.IniField(_SECTION)
    patch_url = ini.IniField(_SECTION)
    patch_filename = ini.IniField(_SECTION)
    patch_hash = ini.IniField(_SECTION)
