import requests

# Step 1: Get the list of neighbourhoods for London (Metropolitan Police)
# This will give you specific IDs like '00BK01'
list_url = "https://data.police.uk/api/metropolitan/neighbourhoods"
forces_data = requests.get(list_url).json()

# Grab the first neighbourhood ID as an example
example_id = forces_data[0]['id']  # e.g., "00BK01"

# Step 2: Query the boundary endpoint using that specific ID
boundary_url = f"https://data.police.uk/api/metropolitan/{example_id}/boundary"
boundary_data = requests.get(boundary_url).json()

print(boundary_data[:3])