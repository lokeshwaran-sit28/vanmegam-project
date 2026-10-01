# System Design

## Architecture Overview

```
CLI (cli.py)
    |
    |-- topology.py          Parse coordinates, build communication graph G
    |-- conflict_graph.py    Build distance-2 conflict graph C
    |-- coloring.py          DSATUR heuristic coloring
    |-- optimizer.py         Optional local-improvement pass
    |-- coloring.py          normalize_colors()
    |-- matrix.py            Build binary schedule matrix
    |-- validator.py         Independent conflict checker
    |-- reporting.py         Text / JSON output
    |
    models.py                Shared dataclasses (no logic)
```

## Data Flow

1. User provides `--file` or `--coordinates` JSON.  
2. `topology.parse_coordinates` validates and produces `List[NodeCoordinate]`.  
3. `topology.build_communication_graph` builds NetworkX graph G.  
4. `conflict_graph.build_distance_two_conflict_graph` builds C.  
5. `coloring.dsatur_coloring` produces initial node→slot mapping.  
6. `coloring.normalize_colors` compacts slot numbers.  
7. *(optional)* `optimizer.improve_coloring` reduces slot count further.  
8. `matrix.build_schedule_matrix` produces the binary matrix.  
9. `validator.validate_schedule` checks every conflict edge.  
10. `reporting.generate_text_report` / `generate_json_report` prints output.  

## Module Boundaries

| Module | Depends on | Does NOT depend on |
|--------|-----------|-------------------|
| models.py | nothing | everything else |
| topology.py | models | NetworkX |
| conflict_graph.py | NetworkX | topology, coloring |
| coloring.py | nothing except types | NetworkX |
| optimizer.py | coloring | NetworkX |
| matrix.py | nothing | everything |
| validator.py | models | coloring |
| reporting.py | models | algorithms |
| cli.py | all of the above | — |

## Design Decisions

### Why dataclasses in models.py?
Single source of truth for the shared data contract.  Downstream
modules receive typed objects, not raw dicts.  Easy to extend.

### Why is the validator independent?
If the validator called the same code path as the colorer, a bug in
the coloring logic could produce an incorrect schedule that the
validator also incorrectly marks as valid.  Independence is critical.

### Why NetworkX for graph operations?
BFS, shortest-path, and adjacency queries are already optimised in
NetworkX.  Re-implementing them would add code without value.

### Why argparse instead of click/typer?
Zero extra dependency.  The CLI is simple enough that argparse is
clear and sufficient.  Keeps `requirements.txt` minimal.
