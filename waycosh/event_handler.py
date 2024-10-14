def on_event(type, window, window_registry):
    if type == "windowAdded":
        group = window.group
        
        # only apply remembered position to the first window of a group
        if group is not None and len(group) == 1:
            geo = group.rememberedFrameGeometry
            if geo is not None:
                return [{"type": "move", "windowId": window.id, "x": geo["x"], "y": geo["y"]}]
    return []
