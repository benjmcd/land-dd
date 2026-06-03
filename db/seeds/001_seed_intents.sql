INSERT INTO core.intents(intent_code, name, description)
VALUES
('rural_land_purchase', 'Rural land purchase', 'Screen a parcel or area before purchase for buildability, access, hazards, water, zoning, and market context.'),
('homestead_feasibility', 'Homestead feasibility', 'Screen whether available evidence suggests a parcel could plausibly support residence, water, septic, access, and basic rural living requirements.')
ON CONFLICT (intent_code) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description;
