import os
import platform
import sublime
import sublime_plugin

PLUGIN = "HostSettings"
SETTINGS = {
    "user": "Preferences.sublime-settings",
    "global": "Preferences (All).sublime-settings",
    "package": "HostSettings.sublime-settings",
}
LOADED = {}
HOSTNAME = platform.node()

def console_print(msg):
    print("HostSettings: {}".format(msg))

def load_user_resource_keys(settings_type):
    keys = []
    settings_files = sublime.find_resources(SETTINGS[settings_type])
    if settings_files:
        settings_file = settings_files[-1]
        settings_path = os.path.dirname(settings_file)
        if os.path.split(settings_path)[-1] == "User":
            keys = list(
                sublime.decode_value(sublime.load_resource(settings_file))
            )
    return keys

def copy_settings(from_settings, into_settings, overwrite=False):
    copied = False
    for key in load_user_resource_keys(from_settings):
        setting = LOADED[from_settings].get(key)
        if(LOADED[into_settings].has(key)
           and not LOADED[into_settings].get(key) == setting
           or overwrite):
            LOADED[into_settings].set(key, setting)
            copied = True

    if copied:
        console_print("Updated `{}'".format(SETTINGS[into_settings]))
    return copied

def clear_unknown_settings(settings_type):
    erased = False
    if settings_type == "user":
        for key in load_user_resource_keys("user"):
            if not(LOADED["global"].has(key) or LOADED["local"].has(key)):
                LOADED["user"].erase(key)
                erased = True
    else:
        for key in load_user_resource_keys("global"):
            if not LOADED["user"].has(key):
                LOADED["global"].erase(key)
                erased = True
        for key in load_user_resource_keys("local"):
            if not LOADED["user"].has(key):
                LOADED["local"].erase(key)
                erased = True

    if erased:
        console_print("Removed unknown keys from `{}'".format(
            SETTINGS[settings_type]
        ))

def save_settings(settings_type):
    sublime.save_settings(SETTINGS[settings_type])

def clear_on_change():
    for settings_type in ("global", "local", "user"):
        LOADED[settings_type].clear_on_change(PLUGIN)

def add_on_change():
    for settings_type in ("global", "local", "user"):
        LOADED[settings_type].add_on_change(
            PLUGIN,
            make_callback(settings_type)
        )

def make_callback(settings_type):
    def callback():
        clear_on_change()
        if settings_type == "user":
            for key in load_user_resource_keys("user"):
                if LOADED["global"].has(key):
                    if copy_settings("user", "global"):
                        save_settings("global")
                else:
                    if copy_settings("user", "local"):
                        save_settings("local")
        else:
            if(copy_settings("global", "user")
               or copy_settings("local", "user")):
                save_settings("user")
        clear_unknown_settings(settings_type)
        add_on_change()
    return callback

def build_settings():
    console_print("Building settings file")
    clear_on_change()
    if(copy_settings("global", "user", overwrite=True)
       or copy_settings("local", "user", overwrite=True)):
        save_settings("user")
    add_on_change()

def plugin_loaded():
    global SETTINGS
    global LOADED

    for settings_type, settings_file in SETTINGS.items():
        LOADED[settings_type] = sublime.load_settings(settings_file)

    # TODO: use re.match to get settings alias
    alias = LOADED["package"].get("alias", {})
    SETTINGS["local"] = "Preferences ({}).sublime-settings".format(
        alias.get(HOSTNAME, HOSTNAME)
    )
    LOADED["local"] = sublime.load_settings(SETTINGS["local"])
    console_print("Local settings: `{}'".format(SETTINGS["local"]))

    build_settings()

class HostSettingsEditCommand(sublime_plugin.WindowCommand):
    def run(self, default=None):
        user_path = os.path.join(sublime.packages_path(), "User")
        sublime.active_window().run_command(
            "open_file",
            {
                "file": os.path.join(user_path, SETTINGS["local"]),
                "contents": default
            }
        )
