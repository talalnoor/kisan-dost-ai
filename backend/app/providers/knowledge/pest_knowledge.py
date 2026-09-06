# Knowledge base for common farm pests. Labels are matched loosely
# (substring match on the normalized model label) since the underlying
# model's exact class names can vary by training run. Any label that
# doesn't match falls through to a clearly-marked generic entry rather
# than silently returning empty guidance.

PEST_KNOWLEDGE = {
    "aphid": {
        "display_name": "Aphids",
        "severity": "moderate",
        "symptoms": ["Clusters of small soft-bodied insects on new growth", "Curled or yellowing leaves", "Sticky honeydew residue, sometimes with black sooty mold"],
        "causes": ["Rapid reproduction in warm weather", "Attracted to nitrogen-rich new growth"],
        "treatment": ["Spray with insecticidal soap or neem oil, covering leaf undersides", "Introduce natural predators like ladybugs where possible"],
        "prevention": ["Avoid excess nitrogen fertilizer", "Monitor new growth weekly during warm months"],
    },
    "armyworm": {
        "display_name": "Armyworm",
        "severity": "severe",
        "symptoms": ["Ragged holes chewed through leaves", "Larvae feeding at night, hiding in soil by day", "Rapid defoliation across a field"],
        "causes": ["Moth eggs laid in large clusters on foliage", "Favored by warm, humid conditions"],
        "treatment": ["Apply a targeted biological or chemical insecticide labeled for armyworm", "Handpick larvae in small plots if infestation is light"],
        "prevention": ["Scout fields regularly during moth flight season", "Remove crop debris where moths lay eggs"],
    },
    "beetle": {
        "display_name": "Beetle damage",
        "severity": "moderate",
        "symptoms": ["Round or irregular holes chewed in leaves", "Skeletonized leaf tissue between veins", "Visible adult beetles on plants"],
        "causes": ["Adult beetles feeding directly on foliage", "Larvae may also feed on roots depending on species"],
        "treatment": ["Handpick beetles where population is low", "Use a labeled insecticide for heavier infestations"],
        "prevention": ["Rotate crops to disrupt beetle life cycles", "Use row covers during peak emergence periods"],
    },
    "grasshopper": {
        "display_name": "Grasshopper",
        "severity": "moderate",
        "symptoms": ["Large, ragged bites out of leaf edges", "Visible grasshoppers on or near plants", "Rapid damage across many plants at once"],
        "causes": ["Migration from nearby dry or fallow land", "Population surges after dry seasons"],
        "treatment": ["Apply a labeled insecticide barrier around field edges", "Use bait treatments for large-scale infestations"],
        "prevention": ["Keep field margins mowed to reduce breeding habitat", "Monitor edges of fields early in the season"],
    },
    "caterpillar": {
        "display_name": "Caterpillar damage",
        "severity": "moderate",
        "symptoms": ["Chewed leaf margins or holes in leaves", "Visible frass (droppings) on foliage", "Silk webbing in some species"],
        "causes": ["Moth or butterfly eggs hatching on host plants"],
        "treatment": ["Handpick caterpillars where feasible", "Apply Bacillus thuringiensis (Bt) or a labeled insecticide"],
        "prevention": ["Inspect leaf undersides regularly for egg clusters", "Encourage natural predators like birds and parasitic wasps"],
    },
    "whitefly": {
        "display_name": "Whitefly",
        "severity": "moderate",
        "symptoms": ["Tiny white flying insects that scatter when disturbed", "Yellowing leaves", "Sticky honeydew and sooty mold"],
        "causes": ["Warm conditions and dense plant canopies favor rapid buildup"],
        "treatment": ["Use yellow sticky traps to monitor and reduce numbers", "Apply insecticidal soap or neem oil to leaf undersides"],
        "prevention": ["Avoid over-fertilizing with nitrogen", "Remove heavily infested leaves promptly"],
    },
    "mite": {
        "display_name": "Spider mites",
        "severity": "moderate",
        "symptoms": ["Fine speckling or stippling on leaves", "Fine webbing on leaf undersides in heavy infestations", "Leaves turning bronze or dry"],
        "causes": ["Hot, dry weather favors rapid mite reproduction"],
        "treatment": ["Spray leaf undersides with water to dislodge mites", "Apply a labeled miticide if infestation is heavy"],
        "prevention": ["Keep plants adequately watered — drought stress worsens infestations", "Avoid excessive dust near plants"],
    },
    "locust": {
        "display_name": "Locust",
        "severity": "severe",
        "symptoms": ["Large swarms stripping fields of foliage rapidly", "Complete defoliation over a short period"],
        "causes": ["Swarm migration, often following population booms elsewhere"],
        "treatment": ["Contact local agricultural authorities immediately — locust swarms typically require coordinated regional response"],
        "prevention": ["Early reporting to extension services when swarms are first sighted"],
    },
}

GENERIC_PEST_ENTRY = {
    "display_name": None,  # filled in dynamically with the raw model label
    "severity": "unknown",
    "symptoms": ["Insect activity detected, but this specific type isn't in our detailed guide yet"],
    "causes": [],
    "treatment": ["Take a closer, well-lit photo if possible and consult your local agricultural extension office to confirm the exact pest before treating"],
    "prevention": ["Monitor the affected area regularly for spread"],
}


def get_pest_knowledge(normalized_label: str, raw_label: str) -> dict:
    for key, entry in PEST_KNOWLEDGE.items():
        if key in normalized_label:
            return entry
    fallback = dict(GENERIC_PEST_ENTRY)
    fallback["display_name"] = raw_label.replace("_", " ").title()
    return fallback