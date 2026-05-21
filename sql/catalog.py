"""
Query catalog with metadata.
This is WHERE YOU ADD NEW QUERIES.

To add a new query:
1. Add the SQL string to sql_queries.py
2. Add an entry to QUERIES_CATALOG below
3. Run validate_catalog() to verify

That's it! No other changes needed.
"""

from enum import Enum
from typing import List, Dict
from queries.sql_queries import (
    QUERY_STICKER_OFFERED,
    QUERY_CUSTOMER_TRANSACTIONS,
    QUERY_CUSTOMER_SEGMENTS,
    # ... import all your queries here
)


class ParamType(Enum):
    START_DATE = "start_date"
    END_DATE = "end_date"
    WRITE_OFF_WINDOW = "write_off_window"


# ===== ONE PLACE TO ADD QUERIES =====

QUERIES_CATALOG: Dict[str, Dict] = {
    # ===== PHASE 1: Independent Queries =====
    # These have no dependencies and can run in parallel
    
    "sticker_offered": {
        "sql": QUERY_STICKER_OFFERED,
        "params": [ParamType.START_DATE, ParamType.END_DATE],
        "dependencies": [],
        "description": "Customers offered stickers, comeback rates",
        "owner": "analytics-team",  # Optional: for code review routing
        "added_date": "2025-11-01",
        "tags": ["core_metric", "sticker_analysis"],
    },
    
    "customer_transactions": {
        "sql": QUERY_CUSTOMER_TRANSACTIONS,
        "params": [ParamType.START_DATE, ParamType.END_DATE],
        "dependencies": [],
        "description": "Transaction summary per customer",
        "owner": "analytics-team",
        "added_date": "2025-11-01",
        "tags": ["base_metric"],
    },
    
    "write_off_summary": {
        "sql": QUERY_WRITE_OFF_SUMMARY,
        "params": [ParamType.WRITE_OFF_WINDOW],
        "dependencies": [],
        "description": "Write-off summary for last N months",
        "owner": "finance-team",
        "added_date": "2025-11-15",
        "tags": ["financial"],
    },
    
    # ===== PHASE 2: First-Level Dependencies =====
    # These depend on phase 1 queries
    
    "customer_segments": {
        "sql": QUERY_CUSTOMER_SEGMENTS,
        "params": [],
        "dependencies": ["customer_transactions", "write_off_summary", "churn_risk"],
        "description": "Segment customers (LOYAL/AT_RISK/NEW/REGULAR)",
        "owner": "analytics-team",
        "added_date": "2025-11-20",
        "tags": ["segmentation", "downstream"],
    },
    
    # To add a new query:
    # 1. Add SQL to sql_queries.py
    # 2. Import it above
    # 3. Add entry here
    # 4. Call validate_catalog()
    #
    # Example:
    # "my_new_query": {
    #     "sql": QUERY_MY_NEW_QUERY,
    #     "params": [ParamType.START_DATE],
    #     "dependencies": ["some_other_query"],
    #     "description": "What does this query do?",
    #     "owner": "your-team",
    #     "added_date": "2025-12-01",
    #     "tags": ["relevant_tag"],
    # },
}


# ===== UTILITY FUNCTIONS =====

def validate_catalog() -> bool:
    """
    Validate the catalog for errors:
    - Missing SQL references
    - Circular dependencies
    - Missing dependencies
    """
    errors = []
    
    # Check all dependencies exist
    for query_name, config in QUERIES_CATALOG.items():
        for dep in config["dependencies"]:
            if dep not in QUERIES_CATALOG:
                errors.append(
                    f"Query '{query_name}' depends on '{dep}' "
                    f"which is not in QUERIES_CATALOG"
                )
    
    # Check for circular dependencies
    for query_name in QUERIES_CATALOG:
        if _has_circular_dep(query_name, set()):
            errors.append(f"Circular dependency in '{query_name}'")
    
    if errors:
        print("❌ Catalog validation FAILED:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    print("✅ Catalog validation PASSED")
    return True


def _has_circular_dep(query_name: str, visited: set) -> bool:
    if query_name in visited:
        return True
    
    visited.add(query_name)
    
    for dep in QUERIES_CATALOG[query_name]["dependencies"]:
        if _has_circular_dep(dep, visited.copy()):
            return True
    
    return False


def get_execution_phases() -> Dict[str, List[str]]:
    """Return queries grouped by execution phase."""
    phases = {}
    
    for query_name, config in QUERIES_CATALOG.items():
        depth = _get_dependency_depth(query_name)
        phase_key = f"phase_{depth}"
        
        if phase_key not in phases:
            phases[phase_key] = []
        
        phases[phase_key].append(query_name)
    
    return phases


def _get_dependency_depth(query_name: str) -> int:
    """How deep in the dependency chain?"""
    deps = QUERIES_CATALOG[query_name]["dependencies"]
    if not deps:
        return 1
    
    return 1 + max([_get_dependency_depth(dep) for dep in deps], default=0)


def get_query_lineage(query_name: str) -> Dict:
    """Show what queries depend on this one (reverse dependencies)."""
    dependents = []
    
    for name, config in QUERIES_CATALOG.items():
        if query_name in config["dependencies"]:
            dependents.append(name)
    
    return {
        "query": query_name,
        "dependencies": QUERIES_CATALOG[query_name]["dependencies"],
        "dependents": dependents,
    }


def print_catalog_summary():
    """Pretty-print the catalog for documentation."""
    phases = get_execution_phases()
    
    print("\n" + "="*70)
    print("QUERY CATALOG SUMMARY")
    print("="*70)
    
    for phase_key in sorted(phases.keys()):
        print(f"\n{phase_key.upper()}:")
        for query_name in phases[phase_key]:
            config = QUERIES_CATALOG[query_name]
            print(f"  - {query_name}")
            print(f"    Description: {config['description']}")
            print(f"    Params: {[p.value for p in config['params']]}")
            if config["dependencies"]:
                print(f"    Depends on: {config['dependencies']}")