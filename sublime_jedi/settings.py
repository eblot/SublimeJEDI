import sublime
from os import sep as pathsep
from os import walk
from os.path import basename, dirname, isdir, join as joinpath


# caches to reduce useless directory scanning
_projects = {}
_paths = {}


def _get_project_paths(view, find_dir, match_dir):
    """Handle path property '<matchdir:a:b>'' in "python_package_paths"
        where:
          * a is a path suffix to locate to match a projec top directory
          * b is the path suffix considered as a package directory to add to
              the JEDI Python path
        example:
          x/y/a:     -> x/y gets defined as the top dir to look for modules
          x/y/z/b:   -> match 'b', added to the Python path
          x/y/z/c:   -> not match, ignored
          x/y/u/v/b: -> match 'b', added to the Python path
    """
    if not view:
        return []
    file_name = view.file_name()
    if not file_name:
        return []
    projdir = curdir = dirname(file_name)
    global _projects
    global _paths
    if projdir not in _projects:
        maxrecurse = 100
        while curdir and curdir != pathsep:
            maxrecurse -= 1
            if not maxrecurse:
                return []
            match_path = joinpath(curdir, find_dir)
            if isdir(match_path):
                _projects[projdir] = curdir
                break
            curdir = dirname(curdir)
        else:
            return []
    topdir = _projects[projdir]
    if topdir not in _paths:
        paths = [joinpath(topdir, find_dir)]
        for dirpath, dirnames, filenames in walk(topdir):
            if basename(dirpath) == match_dir:
                paths.append(dirpath)
                dirnames[:] = []
            else:
                dirnames[:] = [d for d in dirnames if not d.startswith('.') and
                               d != '__pycache__']
        _paths[topdir] = paths
    return _paths[topdir]


def get_plugin_settings():
    setting_name = 'sublime_jedi.sublime-settings'
    plugin_settings = sublime.load_settings(setting_name)
    return plugin_settings


def get_settings_param(view, param_name, default=None):
    plugin_settings = get_plugin_settings()
    project_settings = view.settings()
    value = project_settings.get(
        param_name,
        plugin_settings.get(param_name, default)
    )
    if param_name == 'python_package_paths':
        if isinstance(value, list):
            values = []
            for val in value:
                if val.startswith('<matchdir:'):
                    try:
                        _, find_dir, match_dir = val[1:-1].split(':')
                        paths = _get_project_paths(view, find_dir, match_dir)
                    except Exception:
                        print("ERROR")
                        paths = []
                    if paths:
                        values.extend(paths)
                else:
                    values.append(val)
            value = values
    return value
