from eralchemy2 import render_er
from database import engine


def create_uml_graph(output_path="models_uml.png"):
    """
    Erzeugt ein UML-Diagramm der SQLAlchemy-Models.
    """
    render_er(engine, output_path)
    return output_path