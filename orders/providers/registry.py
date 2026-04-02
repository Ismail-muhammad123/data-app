# orders/providers/registry.py

# List of all available and planned providers.
# When adding new implementations, list them here first.
AVAILABLE_PROVIDERS = [
    # Currently implemented
    ('vtpass', 'VTPass'),
    ('clubkonnect', 'ClubKonnect'),
    
    # Planned or available for generic configuration
    ('alrahuz', 'Alrahuz Data'),
    ('mobilenig', 'MobileNig'),
    ('otapay', 'OTAPAY'),
    ('arewa_global', 'Arewa Global'),
    ('mightydata', 'MightyData'),
    ('smedata', 'SMEDATA.NG'),
    ('mobilevtu', 'MobileVTU'),
    ('aimtoget', 'Aimtoget'),
    ('nata', 'Nata API'),
    ('amigo', 'Amigo'),
    ('vtuorg', 'vtu.org'),
    ('payflex', 'PayFlex'),
]

def get_provider_display_name(provider_id: str) -> str:
    """Returns the human-readable display name for a provider."""
    return dict(AVAILABLE_PROVIDERS).get(provider_id, provider_id.capitalize())
