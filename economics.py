def calculate_economics(
    recovered_gas_mmscfd,
    residual_flare_mmscfd,
    gas_value_per_mmbtu=4,
    capex=0,
    annual_opex=0,
    eor_oil_credit_annual=0,
    flare_penalty_avoided_annual=0
):
    # Approximate conversion
    mmbtu_per_mmscfd_day = 365

    annual_mmbtu = (
        recovered_gas_mmscfd
        * mmbtu_per_mmscfd_day
        * 1000
    )

    # Base gas revenue plus any extra EOR oil credit
    annual_gross_value = (
        (annual_mmbtu * gas_value_per_mmbtu) + eor_oil_credit_annual
    )

    # If it's a cost-compliance play, the financial metric is the net value *relative to doing nothing* (avoided penalty)
    annual_net_value = (
        annual_gross_value
        + flare_penalty_avoided_annual
        - annual_opex
    )

    if annual_net_value > 0:
        payback = capex / annual_net_value
    else:
        payback = None

    return {
        "annual_gross_value": annual_gross_value,
        "annual_net_value": annual_net_value,
        "payback_years": payback
    }
