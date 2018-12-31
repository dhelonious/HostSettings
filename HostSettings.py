import os
import platform
import sublime
import sublime_plugin

SETTINGS = {
    "user": "Preferences.sublime-settings",
    "global": "Preferences (All).sublime-settings",
    "local": "Preferences ({}).sublime-settings".format(platform.node()),
}
LOADED = {
    "user": None,
    "global": None,
    "local": None,
}

def console_print(msg):
    print("HostSettings: {}".format(msg))

def load_user_resource_keys(filename):
    keys = []
    settings_files = sublime.find_resources(filename)
    if settings_files:
        settings_file = settings_files[-1]
        settings_path = os.path.dirname(settings_file)
        if os.path.split(settings_path)[-1] == "User":
            keys = list(
                sublime.decode_value(sublime.load_resource(settings_file))
            )
    return keys

def copy_settings(key, from_settings, into_settings):
    setting = LOADED[from_settings].get(key)
    if setting:
        LOADED[into_settings].set(key, setting)

def copy_and_update_settings(key, from_settings, into_settings):
    copy_settings(key, from_settings, into_settings)
    sublime.save_settings(SETTINGS[into_settings])

def clear_unknown_settings():
    console_print("Removing unknown keys from `{}'".format(SETTINGS["user"]))

    for key in load_user_resource_keys(SETTINGS["user"]):
        if not(LOADED["global"].has(key) or LOADED["local"].has(key)):
            LOADED["user"].erase(key)

def update_user_settings():
    console_print("Updating `{}'".format(SETTINGS["user"]))

    for settings_type in ("global", "local"):
        for key in load_user_resource_keys(SETTINGS[settings_type]):
            def make_callback(key, settings):
                def callback():
                    copy_and_update_settings(key, settings, "user")
                return callback

            copy_settings(key, settings_type, "user")
            LOADED[settings_type].add_on_change(
                key,
                make_callback(key, settings_type)
            )

    clear_unknown_settings()
    sublime.save_settings(SETTINGS["user"])

def sync_settings():
    console_print("Synchronizing `{}' and `{}'".format(SETTINGS["global"], SETTINGS["local"]))

    for key in load_user_resource_keys(SETTINGS["user"]):
        if LOADED["global"].has(key):
            copy_and_update_settings(key, "user", "global")
        else:
            copy_and_update_settings(key, "user", "local")

def plugin_loaded():
    global LOADED

    LOADED["user"] = sublime.load_settings(SETTINGS["user"])
    LOADED["global"] = sublime.load_settings(SETTINGS["global"])
    LOADED["local"] = sublime.load_settings(SETTINGS["local"])

    update_user_settings()

def plugin_unloaded():
    sync_settings()

class HostSettingsListener(sublime_plugin.EventListener):
    def on_post_save(self, view):
        file_name = os.path.basename(view.file_name())
        if file_name == SETTINGS["user"]:
            sync_settings()
        elif file_name in list(SETTINGS.values()):
            settings = [key for key, value in SETTINGS.items()
                        if value == file_name][0]
            for key in load_user_resource_keys(settings):
                copy_and_update_settings(key, settings, "user")

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

class HostSettingsUpdateCommand(sublime_plugin.WindowCommand):
    def run(self):
        update_user_settings()

class HostSettingsSyncCommand(sublime_plugin.WindowCommand):
    def run(self):
        sync_settings()