#!/usr/bin/env python3
"""
Test script to demonstrate the UUID comparison issue.
"""

import uuid

# Simulate the issue
sport_id_string = "c4476633-3ee4-40c5-9c06-a719751175cb"
sport_id_uuid = uuid.UUID("c4476633-3ee4-40c5-9c06-a719751175cb")

print(f"String ID: {sport_id_string} (type: {type(sport_id_string)})")
print(f"UUID ID: {sport_id_uuid} (type: {type(sport_id_uuid)})")
print(f"Are they equal? {sport_id_string == sport_id_uuid}")
print(f"String representation equal? {str(sport_id_uuid) == sport_id_string}")

# Demonstrate the set comparison issue
string_ids = {sport_id_string}
uuid_ids = {sport_id_uuid}

print(f"\nSet difference (strings - uuids): {string_ids - uuid_ids}")
print(f"Set difference (uuids - strings): {uuid_ids - string_ids}")

# Show the correct way to compare
string_ids_converted = {str(uuid_id) for uuid_id in uuid_ids}
print(f"\nConverted UUID to string: {string_ids_converted}")
print(f"Set difference after conversion: {string_ids - string_ids_converted}")
