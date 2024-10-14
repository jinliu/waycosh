import asyncio
import json
import tempfile
import traceback

from dbus_next.aio import MessageBus
from dbus_next.service import ServiceInterface, method

from . import event_handler, kwin_script
from .window_registry import Window, WindowRegistry


class WaycoshDaemon(ServiceInterface):

    DBUS_ADDRESS = "io.github.jinliu.WaycoshDaemon"
    DBUS_PATH = "/io/github/jinliu/WaycoshDaemon"
    DBUS_INTERFACE = DBUS_ADDRESS

    SAVE_STATE_INTERVAL = 30


    def __init__(self):
        super().__init__(WaycoshDaemon.DBUS_INTERFACE)
        self.window_registry = WindowRegistry()
        self.window_registry.load_state()


    async def main_loop(self):
        self.bus = await MessageBus().connect()
        self.bus.export(WaycoshDaemon.DBUS_PATH, self)
        await self.bus.request_name(WaycoshDaemon.DBUS_ADDRESS)

        await self.load_script()

        try:
            while True:
                if self.window_registry.save_state():
                    await asyncio.sleep(WaycoshDaemon.SAVE_STATE_INTERVAL)
                else:
                    await asyncio.sleep(1)

        except:
            await self.unload_script()
            self.window_registry.save_state()


    # Our kwin script calls this method to notify us of window events.
    # We then send back a list of actions to perform, if any.
    # Currently, the only supported action is "move".
    @method()
    async def Event(self, type: 's', data: 's') -> 's':
        try:
            print("EVENT", type, data)
            print()
            w = Window.from_json(data)
            
            if type == "windowAdded":
                self.window_registry.add_window(w)
            elif type == "windowRemoved":
                self.window_registry.remove_window(w)

            result = event_handler.on_event(type, w, self.window_registry)
            if (len(result) > 0):
                print("ACTION", result)
                print()
            return json.dumps(result)
        except:
            print(traceback.format_exc())
            return "[]"


    async def load_script(self):
        # Script will be deleted on finalize
        self.script = tempfile.NamedTemporaryFile(delete_on_close=False)
        self.script.write(kwin_script.script(WaycoshDaemon.DBUS_ADDRESS, WaycoshDaemon.DBUS_PATH, WaycoshDaemon.DBUS_INTERFACE).encode("UTF-8"))
        self.script.close()

        proxy_object = self.bus.get_proxy_object('org.kde.KWin', '/Scripting', kwin_script.DBUS_SCHEMA_SCRIPTING)
        interface = proxy_object.get_interface('org.kde.kwin.Scripting')
        self.script_id = await interface.call_load_script(self.script.name, kwin_script.SCRIPT_NAME)
        if self.script_id < 0:
            raise Exception("Failed to load script")
        print("Script loaded, id:", self.script_id)
        print()
        
        proxy_object2 = self.bus.get_proxy_object('org.kde.KWin', '/Scripting/Script%d' % self.script_id, kwin_script.DBUS_SCHEMA_SCRIPTING_SCRIPT)
        interface2 = proxy_object2.get_interface('org.kde.kwin.Script')
        await interface2.call_run()


    async def unload_script(self):
        proxy_object2 = self.bus.get_proxy_object('org.kde.KWin', '/Scripting/Script%d' % self.script_id, kwin_script.DBUS_SCHEMA_SCRIPTING_SCRIPT)
        interface2 = proxy_object2.get_interface('org.kde.kwin.Script')
        await interface2.call_stop()
        print("\nScript unloaded")


    def main(self):
        asyncio.run(self.main_loop())
