import os
import platform
import sublime
import sublime_plugin

SETTINGS = {
    "user": "Preferences.sublime-settings",
    "global": "Preferences (All).sublime-settings",
    "local": "Preferences ({}).sublime-settings".format(platform.node()),
    "package": "HostSettings.sublime-settings",
}
LOADED = { key: None for key in list(SETTINGS) }

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
    if setting and not LOADED[into_settings].get(key) == setting:
        LOADED[into_settings].set(key, setting)
        return True
    else:
        return False

def copy_and_update_settings(key, from_settings, into_settings):
    if copy_settings(key, from_settings, into_settings):
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
                    if copy_settings(key, settings, "user"):
                        sublime.save_settings(SETTINGS["user"])
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
            copy_settings(key, "user", "global")
        else:
            copy_settings(key, "user", "local")

    sublime.save_settings(SETTINGS["global"])
    sublime.save_settings(SETTINGS["local"])

def plugin_loaded():
    global LOADED
    for settings_type in list(SETTINGS):
        LOADED[settings_type] = sublime.load_settings(SETTINGS[settings_type])

    update_user_settings()

    sync_interval = LOADED["package"].get("sync_interval")*1e3
    if sync_interval:
        def auto_sync_settings():
            sync_settings()
            sublime.set_timeout_async(auto_sync_settings, sync_interval)

        sublime.set_timeout_async(auto_sync_settings, sync_interval)

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
                copy_settings(key, settings, "user")
            sublime.save_settings(SETTINGS["user"])

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