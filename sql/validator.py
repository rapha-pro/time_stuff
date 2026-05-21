"""
Validation utilities for catalog.
Run this at pipeline startup to catch errors early.
"""

from queries.catalog import QUERIES_CATALOG, validate_catalog, get_execution_phases


def print_execution_plan():
    """Show what will execute and in what order."""
    phases = get_execution_phases()
    
    print("\n" + "="*70)
    print("EXECUTION PLAN")
    print("="*70)
    
    for phase in sorted(phases.keys()):
        queries = phases[phase]
        print(f"\n{phase}:")
        print(f"  ({len(queries)} queries - can run in parallel)")
        for q in queries:
            print(f"    ✓ {q}")


if __name__ == "__main__":
    # Run validation
    validate_catalog()
    print_execution_plan()