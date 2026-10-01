def evaluate_routes(data):

    routes = {}

    flare = data["flare_mmscfd"]
    gas_quality = data["ch4_percent"]
    distance = data["distance_km"]
    power_demand = data["power_demand_mw"]
    road_access = data["road_access"]
    reinjection = data["reinjection_suitable"]
    gas_richness = data["gas_richness"]

    # ----------------
    # CNG
    # ----------------

    cng_score = 50

    if flare >= 1:
        cng_score += 15

    if road_access:
        cng_score += 15

    if distance <= 150:
        cng_score += 10

    if gas_quality >= 85:
        cng_score += 10

    routes["CNG"] = {
        "score": min(cng_score, 100),
        "infrastructure": [
            "Flare Gas KO Drum",
            "Modular Compressor",
            "Gas Conditioning",
            "Metering",
            "CNG Loading Facility"
        ]
    }

    # ----------------
    # LNG
    # ----------------

    lng_score = 40

    if flare >= 5:
        lng_score += 20

    if gas_quality >= 90:
        lng_score += 15

    if distance <= 300:
        lng_score += 10

    routes["LNG"] = {
        "score": min(lng_score, 100),
        "infrastructure": [
            "Gas Pretreatment",
            "Compression",
            "Liquefaction Unit",
            "LNG Storage",
            "Loading System"
        ]
    }

    # ----------------
    # POWER
    # ----------------

    power_score = 35

    if power_demand >= 5:
        power_score += 35

    if flare >= 1:
        power_score += 15

    routes["POWER"] = {
        "score": min(power_score, 100),
        "infrastructure": [
            "Gas Conditioning",
            "Gas Engine/Turbine",
            "Generator",
            "Electrical Distribution"
        ]
    }

    # ----------------
    # LPG / NGL
    # ----------------

    lpg_score = 30

    if gas_richness:
        lpg_score += 40

    if flare >= 3:
        lpg_score += 15

    routes["LPG/NGL"] = {
        "score": min(lpg_score, 100),
        "infrastructure": [
            "Gas Conditioning",
            "NGL Recovery Unit",
            "Fractionation",
            "Storage",
            "Loading"
        ]
    }

    # ----------------
    # REINJECTION
    # ----------------

    reinjection_score = 20

    if reinjection:
        reinjection_score += 60

    if flare >= 2:
        reinjection_score += 10

    routes["REINJECTION"] = {
        "score": min(reinjection_score, 100),
        "infrastructure": [
            "Compression",
            "Injection Manifold",
            "Injection Well",
            "Metering",
            "Pressure Control"
        ]
    }

    return routes