"""
Validation utilities for catalog.
Run this at pipeline startup to catch errors early.
"""

from queries.catalog import QUERIES_CATALOG, validate_catalog, get_execution_phases




def validate_query_names():
    """Verify catalog keys match SQL constant names."""
    import queries.sql_queries as sql_module
    from queries.catalog import QUERIES_CATALOG
    
    errors = []
    
    for key in QUERIES_CATALOG:
        # Derive expected SQL constant name from key
        expected_sql_name = f"QUERY_{key.upper()}"
        
        # Check if it exists in sql_queries
        if not hasattr(sql_module, expected_sql_name):
            errors.append(
                f"Catalog key '{key}' expects SQL constant '{expected_sql_name}' "
                f"but it doesn't exist in sql_queries.py"
            )
    
    if errors:
        print("❌ Naming validation FAILED:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    print("✅ All catalog keys match their SQL constants")
    return True


# Usage:
# validate_query_names()  # Run on startup to catch naming mismatches



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