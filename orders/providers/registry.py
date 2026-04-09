# orders/providers/registry.py

# List of all available and planned providers.
# When adding new implementations, list them here first.
AVAILABLE_PROVIDERS = [
    # Currently implemented
    ('vtpass', 'VTPass'),
    ('clubkonnect', 'ClubKonnect'),
    ('arewa_global', 'Arewa Global'),
    ('alrahuz', 'Alrahuz Data'),
    ('smedata', 'SMEDATA.NG'),
    
    # Planned or available for generic configuration
    # ----------------------------------------------
    # ('mobilenig', 'MobileNig'),
    # ('otapay', 'OTAPAY'),
    # ('mightydata', 'MightyData'),
    # ('mobilevtu', 'MobileVTU'),
    # ('aimtoget', 'Aimtoget'),
    # ('nata', 'Nata API'),
    # ('amigo', 'Amigo'),
    # ('vtuorg', 'vtu.org'),
    # ('payflex', 'PayFlex'),
]

def get_provider_display_name(provider_id: str) -> str:
    """Returns the human-readable display name for a provider."""
    return dict(AVAILABLE_PROVIDERS).get(provider_id, provider_id.capitalize())
