from sqlalchemy_schemadisplay import create_schema_graph
from sqlalchemy import MetaData
from database import engine


def create_schema_graph_png(output_path="schema.png"):
    """
    Erzeugt ein PNG-Diagramm aller Tabellen aus SQLAlchemy-Mapping.
    """
    metadata = MetaData()
    metadata.reflect(bind=engine)

    graph = create_schema_graph(
        metadata=metadata,
        show_datatypes=True,
        show_indexes=True,
        rankdir="LR",
    )

    graph.write_png(output_path)
    return output_path