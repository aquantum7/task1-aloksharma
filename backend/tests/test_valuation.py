from app.valuation import calculate_dcf, calculate_relative

def test_dcf_returns_positive_value():
    result = calculate_dcf(
        revenue=1000,
        fcf_margin=0.2,
        growth_rate=0.08,
        wacc=0.09,
        terminal_growth=0.03,
        forecast_years=5,
        net_debt=100,
        shares=100,
    )
    assert result["enterprise_value"] > 0
    assert result["intrinsic_value_per_share"] > 0

def test_relative_multiples():
    result = calculate_relative([{
        "name": "Demo",
        "market_cap": 1000,
        "net_income": 100,
        "book_value": 500,
        "enterprise_value": 1200,
        "ebitda": 200,
    }])
    assert result["peers"][0]["pe"] == 10
    assert result["peers"][0]["pb"] == 2
    assert result["peers"][0]["ev_ebitda"] == 6
