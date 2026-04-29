# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# airports.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Airport database with coordinates for US, Canada, and Europe."""

# Airport database with ICAO codes and coordinates
# Format: ICAO -> (name, lat, lon, elevation_ft)
AIRPORTS = {
    # ============================================
    # UNITED STATES
    # ============================================
    # California
    "KCRQ": ("McClellan-Palomar Airport", 33.1283, -117.2803, 331),
    "KSAN": ("San Diego International", 32.7336, -117.1897, 17),
    "KLAX": ("Los Angeles International", 33.9425, -118.4081, 128),
    "KSFO": ("San Francisco International", 37.6213, -122.3790, 13),
    "KOAK": ("Oakland International", 37.7213, -122.2208, 9),
    "KSJC": ("San Jose International", 37.3626, -121.9291, 62),
    "KBUR": ("Hollywood Burbank", 34.2007, -118.3585, 778),
    "KSNA": ("John Wayne Orange County", 33.6757, -117.8682, 56),
    "KONT": ("Ontario International", 34.0560, -117.6012, 944),
    "KPSP": ("Palm Springs International", 33.8303, -116.5067, 477),
    "KSMF": ("Sacramento International", 38.6954, -121.5908, 27),
    "KFAT": ("Fresno Yosemite International", 36.7762, -119.7181, 336),
    "KMRY": ("Monterey Regional", 36.5870, -121.8430, 257),
    "KSTS": ("Charles M. Schulz Sonoma County", 38.5090, -122.8128, 128),
    "KSBP": ("San Luis Obispo County Regional", 35.2368, -120.6424, 212),
    "KRNM": ("Ramona Airport", 33.0392, -116.9153, 1395),
    "KSEE": ("Gillespie Field", 32.8262, -116.9724, 388),
    "KRNC": ("Riverside Municipal", 33.9519, -117.4451, 816),
    # Arizona
    "KPHX": ("Phoenix Sky Harbor", 33.4373, -112.0078, 1135),
    "KTUS": ("Tucson International", 32.1161, -110.9410, 2643),
    "KSDL": ("Scottsdale Airport", 33.6229, -111.9105, 1510),
    "KFLG": ("Flagstaff Pulliam", 35.1385, -111.6712, 7014),
    "KGYR": ("Phoenix Goodyear", 33.4225, -112.3761, 968),
    "KIWA": ("Phoenix-Mesa Gateway", 33.3078, -111.6556, 1382),
    # Nevada
    "KLAS": ("Harry Reid International", 36.0840, -115.1537, 2181),
    "KRNO": ("Reno-Tahoe International", 39.4991, -119.7681, 4415),
    "KHND": ("Henderson Executive", 35.9728, -115.1344, 2492),
    # Texas
    "KDFW": ("Dallas/Fort Worth International", 32.8998, -97.0403, 607),
    "KIAH": ("George Bush Intercontinental", 29.9902, -95.3368, 97),
    "KHOU": ("William P. Hobby", 29.6454, -95.2789, 46),
    "KAUS": ("Austin-Bergstrom International", 30.1975, -97.6664, 542),
    "KSAT": ("San Antonio International", 29.5337, -98.4698, 809),
    "KELP": ("El Paso International", 31.8072, -106.3778, 3959),
    "KDAL": ("Dallas Love Field", 32.8471, -96.8518, 487),
    "KMAF": ("Midland International", 31.9425, -102.2019, 2871),
    "KLBB": ("Lubbock Preston Smith", 33.6636, -101.8227, 3282),
    "KCRP": ("Corpus Christi International", 27.7704, -97.5012, 44),
    "KAMA": ("Rick Husband Amarillo", 35.2194, -101.7059, 3607),
    # Florida
    "KMIA": ("Miami International", 25.7959, -80.2870, 8),
    "KFLL": ("Fort Lauderdale-Hollywood", 26.0726, -80.1527, 9),
    "KMCO": ("Orlando International", 28.4294, -81.3090, 96),
    "KTPA": ("Tampa International", 27.9755, -82.5332, 26),
    "KJAX": ("Jacksonville International", 30.4941, -81.6879, 30),
    "KPBI": ("Palm Beach International", 26.6832, -80.0956, 19),
    "KRSW": ("Southwest Florida International", 26.5362, -81.7552, 30),
    "KSFB": ("Orlando Sanford International", 28.7776, -81.2375, 55),
    "KPNS": ("Pensacola International", 30.4734, -87.1866, 121),
    "KEYW": ("Key West International", 24.5561, -81.7596, 3),
    "KFMY": ("Page Field", 26.5866, -81.8633, 17),
    # New York
    "KJFK": ("John F. Kennedy International", 40.6413, -73.7781, 13),
    "KLGA": ("LaGuardia", 40.7769, -73.8740, 21),
    "KEWR": ("Newark Liberty International", 40.6895, -74.1745, 18),
    "KISP": ("Long Island MacArthur", 40.7952, -73.1002, 99),
    "KBUF": ("Buffalo Niagara International", 42.9405, -78.7322, 728),
    "KSYR": ("Syracuse Hancock International", 43.1112, -76.1063, 421),
    "KROC": ("Greater Rochester International", 43.1189, -77.6724, 559),
    "KSWF": ("New York Stewart International", 41.5041, -74.1048, 491),
    # Illinois
    "KORD": ("O'Hare International", 41.9742, -87.9073, 672),
    "KMDW": ("Chicago Midway", 41.7868, -87.7522, 620),
    "KRFD": ("Chicago Rockford International", 42.1954, -89.0972, 742),
    # Georgia
    "KATL": ("Hartsfield-Jackson Atlanta", 33.6407, -84.4277, 1026),
    "KSAV": ("Savannah/Hilton Head", 32.1276, -81.2021, 50),
    "KAGS": ("Augusta Regional", 33.3699, -81.9645, 144),
    # Colorado
    "KDEN": ("Denver International", 39.8561, -104.6737, 5434),
    "KCOS": ("Colorado Springs", 38.8058, -104.7008, 6187),
    "KASE": ("Aspen-Pitkin County", 39.2232, -106.8688, 7820),
    "KEGE": ("Eagle County Regional", 39.6426, -106.9177, 6548),
    "KGJT": ("Grand Junction Regional", 39.1224, -108.5267, 4858),
    # Washington
    "KSEA": ("Seattle-Tacoma International", 47.4502, -122.3088, 433),
    "KGEG": ("Spokane International", 47.6199, -117.5338, 2376),
    "KPAE": ("Paine Field", 47.9063, -122.2815, 606),
    "KBFI": ("Boeing Field King County", 47.5300, -122.3019, 21),
    # Oregon
    "KPDX": ("Portland International", 45.5898, -122.5951, 31),
    "KEUG": ("Eugene Airport", 44.1246, -123.2190, 374),
    "KMFR": ("Rogue Valley International", 42.3742, -122.8735, 1335),
    # Massachusetts
    "KBOS": ("Boston Logan International", 42.3656, -71.0096, 20),
    "KBED": ("Laurence G. Hanscom Field", 42.4700, -71.2890, 133),
    "KORH": ("Worcester Regional", 42.2673, -71.8757, 1009),
    # Pennsylvania
    "KPHL": ("Philadelphia International", 39.8744, -75.2424, 36),
    "KPIT": ("Pittsburgh International", 40.4915, -80.2329, 1203),
    "KMDT": ("Harrisburg International", 40.1935, -76.7634, 310),
    "KABE": ("Lehigh Valley International", 40.6521, -75.4408, 393),
    # Michigan
    "KDTW": ("Detroit Metropolitan", 42.2124, -83.3534, 645),
    "KGRR": ("Gerald R. Ford International", 42.8808, -85.5228, 794),
    "KFNT": ("Bishop International", 42.9655, -83.7436, 782),
    "KLAN": ("Capital Region International", 42.7787, -84.5874, 861),
    # Minnesota
    "KMSP": ("Minneapolis-Saint Paul", 44.8820, -93.2218, 841),
    "KDLH": ("Duluth International", 46.8420, -92.1936, 1428),
    "KRST": ("Rochester International", 43.9083, -92.5000, 1317),
    # Missouri
    "KSTL": ("St. Louis Lambert", 38.7487, -90.3700, 618),
    "KMCI": ("Kansas City International", 39.2976, -94.7139, 1026),
    "KSGF": ("Springfield-Branson National", 37.2457, -93.3886, 1268),
    # North Carolina
    "KCLT": ("Charlotte Douglas International", 35.2140, -80.9431, 748),
    "KRDU": ("Raleigh-Durham International", 35.8776, -78.7875, 435),
    "KGSO": ("Piedmont Triad International", 36.0978, -79.9373, 925),
    "KAVL": ("Asheville Regional", 35.4362, -82.5418, 2165),
    # Tennessee
    "KBNA": ("Nashville International", 36.1263, -86.6774, 599),
    "KMEM": ("Memphis International", 35.0424, -89.9767, 341),
    "KTYS": ("McGhee Tyson", 35.8110, -83.9940, 981),
    # Ohio
    "KCLE": ("Cleveland Hopkins International", 41.4117, -81.8498, 791),
    "KCMH": ("John Glenn Columbus", 39.9980, -82.8919, 815),
    "KDAY": ("James M. Cox Dayton", 39.9024, -84.2194, 1009),
    "KCAK": ("Akron-Canton", 40.9161, -81.4422, 1228),
    # Louisiana
    "KMSY": ("Louis Armstrong New Orleans", 29.9934, -90.2580, 4),
    "KBTR": ("Baton Rouge Metropolitan", 30.5332, -91.1496, 70),
    "KSHV": ("Shreveport Regional", 32.4466, -93.8256, 258),
    # Utah
    "KSLC": ("Salt Lake City International", 40.7884, -111.9778, 4227),
    "KPVU": ("Provo Municipal", 40.2192, -111.7235, 4497),
    # Hawaii
    "PHNL": ("Daniel K. Inouye International", 21.3187, -157.9225, 13),
    "PHOG": ("Kahului Airport", 20.8986, -156.4305, 54),
    "PHKO": ("Ellison Onizuka Kona", 19.7388, -156.0456, 47),
    "PHLI": ("Lihue Airport", 21.9760, -159.3389, 153),
    "PHTO": ("Hilo International", 19.7214, -155.0485, 38),
    # Alaska
    "PANC": ("Ted Stevens Anchorage", 61.1743, -149.9962, 152),
    "PAFA": ("Fairbanks International", 64.8151, -147.8561, 439),
    "PAJN": ("Juneau International", 58.3547, -134.5762, 21),
    "PAKN": ("King Salmon Airport", 58.6768, -156.6492, 73),
    # Other US airports
    "KBWI": ("Baltimore/Washington", 39.1754, -76.6683, 146),
    "KIAD": ("Washington Dulles", 38.9531, -77.4565, 313),
    "KDCA": ("Ronald Reagan Washington", 38.8512, -77.0402, 15),
    "KPVD": ("T.F. Green Providence", 41.7267, -71.4282, 55),
    "KBDL": ("Bradley International", 41.9389, -72.6832, 173),
    "KALB": ("Albany International", 42.7483, -73.8017, 285),
    "KIND": ("Indianapolis International", 39.7173, -86.2944, 797),
    "KCVG": ("Cincinnati/Northern Kentucky", 39.0488, -84.6678, 896),
    "KMKE": ("Milwaukee Mitchell", 42.9472, -87.8966, 723),
    "KOMA": ("Eppley Airfield", 41.3032, -95.8941, 984),
    "KOKC": ("Will Rogers World", 35.3931, -97.6007, 1295),
    "KTUL": ("Tulsa International", 36.1984, -95.8881, 677),
    "KABQ": ("Albuquerque International", 35.0402, -106.6094, 5355),
    "KDSM": ("Des Moines International", 41.5340, -93.6631, 958),
    "KICT": ("Wichita Eisenhower National", 37.6499, -97.4331, 1333),
    "KLIT": ("Bill and Hillary Clinton National", 34.7294, -92.2243, 262),
    "KJAN": ("Jackson-Medgar Wiley Evers", 32.3112, -90.0759, 346),
    "KBHM": ("Birmingham-Shuttlesworth", 33.5629, -86.7535, 650),
    "KHSV": ("Huntsville International", 34.6372, -86.7751, 629),
    "KPWM": ("Portland International Jetport", 43.6462, -70.3093, 77),
    "KBTV": ("Burlington International", 44.4720, -73.1533, 335),
    "KFSD": ("Sioux Falls Regional", 43.5820, -96.7419, 1429),
    "KBOI": ("Boise Airport", 43.5644, -116.2228, 2871),
    "KGFK": ("Grand Forks International", 47.9493, -97.1761, 845),
    "KBIL": ("Billings Logan International", 45.8077, -108.5428, 3652),
    "KMSN": ("Dane County Regional", 43.1399, -89.3375, 887),
    # ============================================
    # CANADA
    # ============================================
    # Ontario
    "CYYZ": ("Toronto Pearson International", 43.6777, -79.6248, 569),
    "CYOW": ("Ottawa Macdonald-Cartier", 45.3225, -75.6692, 374),
    "CYHM": ("John C. Munro Hamilton", 43.1735, -79.9350, 780),
    "CYXU": ("London International", 43.0356, -81.1539, 912),
    "CYKF": ("Region of Waterloo International", 43.4608, -80.3847, 1055),
    "CYQT": ("Thunder Bay International", 48.3719, -89.3239, 653),
    # Quebec
    "CYUL": ("Montreal-Trudeau International", 45.4706, -73.7408, 118),
    "CYQB": ("Quebec City Jean Lesage", 46.7911, -71.3933, 244),
    # British Columbia
    "CYVR": ("Vancouver International", 49.1947, -123.1839, 14),
    "CYYJ": ("Victoria International", 48.6469, -123.4258, 63),
    "CYLW": ("Kelowna International", 49.9561, -119.3778, 1421),
    "CYXX": ("Abbotsford International", 49.0253, -122.3611, 195),
    # Alberta
    "CYYC": ("Calgary International", 51.1225, -114.0133, 3557),
    "CYEG": ("Edmonton International", 53.3097, -113.5800, 2373),
    # Manitoba
    "CYWG": ("Winnipeg James Armstrong Richardson", 49.9100, -97.2399, 783),
    # Saskatchewan
    "CYXE": ("Saskatoon John G. Diefenbaker", 52.1708, -106.6997, 1653),
    "CYQR": ("Regina International", 50.4319, -104.6658, 1894),
    # Nova Scotia
    "CYHZ": ("Halifax Stanfield International", 44.8808, -63.5086, 477),
    # New Brunswick
    "CYQM": ("Greater Moncton Romeo LeBlanc", 46.1122, -64.6786, 232),
    "CYSJ": ("Saint John Airport", 45.3161, -65.8903, 357),
    # Newfoundland
    "CYYT": ("St. John's International", 47.6186, -52.7519, 461),
    "CYDF": ("Deer Lake Regional", 49.2108, -57.3914, 72),
    # Prince Edward Island
    "CYYG": ("Charlottetown Airport", 46.2900, -63.1211, 160),
    # Northwest Territories / Yukon / Nunavut
    "CYZF": ("Yellowknife Airport", 62.4628, -114.4403, 675),
    "CYXY": ("Erik Nielsen Whitehorse", 60.7096, -135.0674, 2317),
    # ============================================
    # EUROPE
    # ============================================
    # United Kingdom
    "EGLL": ("London Heathrow", 51.4700, -0.4543, 83),
    "EGKK": ("London Gatwick", 51.1481, -0.1903, 202),
    "EGSS": ("London Stansted", 51.8850, 0.2350, 348),
    "EGLC": ("London City", 51.5053, 0.0553, 19),
    "EGCC": ("Manchester", 53.3537, -2.2750, 257),
    "EGBB": ("Birmingham", 52.4539, -1.7480, 327),
    "EGPH": ("Edinburgh", 55.9500, -3.3725, 135),
    "EGPF": ("Glasgow", 55.8719, -4.4331, 26),
    "EGGW": ("London Luton", 51.8747, -0.3683, 526),
    "EGHI": ("Southampton", 50.9503, -1.3568, 44),
    "EGNX": ("East Midlands", 52.8311, -1.3281, 306),
    "EGGD": ("Bristol", 51.3827, -2.7190, 622),
    # France
    "LFPG": ("Paris Charles de Gaulle", 49.0097, 2.5478, 392),
    "LFPO": ("Paris Orly", 48.7233, 2.3794, 291),
    "LFML": ("Marseille Provence", 43.4393, 5.2214, 74),
    "LFLL": ("Lyon-Saint Exupery", 45.7256, 5.0811, 821),
    "LFMN": ("Nice Cote d'Azur", 43.6584, 7.2159, 12),
    "LFBD": ("Bordeaux-Merignac", 44.8283, -0.7156, 162),
    "LFBO": ("Toulouse-Blagnac", 43.6292, 1.3678, 499),
    "LFSB": ("EuroAirport Basel-Mulhouse", 47.5896, 7.5299, 885),
    # Germany
    "EDDF": ("Frankfurt", 50.0264, 8.5431, 364),
    "EDDM": ("Munich", 48.3538, 11.7861, 1487),
    "EDDB": ("Berlin Brandenburg", 52.3514, 13.4939, 157),
    "EDDL": ("Dusseldorf", 51.2895, 6.7668, 147),
    "EDDH": ("Hamburg", 53.6304, 9.9882, 53),
    "EDDK": ("Cologne Bonn", 50.8659, 7.1427, 302),
    "EDDS": ("Stuttgart", 48.6899, 9.2220, 1276),
    "EDDW": ("Bremen", 53.0475, 8.7867, 14),
    # Netherlands
    "EHAM": ("Amsterdam Schiphol", 52.3086, 4.7639, -11),
    "EHRD": ("Rotterdam The Hague", 51.9569, 4.4372, -15),
    "EHEH": ("Eindhoven", 51.4501, 5.3743, 74),
    # Belgium
    "EBBR": ("Brussels", 50.9014, 4.4844, 184),
    "EBCI": ("Brussels South Charleroi", 50.4592, 4.4538, 614),
    # Spain
    "LEMD": ("Madrid-Barajas", 40.4936, -3.5668, 1998),
    "LEBL": ("Barcelona-El Prat", 41.2971, 2.0785, 12),
    "LEPA": ("Palma de Mallorca", 39.5517, 2.7388, 27),
    "LEMG": ("Malaga-Costa del Sol", 36.6749, -4.4991, 53),
    "LEAL": ("Alicante-Elche", 38.2822, -0.5582, 142),
    "LEVC": ("Valencia", 39.4893, -0.4816, 240),
    "LEZL": ("Seville", 37.4180, -5.8931, 112),
    "LEST": ("Santiago de Compostela", 42.8963, -8.4151, 1213),
    # Italy
    "LIRF": ("Rome Fiumicino", 41.8003, 12.2389, 13),
    "LIMC": ("Milan Malpensa", 45.6306, 8.7231, 768),
    "LIME": ("Milan Bergamo", 45.6739, 9.7042, 782),
    "LIPZ": ("Venice Marco Polo", 45.5053, 12.3519, 7),
    "LIRN": ("Naples International", 40.8860, 14.2908, 294),
    "LICC": ("Catania-Fontanarossa", 37.4668, 15.0664, 39),
    "LIPE": ("Bologna Guglielmo Marconi", 44.5354, 11.2887, 123),
    "LIML": ("Milan Linate", 45.4451, 9.2768, 353),
    # Switzerland
    "LSZH": ("Zurich", 47.4647, 8.5492, 1416),
    "LSGG": ("Geneva", 46.2381, 6.1089, 1411),
    # Austria
    "LOWW": ("Vienna International", 48.1103, 16.5697, 600),
    "LOWS": ("Salzburg", 47.7933, 13.0043, 1411),
    "LOWG": ("Graz", 46.9911, 15.4396, 1115),
    # Portugal
    "LPPT": ("Lisbon Humberto Delgado", 38.7742, -9.1342, 374),
    "LPPR": ("Porto Francisco Sa Carneiro", 41.2481, -8.6814, 228),
    "LPFR": ("Faro", 37.0144, -7.9659, 24),
    # Ireland
    "EIDW": ("Dublin", 53.4213, -6.2701, 242),
    "EICK": ("Cork", 51.8413, -8.4911, 502),
    "EINN": ("Shannon", 52.7020, -8.9248, 46),
    # Scandinavia
    "EKCH": ("Copenhagen Kastrup", 55.6180, 12.6560, 17),
    "ESSA": ("Stockholm Arlanda", 59.6519, 17.9186, 137),
    "ENGM": ("Oslo Gardermoen", 60.1939, 11.1004, 681),
    "EFHK": ("Helsinki-Vantaa", 60.3172, 24.9633, 179),
    "ESGG": ("Gothenburg Landvetter", 57.6628, 12.2798, 506),
    "EKBI": ("Billund", 55.7403, 9.1518, 247),
    "ENBR": ("Bergen Flesland", 60.2934, 5.2181, 170),
    # Eastern Europe
    "EPWA": ("Warsaw Chopin", 52.1657, 20.9671, 361),
    "LKPR": ("Prague Vaclav Havel", 50.1008, 14.2600, 1247),
    "LHBP": ("Budapest Ferenc Liszt", 47.4369, 19.2556, 495),
    "LROP": ("Bucharest Henri Coanda", 44.5711, 26.0850, 314),
    "LBSF": ("Sofia", 42.6952, 23.4114, 1742),
    "LWSK": ("Skopje International", 41.9616, 21.6214, 781),
    "LDZA": ("Zagreb Franjo Tudman", 45.7429, 16.0688, 353),
    # Greece
    "LGAV": ("Athens Eleftherios Venizelos", 37.9364, 23.9445, 308),
    "LGTS": ("Thessaloniki Macedonia", 40.5197, 22.9709, 22),
    "LGIR": ("Heraklion Nikos Kazantzakis", 35.3397, 25.1803, 115),
    "LGSR": ("Santorini", 36.3992, 25.4793, 127),
    # Turkey
    "LTFM": ("Istanbul Airport", 41.2753, 28.7519, 325),
    "LTFJ": ("Istanbul Sabiha Gokcen", 40.8986, 29.3092, 312),
    "LTAC": ("Ankara Esenboga", 40.1281, 32.9951, 3125),
    "LTAI": ("Antalya", 36.8987, 30.8005, 177),
    # Iceland
    "BIKF": ("Keflavik International", 63.9850, -22.6056, 171),
}


