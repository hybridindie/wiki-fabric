"""GDScript language pack for graphify.

Registers a tree-sitter GDScript LanguageConfig into graphify's dispatch
so .gd files extract real callables (func/class/signal) instead of the
sparse generic path (aperiodic: 5 callable nodes across 767 without it).

Imported by graphify-bridge.py when tree_sitter_gdscript is installed:
    uv pip install tree-sitter-gdscript
"""
import graphify.extract as gx

_CONFIG = gx.LanguageConfig(
    ts_module="tree_sitter_gdscript",
    class_types=frozenset({"class_definition"}),
    function_types=frozenset({"function_definition"}),
    import_types=frozenset({"extends_statement"}),
    call_types=frozenset({"call"}),
    call_function_field="function",
)

def extract_gdscript(path):
    return gx._extract_generic(path, _CONFIG)

def install():
    gx._DISPATCH[".gd"] = extract_gdscript
    gx._LANG_FAMILY_BY_EXT[".gd"] = "gdscript"
