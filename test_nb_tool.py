import nb_tool

nb_tool.NOTEBOOKS = {"blog": ("id-1", "Our blog"), "team_meetings": ("id-2", "Team meetings")}
assert nb_tool.notebook("Team Meetings")[1] == "Team meetings"
assert nb_tool.notebook("blog")[0] == "id-1"
for bad in ("HR", "", "id-1"):
    try:
        nb_tool.notebook(bad)
        raise SystemExit(f"allowlist let {bad!r} through")
    except ValueError:
        pass
assert nb_tool.load_notebooks("notebooks.example.json")["blog"][1] == "Our blog"
assert nb_tool.for_speech("It is **a tool** [1, 2] for audio [3-5].\n\n---\nWould you like more?") \
    == "It is a tool for audio."
assert nb_tool.for_speech("The meeting covered AI.\n\n\u26fa Would you like a deeper breakdown?") == "The meeting covered AI."
print("ok")