def lookup_airport(icao: str) -> dict | None:
    """Look up airport by ICAO code.

    Args:
        icao: ICAO airport code (e.g., "KCRQ", "KLAX", "EGLL")

    Returns:
        Dict with name, lat, lon, elevation_ft or None if not found
    """
    icao = icao.upper().strip()
    if icao in AIRPORTS:
        name, lat, lon, elev = AIRPORTS[icao]
        return {
            "icao": icao,
            "name": name,
            "lat": lat,
            "lon": lon,
            "elevation_ft": elev,
        }
    return None


def search_airports(query: str, limit: int = 10) -> list[dict]:
    """Search airports by ICAO code or name.

    Args:
        query: Search string (matches ICAO code or airport name)
        limit: Maximum results to return

    Returns:
        List of matching airports
    """
    query = query.upper().strip()
    results = []

    for icao, (name, lat, lon, elev) in AIRPORTS.items():
        if query in icao or query in name.upper():
            results.append(
                {
                    "icao": icao,
                    "name": name,
                    "lat": lat,
                    "lon": lon,
                    "elevation_ft": elev,
                }
            )
            if len(results) >= limit:
                break

    # Sort by ICAO code
    results.sort(key=lambda x: x["icao"])
    return results


def list_all_airports() -> list[dict]:
    """Get list of all airports.

    Returns:
        List of all airports sorted by ICAO code
    """
    results = []
    for icao, (name, lat, lon, elev) in AIRPORTS.items():
        results.append(
            {
                "icao": icao,
                "name": name,
                "lat": lat,
                "lon": lon,
                "elevation_ft": elev,
            }
        )
    results.sort(key=lambda x: x["icao"])
    return results
