import os


def show_schema_graph(path="schema.png"):
    if os.path.exists(path):
        print(f"✅ Schema-Diagramm gespeichert in: {path}")
    else:
        print("❌ Datei nicht gefunden:", path)


def show_uml_graph(path="models_uml.png"):
    if os.path.exists(path):
        print(f"✅ UML-Diagramm gespeichert in: {path}")
    else:
        print("❌ Datei nicht gefunden:", path)