"""
Minimal floating panel with a search box and clear button.
Filters Read nodes by name or filename and selects the first match.
"""
import os, re, nuke, nukescripts

class ShotFinderPanel(nukescripts.PythonPanel):
    def __init__(self):
        super(ShotFinderPanel, self).__init__("Find Shot in Lineup")
        self.search_knob = nuke.String_Knob("search", "Shot Name:")
        self.addKnob(self.search_knob)
        self.clear_btn = nuke.PyScript_Knob("clear", "Clear")
        self.addKnob(self.clear_btn)
        self.all_reads = list(nuke.allNodes("Read"))

    def knobChanged(self, knob):
        if knob is self.search_knob:
            keyword = self.search_knob.value().strip()
            self._filter_and_select(keyword)
        elif knob is self.clear_btn:
            self.search_knob.setValue("")
            self._clear_selection()

    def _filter_and_select(self, keyword: str):
        if not keyword:
            self._clear_selection()
            return
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        found = False
        for node in self.all_reads:
            try:
                name = node.name()
                path = node["file"].value()
                filename = os.path.basename(path)
                match = pattern.search(name) or pattern.search(filename)
                node.setSelected(bool(match))
                if match and not found:
                    found = True
                    nuke.zoomToFitSelected()
            except Exception:
                continue
        if not found:
            nuke.message(f"No Read nodes found for: {keyword}")

    def _clear_selection(self):
        for node in self.all_reads:
            node.setSelected(False)

    def showModal(self):
        try:
            self.show()
        except Exception as e:
            nuke.message(f"Error displaying panel: {e}")

def launch():
    try:
        ShotFinderPanel().showModal()
    except Exception as e:
        nuke.message(str(e))
