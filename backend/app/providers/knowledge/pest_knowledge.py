PEST_KNOWLEDGE = {
    "fall_armyworms": {
        "display_name": "Fall Armyworm",
        "severity": "severe",
        "symptoms": ["Ragged holes in leaves, especially whorl of young plants", "Sawdust-like frass near feeding sites"],
        "causes": ["Larval stage of the fall armyworm moth", "Spreads rapidly, especially in maize"],
        "treatment": ["Apply targeted insecticide while larvae are still small", "Handpick larvae on small plots"],
        "prevention": ["Scout fields regularly, especially maize whorls", "Rotate crops", "Encourage natural predators like birds and parasitic wasps"],
    },
    "western_corn_rootworms": {
        "display_name": "Western Corn Rootworm",
        "severity": "severe",
        "symptoms": ["Larvae feed on corn roots causing lodging", "Adult beetles feed on silks and leaves"],
        "causes": ["Beetle larvae in soil feeding on corn root systems"],
        "treatment": ["Apply soil insecticide at planting if infestation is known", "Consider a resistant corn hybrid next season"],
        "prevention": ["Rotate corn with a non-host crop like soybeans", "Monitor beetle counts with sticky traps"],
    },
    "colorado_potato_beetles": {
        "display_name": "Colorado Potato Beetle",
        "severity": "severe",
        "symptoms": ["Defoliated potato/tomato leaves", "Orange-red larvae and yellow-black striped adult beetles visible"],
        "causes": ["Beetle feeds on potato, tomato, and eggplant foliage"],
        "treatment": ["Handpick beetles and larvae on small plots", "Apply targeted insecticide if infestation is heavy"],
        "prevention": ["Rotate crops away from nightshade family", "Mulch with straw to disrupt beetle movement", "Encourage natural predators"],
    },
    "thrips": {
        "display_name": "Thrips",
        "severity": "moderate",
        "symptoms": ["Silvery streaks and stippling on leaves", "Distorted new growth", "Tiny slender insects visible on undersides"],
        "causes": ["Tiny insects that scrape and feed on plant tissue, thrive in warm dry weather"],
        "treatment": ["Apply insecticidal soap or spinosad-based product", "Remove heavily infested leaves"],
        "prevention": ["Use reflective mulch to deter thrips", "Encourage predatory mites and lacewings", "Avoid excess nitrogen fertilizer"],
    },
    "corn_earworms": {
        "display_name": "Corn Earworm",
        "severity": "moderate",
        "symptoms": ["Larvae feeding damage at the tip of corn ears", "Chewed kernels"],
        "causes": ["Moth larvae that bore into corn ear tips"],
        "treatment": ["Apply mineral oil to ear tips at silking as a barrier method", "Targeted insecticide if infestation is heavy"],
        "prevention": ["Plant early to avoid peak moth activity", "Choose resistant corn varieties with tight husks"],
    },
    "cabbage_loopers": {
        "display_name": "Cabbage Looper",
        "severity": "moderate",
        "symptoms": ["Large, ragged holes in leaves", "Green looping caterpillars visible on undersides"],
        "causes": ["Moth larvae feeding on cabbage-family crops"],
        "treatment": ["Apply Bacillus thuringiensis (Bt) spray, effective and low-risk", "Handpick larvae on small plots"],
        "prevention": ["Use row covers to block egg-laying moths", "Encourage parasitic wasps"],
    },
    "armyworms": {
        "display_name": "Armyworm",
        "severity": "severe",
        "symptoms": ["Rapid, widespread defoliation across a field", "Large numbers of caterpillars moving together"],
        "causes": ["Moth larvae that move in large groups, feeding heavily on grasses and grains"],
        "treatment": ["Apply insecticide quickly once detected - infestations spread fast", "Till soil after harvest to disrupt pupae"],
        "prevention": ["Scout fields regularly during warm, humid periods", "Encourage natural predators like birds"],
    },
    "brown_marmorated_stink_bugs": {
        "display_name": "Brown Marmorated Stink Bug",
        "severity": "moderate",
        "symptoms": ["Discolored, dimpled marks on fruit", "Shield-shaped brown insects on plants"],
        "causes": ["Insect feeds by piercing fruit and sucking plant juices"],
        "treatment": ["Apply targeted insecticide during peak activity", "Use pheromone traps to monitor and reduce numbers"],
        "prevention": ["Seal building entry points to reduce overwintering indoors", "Remove nearby weed hosts"],
    },
    "tomato_hornworms": {
        "display_name": "Tomato Hornworm",
        "severity": "moderate",
        "symptoms": ["Large chunks missing from tomato leaves and stems", "Large green caterpillar with a horn-like tail visible"],
        "causes": ["Larval stage of the hawk moth, feeds heavily on tomato foliage"],
        "treatment": ["Handpick hornworms off plants", "Apply Bacillus thuringiensis (Bt) spray if infestation is heavy"],
        "prevention": ["Till soil after harvest to destroy overwintering pupae", "Encourage parasitic wasps (small white cocoons on hornworms are a good sign)"],
    },
    "citrus_canker": {
        "display_name": "Citrus Canker (flagged by pest model - this is a plant disease, not an insect)",
        "severity": "unknown",
        "symptoms": ["This result came from our pest/insect model, but Citrus Canker is actually a bacterial plant disease, not a pest"],
        "causes": [],
        "treatment": ["For an actual disease diagnosis, please use the Disease scan instead of Pest scan", "If citrus canker is suspected, consult your local agricultural extension office"],
        "prevention": ["Use the Disease tab for suspected plant diseases; use Pest tab for insects specifically"],
    },
    "aphids": {
        "display_name": "Aphids",
        "severity": "mild",
        "symptoms": ["Curled, yellowing leaves", "Sticky honeydew residue", "Clusters of tiny insects on new growth"],
        "causes": ["Small sap-sucking insects that reproduce rapidly in warm weather"],
        "treatment": ["Spray with insecticidal soap or a strong water jet to dislodge them", "Introduce ladybugs as a natural predator"],
        "prevention": ["Avoid excess nitrogen fertilizer", "Encourage natural predators", "Monitor new growth regularly"],
    },
    "corn_borers": {
        "display_name": "Corn Borer",
        "severity": "moderate",
        "symptoms": ["Small holes in leaves and stalks", "Broken tassels or stalks", "Sawdust-like frass at entry holes"],
        "causes": ["Moth larvae that tunnel into corn stalks and ears"],
        "treatment": ["Apply targeted insecticide at early larval stage before boring begins", "Remove and destroy old stalks after harvest"],
        "prevention": ["Rotate crops", "Choose resistant corn hybrids", "Till field after harvest to destroy overwintering larvae"],
    },
    "fruit_flies": {
        "display_name": "Fruit Fly",
        "severity": "mild",
        "symptoms": ["Small punctures on ripening fruit", "Fruit rot and premature dropping", "Tiny flies hovering around fruit"],
        "causes": ["Flies lay eggs in ripening or damaged fruit"],
        "treatment": ["Use fruit fly traps with bait", "Remove and destroy fallen or overripe fruit promptly"],
        "prevention": ["Harvest fruit promptly when ripe", "Keep the area free of rotting fruit debris"],
    },
    "africanized_honey_bees_killer_bees": {
        "display_name": "Africanized Honey Bee",
        "severity": "unknown",
        "symptoms": ["Defensive, aggressive swarming behavior near hives", "Not typically a crop-damaging pest"],
        "causes": ["A more defensive honey bee subspecies, important pollinators despite the nickname"],
        "treatment": ["Do not attempt removal yourself - contact a professional beekeeper or pest control service", "Keep distance from hives, avoid provoking them"],
        "prevention": ["Inspect property regularly for hive establishment in eaves or hollow spaces", "Seal potential nesting cavities"],
    },
    "spider_mites": {
        "display_name": "Spider Mites",
        "severity": "moderate",
        "symptoms": ["Fine yellow stippling on leaves", "Fine webbing on leaf undersides in heavy infestations"],
        "causes": ["Tiny arachnid pests, thrive in hot, dry conditions"],
        "treatment": ["Apply insecticidal soap or miticide", "Spray leaf undersides with water to dislodge mites"],
        "prevention": ["Avoid drought stress", "Encourage natural predators like ladybugs", "Monitor regularly during hot weather"],
    },
}


def get_pest_knowledge(detected_label: str, raw_label: str = None) -> dict:
    if detected_label in PEST_KNOWLEDGE:
        return PEST_KNOWLEDGE[detected_label]

    display = raw_label or detected_label

    display = raw_label or detected_label
    return {
        "display_name": display,
        "severity": "unknown",
        "symptoms": ["Insect activity detected, but this specific type is not in our detailed guide yet"],
        "causes": [],
        "treatment": ["Take a closer, well-lit photo if possible and consult your local agricultural extension office to confirm the exact pest before treating"],
        "prevention": ["Monitor the affected area regularly for spread"],
    }
