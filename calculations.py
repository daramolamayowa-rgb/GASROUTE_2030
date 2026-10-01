def calculate_recovery(flare_mmscfd, recovery_factor=0.85):
    recoverable_gas = flare_mmscfd * recovery_factor
    residual_flare = flare_mmscfd - recoverable_gas

    return recoverable_gas, residual_flare


def calculate_compressor_duty(
    gas_flow_mmscfd,
    suction_pressure_barg,
    discharge_pressure_barg,
    efficiency=0.75
):
    """
    Screening-level compressor duty estimate.
    NOT for final equipment sizing.
    """

    pressure_ratio = (
        discharge_pressure_barg + 1.013
    ) / (
        suction_pressure_barg + 1.013
    )

    # Simplified screening relationship
    duty_kw = (
        gas_flow_mmscfd
        * 120
        * max(pressure_ratio - 1, 0.1)
        / efficiency
    )

    return duty_kw


def calculate_flare_reduction(
    recovered_gas,
    original_flare
):
    if original_flare <= 0:
        return 0

    return (recovered_gas / original_flare) * 100