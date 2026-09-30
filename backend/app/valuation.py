def calculate_dcf(
    revenue: float,
    fcf_margin: float,
    growth_rate: float,
    wacc: float,
    terminal_growth: float,
    forecast_years: int,
    net_debt: float,
    shares: float,
):
    if wacc <= terminal_growth:
        raise ValueError("WACC must be greater than terminal growth.")

    rows = []
    pv_fcf_total = 0.0
    current_revenue = revenue

    for year in range(1, forecast_years + 1):
        current_revenue *= 1 + growth_rate
        fcf = current_revenue * fcf_margin
        discount_factor = 1 / ((1 + wacc) ** year)
        pv = fcf * discount_factor
        pv_fcf_total += pv

        rows.append({
            "year": year,
            "revenue": current_revenue,
            "fcf": fcf,
            "discount_factor": discount_factor,
            "present_value": pv,
        })

    terminal_fcf = rows[-1]["fcf"] * (1 + terminal_growth)
    terminal_value = terminal_fcf / (wacc - terminal_growth)
    pv_terminal = terminal_value / ((1 + wacc) ** forecast_years)

    enterprise_value = pv_fcf_total + pv_terminal
    equity_value = enterprise_value - net_debt
    intrinsic_value_per_share = equity_value / shares

    return {
        "forecast": rows,
        "pv_explicit_fcf": pv_fcf_total,
        "terminal_value": terminal_value,
        "pv_terminal_value": pv_terminal,
        "enterprise_value": enterprise_value,
        "equity_value": equity_value,
        "intrinsic_value_per_share": intrinsic_value_per_share,
    }


def calculate_relative(peers):
    result = []
    for peer in peers:
        pe = peer.market_cap / peer.net_income if peer.net_income else None
        pb = peer.market_cap / peer.book_value if peer.book_value else None
        ev_ebitda = peer.enterprise_value / peer.ebitda if peer.ebitda else None

        result.append({
            "name": peer.name,
            "market_cap": peer.market_cap,
            "pe": pe,
            "pb": pb,
            "ev_ebitda": ev_ebitda,
        })

    valid_pe = [x["pe"] for x in result if x["pe"] is not None]
    valid_pb = [x["pb"] for x in result if x["pb"] is not None]
    valid_ev_ebitda = [x["ev_ebitda"] for x in result if x["ev_ebitda"] is not None]

    return {
        "peers": result,
        "median": {
            "pe": median(valid_pe),
            "pb": median(valid_pb),
            "ev_ebitda": median(valid_ev_ebitda),
        }
    }


def median(values):
    if not values:
        return None
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2
