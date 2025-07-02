import numpy as np
import pandas as pd

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
        [
            (
                r1,
                r2,
                1,
                STARTING_VOLTAGE * r2 / (r1 + r2),
                0,
                STARTING_VOLTAGE / (r1 + r2),
                0,
            )
            for r1 in resistors_scaled
            for r2 in resistors_scaled
        ],
        dtype=[
            ("R1", int),
            ("R2", int),
            ("Mult", int),
            ("Output Voltage", float),
            ("Percent Error", float),
            ("Current", float),
            ("Power Dissipation", float),
        ],
    )
    # Simplify R1 and R2 to the same Multiplier
    for combo in resistor_combos:
        lowest_resistor = min(combo["R1"], combo["R2"])
        # If <=E24, drop to 2 digits. Otherwise, keep 3 digits.
        num_digits = 2 if RESISTOR_E_SERIES <= 24 else 3
        common_mult = 10 ** (int(np.log10(lowest_resistor)) - num_digits + 1)
        combo["Mult"] = common_mult
        combo["R1"] /= common_mult
        combo["R2"] /= common_mult

    # Calculate the percent error for each combination
    for combo in resistor_combos:
        # Calculate the percent error
        percent_error = (
            abs((combo["Output Voltage"] - TARGET_VOLTAGE) / TARGET_VOLTAGE) * 100
        )
        combo["Percent Error"] = percent_error
        # Calculate power dissipation for R1 and R2
        r1_voltage_drop = STARTING_VOLTAGE - combo["Output Voltage"]
        r1_power_dissipation = r1_voltage_drop * combo["Current"]
        r2_power_dissipation = combo["Output Voltage"] * combo["Current"]
        max_power_dissipation = max(r1_power_dissipation, r2_power_dissipation)
        combo["Power Dissipation"] = max_power_dissipation

    # Filter out combinations that exceed max power dissipation or have too high percent error
    valid_combos = resistor_combos[
        resistor_combos["Power Dissipation"] <= MAX_RESISTOR_HEAT,
    ]
    max_allowable_error = (resistors[1] / resistors[0] - 1) * 100
    valid_combos = valid_combos[valid_combos["Percent Error"] <= max_allowable_error]
    # Sort the valid combinations
    valid_combos = np.sort(
        valid_combos,
        order=["Percent Error", "Output Voltage", "R1", "R2", "Mult"],
    )
    # Remove duplicates based on R1 and R2
    # This ensures we don't have the same resistor values with different Multipliers
    # We keep the first occurrence (lowest Multiplier)
    dt = np.dtype([("R1", valid_combos.dtype["R1"]), ("R2", valid_combos.dtype["R2"])])
    temp_r1_r2_array = np.vstack((valid_combos["R1"], valid_combos["R2"])).T
    R1_R2_view = np.ascontiguousarray(temp_r1_r2_array).view(dt).reshape(-1)
    _, unique_indices = np.unique(R1_R2_view, return_index=True)
    unique_R1_R2 = valid_combos[unique_indices]
    # Resort the unique combinations
    unique_R1_R2 = np.sort(
        unique_R1_R2,
        order=["Percent Error", "Output Voltage", "R1", "R2", "Mult"],
    )

    # Format everything into a DataFrame for better readability
    df = pd.DataFrame(unique_R1_R2)
    df_display = df.copy()
    df_display["R1"] = df_display["R1"].apply(lambda x: f"{x} Ω")
    df_display["R2"] = df_display["R2"].apply(lambda x: f" {x} Ω")
    df_display["Mult"] = df_display["Mult"].apply(lambda x: f" x{x}")
    df_display["Output Voltage"] = df_display["Output Voltage"].apply(
        lambda x: f" {x:.3f} V"
    )
    df_display["Percent Error"] = df_display["Percent Error"].apply(
        lambda x: f" {x:.3f}%"
    )
    df_display["Current"] = df_display["Current"].apply(lambda x: f" {x * 1000:.3f} mA")
    df_display["Power Dissipation"] = df_display["Power Dissipation"].apply(
        lambda x: f" {x:.3f} W"
    )
    # Add an extra space before column names for better readability
    for col in df_display.columns[1:]:
        df_display.rename(columns={col: " " + col}, inplace=True)

    # Print the results
    print(f"Starting Voltage: {STARTING_VOLTAGE} V")
    print(f"Target Voltage: {TARGET_VOLTAGE} V")
    print(f"Maximum Resistor Heat Dissipation: {MAX_RESISTOR_HEAT} W")
    print(f"Valid resistor combinations for E{RESISTOR_E_SERIES} series:")
    print(df_display.to_string(index=False))


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
