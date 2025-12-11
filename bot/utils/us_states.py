"""
US States list with abbreviations.
Used for state filter in PPTP and SOCKS5 proxy selection.
"""
from typing import List, Dict, Any


# All 50 US states in alphabetical order: (full_name, abbreviation)
US_STATES = [
    ("Alabama", "AL"),
    ("Alaska", "AK"),
    ("Arizona", "AZ"),
    ("Arkansas", "AR"),
    ("California", "CA"),
    ("Colorado", "CO"),
    ("Connecticut", "CT"),
    ("Delaware", "DE"),
    ("Florida", "FL"),
    ("Georgia", "GA"),
    ("Hawaii", "HI"),
    ("Idaho", "ID"),
    ("Illinois", "IL"),
    ("Indiana", "IN"),
    ("Iowa", "IA"),
    ("Kansas", "KS"),
    ("Kentucky", "KY"),
    ("Louisiana", "LA"),
    ("Maine", "ME"),
    ("Maryland", "MD"),
    ("Massachusetts", "MA"),
    ("Michigan", "MI"),
    ("Minnesota", "MN"),
    ("Mississippi", "MS"),
    ("Missouri", "MO"),
    ("Montana", "MT"),
    ("Nebraska", "NE"),
    ("Nevada", "NV"),
    ("New Hampshire", "NH"),
    ("New Jersey", "NJ"),
    ("New Mexico", "NM"),
    ("New York", "NY"),
    ("North Carolina", "NC"),
    ("North Dakota", "ND"),
    ("Ohio", "OH"),
    ("Oklahoma", "OK"),
    ("Oregon", "OR"),
    ("Pennsylvania", "PA"),
    ("Rhode Island", "RI"),
    ("South Carolina", "SC"),
    ("South Dakota", "SD"),
    ("Tennessee", "TN"),
    ("Texas", "TX"),
    ("Utah", "UT"),
    ("Vermont", "VT"),
    ("Virginia", "VA"),
    ("Washington", "WA"),
    ("West Virginia", "WV"),
    ("Wisconsin", "WI"),
    ("Wyoming", "WY"),
]


def get_states_with_counts(api_states: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge full US states list with API response containing counts.

    Args:
        api_states: List from API with format [{"state": "CALIFORNIA", "count": 77}, ...]

    Returns:
        List of all 50 states with format [{"state": "California", "abbr": "CA", "count": 77}, ...]
    """
    # Create mapping from state name (lowercase) to count for case-insensitive matching
    counts = {}
    for s in api_states:
        state_name = s.get("state", "")
        count = s.get("count", 0) or s.get("available_count", 0)
        # Use lowercase key for case-insensitive lookup
        counts[state_name.lower()] = count

    result = []
    for name, abbr in US_STATES:
        result.append({
            "state": name,
            "abbr": abbr,
            "count": counts.get(name.lower(), 0)  # Case-insensitive lookup
        })

    return result


def get_state_abbreviation(state_name: str) -> str:
    """Get abbreviation for state name."""
    for name, abbr in US_STATES:
        if name.lower() == state_name.lower():
            return abbr
    return state_name[:2].upper()  # Fallback: first 2 letters


def get_state_name(abbreviation: str) -> str:
    """Get full state name from abbreviation."""
    abbr_upper = abbreviation.upper()
    for name, abbr in US_STATES:
        if abbr == abbr_upper:
            return name
    return abbreviation  # Fallback: return as-is
