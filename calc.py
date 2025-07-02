import numpy as np

# Source voltage
STARTING_VOLTAGE = 5.0
# Target voltage
TARGET_VOLTAGE = 2.456
# Maximum heat dissipation for a resistor (watts)
MAX_RESISTOR_HEAT = 0.25

# Should be E3, E6, E12, E24, E48, E96, or E192 series
RESISTOR_E_SERIES = 24


def main():
    """
    Main function to calculate resistor values for a voltage divider.
    """
    # Calculate the base list of resistors based on the E series value
    # I don't want to store the whole E series in the code
    if RESISTOR_E_SERIES not in [3, 6, 12, 24, 48, 96, 192]:
        raise ValueError(
            "Invalid E series value. Must be one of: 3, 6, 12, 24, 48, 96, or 192."
        )
    resistors = get_resistors_in_series(RESISTOR_E_SERIES)
    # print(f"Using E{RESISTOR_E_SERIES} series resistors: {sorted(resistors)}")

    # Scale the resistor selection with possible 10x, 100x, etc.
    resistors_scaled = [r * 10**i for r in resistors for i in range(6)]

    # Create a new dataframe to store the resistor combinations
    resistor_combos = np.array(
        [(r1, r2, 1, STARTING_VOLTAGE * r2 / (r1 + r2), 0, 0) for r1 in resistors_scaled for r2 in resistors_scaled],
        dtype=[
            ("R1", int),
            ("R2", int),
            ("Common Mult", int),
            ("Output Voltage", float),
            ("Percent Error", float),
            ("Power Dissipation", float),
        ],
    )
    # Simplify R1 and R2 to the same common multiplier
    for combo in resistor_combos:
        lowest_resistor = min(combo["R1"], combo["R2"])
        combo["Common Mult"] = int(np.log10(lowest_resistor)) - 1
        combo["R1"] /= 10**combo["Common Mult"]
        combo["R2"] /= 10**combo["Common Mult"]

    # Calculate the percent error for each combination
    for combo in resistor_combos:
        # Calculate values
        r1 = combo["R1"] * 10**combo["Common Mult"]
        r2 = combo["R2"] * 10**combo["Common Mult"]
        percent_error = abs((combo["Output Voltage"] - TARGET_VOLTAGE) / TARGET_VOLTAGE) * 100
        r1_voltage_drop = STARTING_VOLTAGE - combo["Output Voltage"]
        r1_power_dissipation = (r1_voltage_drop**2) / r1
        r2_power_dissipation = (combo["Output Voltage"]**2) / r2
        max_power_dissipation = max(r1_power_dissipation, r2_power_dissipation)
        # Insert into dataframe
        combo["Percent Error"] = percent_error
        combo["Power Dissipation"] = max_power_dissipation

    # Filter out combinations that exceed max power dissipation or have too high percent error
    valid_combos = resistor_combos[
        resistor_combos["Power Dissipation"] <= MAX_RESISTOR_HEAT,
    ]
    max_allowable_error = (resistors[1] / resistors[0] - 1) * 100
    print(
        f"Max allowable error for E{RESISTOR_E_SERIES} series: {max_allowable_error:.1f}%"
    )
    valid_combos = valid_combos[valid_combos["Percent Error"] <= max_allowable_error]
    # Sort the valid combinations
    valid_combos = np.sort(
        valid_combos,
        order=["Percent Error", "Output Voltage", "R1", "R2", "Common Mult"],
    )

    # Print the valid combinations
    print(f"Valid resistor combinations for E{RESISTOR_E_SERIES} series:")
    printed_combos = set()
    for combo in valid_combos:
        combo_tuple = (combo["R1"], combo["R2"])
        if combo_tuple not in printed_combos:
            output_str = [
                f"{combo['Output Voltage']:.3f}V",
                f"({combo['Percent Error']:.2f}%)",
                f"[{combo_tuple[0]}Ω + {combo_tuple[1]}Ω]E{combo['Common Mult']}",
                f"({combo['Power Dissipation']:.3f}W)"
            ]
            print("\t".join(output_str))
            printed_combos.add(combo_tuple)


def get_resistors_in_series(series: int) -> list:
    """
    Calculate resistor values for a voltage divider to achieve a target voltage.
    """
    # Start with E192 series as base
    E192 = [round(round(10 ** (i / 192), 2) * 100) for i in range(192)]
    # Slice to get the requested E series
    step = len(E192) // series
    resistors = E192[::step]
    # If falling back to < E48 series, adjust the base list accordingly
    if series < 48:
        resistors = [round(resistors / 10) for resistors in resistors]
        # The values 27-47 and the 82 divert from the exact mathematical rule
        resistors[10:17] = [27, 30, 33, 36, 39, 43, 47]  # +1 vs calc
        resistors[22:23] = [82]  # -1 vs calc
    return resistors


if __name__ == "__main__":
    main()
