import json
from pathlib import Path


class Window:

    @staticmethod
    def from_json(data):
        d = json.loads(data)
        w = Window()
        for k, v in d.items():
            setattr(w, k, v)
        return w


    def __init__(self):
        self.group = None
        self.cmdline = None
        self.exe = None
        self.cgroup = None
        self.comm = None


class WindowGroup(dict):

    def __init__(self):
        super().__init__()
        self.rememberedFrameGeometry = None


class WindowRegistry(dict):
    STATE_PATH = Path("~/.local/share/waycosh/state.json").expanduser()


    def __init__(self):
        super().__init__()
        self.groups = {}
        self.dirty = False


    def add_window(self, window):
        assert window.id not in self
        self[window.id] = window
        self.add_aux_info(window)
        self.group_window(window)


    def remove_window(self, window):
        assert window.id in self
        window.group = self[window.id].group
        del self[window.id]

        self.ungroup_window(window)


    def add_aux_info(self, window):
        pid = window.pid
        if pid is None:
            return
        
        proc = Path(f"/proc/{pid}")
        if not proc.exists():
            return
        
        window.cmdline = (proc / "cmdline").read_text()
        window.exe = str((proc / "exe").resolve())
        window.cgroup = (proc / "cgroup").read_text()
        window.comm = (proc / "comm").read_text()


    def group_window(self, window):
        if window.exe is None:
            return
        
        self.groups.setdefault(window.exe, WindowGroup())[window.id] = window
        window.group = self.groups[window.exe]


    def ungroup_window(self, window):
        if window.group is None:
            return

        window.group.pop(window.id)

        # remember the position of the last closed window in group
        if len(window.group) == 0:
            window.group.rememberedFrameGeometry = window.frameGeometry
            self.dirty = True


    def save_state(self):
        if not self.dirty:
            return False
        
        WindowRegistry.STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        state = dict((group_id, group.rememberedFrameGeometry) for group_id, group in self.groups.items() if group.rememberedFrameGeometry is not None)
        WindowRegistry.STATE_PATH.write_text(json.dumps(state))
        self.dirty = False

        print("State saved\n");

        return True
    

    def load_state(self):
        if not WindowRegistry.STATE_PATH.exists():
            return
        
        try:
            state = json.loads(WindowRegistry.STATE_PATH.read_text())
        except:
            raise "Broken state file at %s" % WindowRegistry.STATE_PATH
        
        self.groups.clear()
        for group_id, rememberedFrameGeometry in state.items():
            self.groups.setdefault(group_id, WindowGroup()).rememberedFrameGeometry = rememberedFrameGeometry
        print("State loaded\n");
