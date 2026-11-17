// Weight and balance data for the three airplanes. Arms, limits, and envelopes are from the FAA type
// certificate data sheets and the manuals listed under each airplane's sources. Basic empty weight and
// moment are different for every airplane. The 172K entry is from that airplane's record and the Pilot 100i
// entry is the POH's sample problem value, each labeled as such. The rest stay null: never make one up.
window.WB_DATA = {
 "units": {
  "weight": "lb",
  "arm": "in aft of datum",
  "moment": "lb-in"
 },
 "fuel_lb_per_gal": 6.0,
 "oil_lb_per_gal": 7.5,
 "aircraft": [
  {
   "id": "c172r",
   "name": "Cessna 172R Skyhawk",
   "model": "172R",
   "serials": "17280001 and on",
   "engine": "Lycoming IO-360-L2A, 160 hp",
   "datum": "Lower portion of the front face of the firewall",
   "manual": "Cessna 172R POH 172RPHUS00 (Section 6)",
   "limits": {
    "normal": {
     "max_ramp": 2457,
     "max_takeoff": 2450,
     "max_landing": 2450
    },
    "utility": {
     "max_takeoff": 2100,
     "note": "172R POH shows 2,100 lb; TCDS 3A12 shows 2,200 lb. Using the more restrictive 2,100 until confirmed against this airplane's POH Section 2. Rear seat and baggage must be empty in utility category."
    }
   },
   "envelope": {
    "normal": [
     [35.0, 1500],
     [35.0, 1950],
     [40.0, 2450],
     [47.3, 2450],
     [47.3, 1500]
    ],
    "utility": [
     [35.0, 1500],
     [35.0, 1950],
     [36.5, 2100],
     [40.5, 2100],
     [40.5, 1500]
    ],
    "chart_axes": {
     "cg_min": 34,
     "cg_max": 48,
     "wt_min": 1500,
     "wt_max": 2600
    }
   },
   "stations": [
    {
     "id": "front",
     "label": "Pilot and Front Passenger",
     "arm": 37.0,
     "range": [34, 46],
     "note": "Arm for seat positioned for an average occupant"
    },
    {
     "id": "rear",
     "label": "Rear Passengers",
     "arm": 73.0
    },
    {
     "id": "bag1",
     "label": "Baggage Area 1",
     "arm": 95.0,
     "range": [82, 108],
     "max": 120,
     "note": "Arm to center of area"
    },
    {
     "id": "bag2",
     "label": "Baggage Area 2",
     "arm": 123.0,
     "range": [108, 142],
     "max": 50,
     "note": "Arm to center of area"
    },
    {
     "id": "fuel",
     "label": "Usable Fuel",
     "arm": 48.0,
     "max_gal": 53,
     "total_gal": 56
    }
   ],
   "combined_limits": [
    {
     "stations": [
      "bag1",
      "bag2"
     ],
     "max": 120,
     "label": "Baggage Areas 1 + 2 combined"
    }
   ],
   "oil": {
    "arm": -13.1,
    "weight": 15,
    "in_bew": true
   },
   "unusable_fuel": {
    "arm": 46.0,
    "weight": 18,
    "in_bew": true
   },
   "taxi_fuel_lb": 7,
   "va": "99 KIAS at 2,450 lb",
   "flags": [
    "If serial is on Cessna kit MK172-72-01 (180 hp) list, weights become 2,550/2,558 and fwd limit 41.0 at 2,550. Data here does not apply to that airplane."
   ],
   "sources": [
    "FAA TCDS 3A12 Rev. 80, Section XI",
    "Cessna 172R POH 172RPHUS00, Sections 2 and 6"
   ]
  },
  {
   "id": "c172k",
   "name": "Cessna 172K Skyhawk",
   "model": "172K",
   "serials": "17257162 through 17259223 (1969-70)",
   "engine": "Lycoming O-320-E2D, 150 hp",
   "datum": "Lower front face of the firewall",
   "manual": "1969/1970 Cessna 172 Owner's Manual (loading graph, no arm table); arms from FAA TCDS 3A12",
   "limits": {
    "normal": {
     "max_ramp": 2300,
     "max_takeoff": 2300,
     "max_landing": 2300,
     "note": "No separate ramp allowance; 2,300 applies on the ramp too"
    },
    "utility": {
     "max_takeoff": 2000,
     "note": "Rear seat and baggage must be empty in utility category"
    }
   },
   "envelope": {
    "normal": [
     [35.0, 1500],
     [35.0, 1950],
     [38.5, 2300],
     [47.3, 2300],
     [47.3, 1500]
    ],
    "utility": [
     [35.0, 1500],
     [35.0, 1950],
     [35.5, 2000],
     [40.5, 2000],
     [40.5, 1500]
    ],
    "chart_axes": {
     "cg_min": 34,
     "cg_max": 48,
     "wt_min": 1500,
     "wt_max": 2400
    }
   },
   "stations": [
    {
     "id": "front",
     "label": "Pilot and Front Passenger",
     "arm": 37.0,
     "range": [34, 46],
     "note": "Use actual seat position; 37 is the average-occupant arm from later 172 POHs"
    },
    {
     "id": "rear",
     "label": "Rear Passengers",
     "arm": 73.0
    },
    {
     "id": "bag",
     "label": "Baggage",
     "arm": 95.0,
     "max": 120
    },
    {
     "id": "jump",
     "label": "Child's Jump Seat (if installed)",
     "arm": 93.0
    },
    {
     "id": "fuel",
     "label": "Usable Fuel",
     "arm": 48.0,
     "max_gal": 38,
     "total_gal": 42
    }
   ],
   "combined_limits": [
    {
     "stations": [
      "bag",
      "jump"
     ],
     "max": 120,
     "label": "Baggage and/or auxiliary seat passenger (placard)"
    }
   ],
   "oil": {
    "arm": -14.0,
    "weight": 15,
    "in_bew": false,
    "note": "As originally certificated, empty weight includes NO oil. Add 15 lb unless this airplane's W&B record says BEW includes full oil."
   },
   "taxi_fuel_lb": null,
   "va": "106 KCAS (122 mph) at 2,300 lb (TCDS 3A12)",
   "flags": [],
   "sources": [
    "FAA TCDS 3A12 Rev. 80, Section V (incl. Note 1 and baggage placard)",
    "1969/1970 Cessna 172 Owner's Manual"
   ]
  },
  {
   "id": "pa28-100i",
   "name": "Piper Pilot 100i",
   "model": "PA-28-181 (Piper Pilot 100i)",
   "serials": "28020001 and up",
   "engine": "Lycoming IO-360-B4A",
   "datum": "78.4 in forward of the wing leading edge",
   "manual": "Piper POH VB-2960 (Section 6)",
   "limits": {
    "normal": {
     "max_ramp": 2558,
     "max_takeoff": 2550,
     "max_landing": 2550
    },
    "utility": null
   },
   "envelope": {
    "normal_definition": "Fwd 82.0 at 2,050 lb or less, straight line to 88.6 at 2,550; aft 93.0 at all weights",
    "normal": [
     [82.0, 1200],
     [82.0, 2050],
     [88.6, 2550],
     [93.0, 2550],
     [93.0, 1200]
    ],
    "utility": null,
    "chart_axes": {
     "cg_min": 82,
     "cg_max": 93,
     "wt_min": 1200,
     "wt_max": 2600
    },
    "fan": {
     "w0": -600,
     "pivot": 87,
     "tick": 50
    }
   },
   "stations": [
    {
     "id": "front",
     "label": "Pilot and Front Passenger",
     "arm": 80.5
    },
    {
     "id": "rear",
     "label": "Rear Passenger (one seat)",
     "arm": 118.1
    },
    {
     "id": "bag",
     "label": "Baggage",
     "arm": 142.8,
     "max": 200
    },
    {
     "id": "fuel",
     "label": "Usable Fuel",
     "arm": 95.0,
     "max_gal": 48,
     "total_gal": 50
    }
   ],
   "combined_limits": [],
   "oil": {
    "arm": 27.5,
    "weight": 15,
    "in_bew": true,
    "note": "Piper empty weight normally includes full oil; confirm on the W&B record"
   },
   "taxi_fuel_lb": 8,
   "seats": 3,
   "va": "113 KIAS at 2,550 lb; 98 KIAS at 1,917 lb (POH)",
   "flags": [
    "Three seats only: two front, one rear"
   ],
   "sources": [
    "FAA TCDS 2A13 Rev. 64, Section XV-C",
    "Piper POH VB-2960, Section 6 (Figure 6-15)"
   ]
  }
 ],
 "tails": [
  {
   "n_number": null,
   "aircraft": "c172r",
   "bew": null,
   "bew_moment": null,
   "bew_arm": null,
   "record_date": null
  },
  {
   "n_number": null,
   "aircraft": "c172k",
   "bew": 1419.67,
   "bew_moment": 51372.38,
   "bew_arm": 36.18614,
   "record_date": "2021-08-19",
   "note": "The basic empty weight is from the airplane's weight and balance change sheet dated August 19, 2021. Check that it is still the current record."
  },
  {
   "n_number": null,
   "aircraft": "pa28-100i",
   "bew": 1582.0,
   "bew_moment": 136843,
   "bew_arm": 86.5,
   "record_date": null,
   "label": "POH sample problem, Figure 6-9",
   "note": "The basic empty weight is the one in the POH's sample loading problem (VB-2960, Figure 6-9), not a particular airplane's. For a real flight, use the airplane's own weight and balance record."
  }
 ]
};
