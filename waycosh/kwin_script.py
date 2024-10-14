SCRIPT = r"""
function actionCallback(actionStr) {
    print("Waycosh actionCallback:", actionStr);
    let actionList = JSON.parse(actionStr);
    let windowList = workspace.windowList();
    for (var i=0; i<actionList.length; i++) {
        let action = actionList[i];
        let windowId = action.windowId;
        var window = null;
        for (var j=0; j<windowList.length; j++) {
            if (windowList[j].internalId == windowId) {
                window = windowList[j];
                break
            }
        }

        if (window == null) {
            print("Window not found:", windowId);
            continue;
        }

        let actionType = action.type;
        if (actionType == "move") {
            var g = window.frameGeometry;
            print("move", g);
            g.x = action.x;
            g.y = action.y;
            print("to", g);
            window.frameGeometry = g;
        }
    }
}

function event(type, data) {
    callDBus("{{{DBUS_ADDRESS}}}",
        "{{{DBUS_PATH}}}",
        "{{{DBUS_INTERFACE}}}",
        "Event",
        type,
        data,
        actionCallback);
}

function windowInfo(w) {
    return JSON.stringify({
        id: w.internalId,
        pid: w.pid,
        caption: w.caption,
        resourceName: w.resourceName,
        resourceClass: w.resourceClass,
        windowRole: w.windowRole,
        transient: w.transient,
        frameGeometry: {x: w.frameGeometry.x, y: w.frameGeometry.y, width: w.frameGeometry.width, height: w.frameGeometry.height},
        fullscreen: w.fullScreen,
    });
}

function windowAdded(w) {
    if (w.normalWindow && w.moveable && !w.skipSwitcher)
        event("windowAdded", windowInfo(w));    
}

function windowRemoved(w) {
    if (w.normalWindow && w.moveable && !w.skipSwitcher)
        event("windowRemoved", windowInfo(w));    
}

workspace.windowAdded.connect(windowAdded);
workspace.windowRemoved.connect(windowRemoved);

let windowList = workspace.windowList();
for (var i=0; i<windowList.length; i++) {
    windowAdded(windowList[i]);
}
"""

DBUS_SCHEMA_SCRIPTING = r"""
    <!DOCTYPE node PUBLIC "-//freedesktop//DTD D-BUS Object Introspection 1.0//EN"
    "http://www.freedesktop.org/standards/dbus/1.0/introspect.dtd">
    <node>
        <interface name="org.kde.kwin.Scripting">
            <method name="loadScript">
                <arg name="filePath" direction="in" type="s" />
                <arg name="pluginName" direction="in" type="s" />
                <arg direction="out" type="i" />
            </method>
        </interface>
    </node>
"""

DBUS_SCHEMA_SCRIPTING_SCRIPT = r"""
    <!DOCTYPE node PUBLIC "-//freedesktop//DTD D-BUS Object Introspection 1.0//EN"
    "http://www.freedesktop.org/standards/dbus/1.0/introspect.dtd">
    <node>
        <interface name="org.kde.kwin.Script">
            <method name="stop"/>
            <method name="run"/>
        </interface>                
    </node>
"""

SCRIPT_NAME = "waycosh"

def script(dbus_address, dbus_path, dbus_interface):
    return SCRIPT.replace("{{{DBUS_ADDRESS}}}", dbus_address) \
        .replace("{{{DBUS_PATH}}}", dbus_path) \
        .replace("{{{DBUS_INTERFACE}}}", dbus_interface)
