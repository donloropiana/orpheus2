# IMPORT DATA FROM edgar_data.py AND yahoo_data.py

def input_sheet():
    # base_inputs, value_drivers, market_numbers, other_inputs, and default assumptions all come from Input Sheet
    industry = ''

    base_inputs = {
        'last_twelve_months' : {
            'revenues' : '', # TTM data from yfinance
            'operating_income' : '', # TTM data from yfinance
            'interest_expense' : '', # TTM data from yfinance, sometimes bundled with other financing costs (maybe use 10K)
            'bv_equity' : '', # TTM data from yfinance, may have to adjust for inter period transactions affecting equity. BV Eqty = Ttl. Common Eqty + Minority Interest (or Non Controlling Interest)
            'bv_debt' : '', # 10K and 10Qs (TTM good for now)
            'has_r&d_expenses_to_capitalize' : '', # 10K
            'has_operating_lease_commitments' : '', # 10K (footnotes); This is a TRUE or FALSE variable, 
            'cash_and_marketable_securities' : '', # TTM Cash, Cash Equivalents & Short Term Investments
            'cross_holdings_and_non_operating_assets' : '', # 10K or 10Q (MD&A section)
            'minority_interests' : '', # 10K or 10Q (footnotes)
            'shares_outstanding' : '', # yfinance
            'stock_price' : '', # yfinance
            'effective_tax_rate' : '', # = ttl_tax_expense / pre_tax_income
            'marginal_tax_rate' : '',
        },
        'last_10K' : {
            'revenues' : '',
            'operating_income' : '',
            'interest_expense' : '',
            'bv_equity' : '',
            'bv_debt' : '',
            'cash_and_marketable_securities' : '',
            'cross_holdings_and_non_operating_assets' : '',
            'minority_interests' : '',
        }
    }

    value_drivers = {
        'revenue_growth_rate_for_next_year' : '',
        'operating_margin_for_next_year' : '',
        'cagr_years_2_to_5' : '',
        'target_pretax_operating_margin' : '',
        'year_of_convergence_for_margin' : '',
        'sales_to_capital_years_1_to_5' : '',
        'sales_to_capital_years_6_to_10' : f"{base_inputs['last_twelve_months']['revenues'] / (base_inputs['last_twelve_months']['bv_equity'] + base_inputs['last_twelve_months']['bv_debt'] - base_inputs['last_twelve_months']['cash_and_marketable_securities'])}",
    }

    market_numbers = {
        'risk_free_rate' : '',
        'initial_cost_of_capital' : ''
    }

    other_inputs = {
        'has_employee_options_outstanding' : '',
        'employee_options_outstanding' : '',
        'avg_strike_price' : '',
        'avg_maturity' : '',
        'std_dev_stock_price' : ''
    }

    default_assumptions = {
        'override_cost_of_capital_assumption' : '', # In stable growth, I will assume that your firm will have a cost of capital similar to that of typical mature companies (riskfree rate + 4.5%)
        'alternative_cost_of_capital' : '',
        'override_return_of_capital_assumption' : '', # I will assume that your firm will earn a return on capital equal to its cost of capital after year 10. I am assuming that whatever competitive advantages you have today will fade over time.
        'alternative_return_of_capital' : '', 
        'override_failure_assumption' : '', # I will assume that your firm has no chance of failure over the foreseeable future.
        'alternative_failure_rate' : '', # Tough to estimate but a key input. Use the failure rate worksheet, if necessary.
        'proceeds_from_failure_go_to' : '', # B: Book value of capital, V= Estimated fair value for the company
        'distress_proceeds_as_percentage_of_book_or_fair_value' : '',
        'override_reinvestment_growth_assumption' : '', # I assume that reinvestment in a year translates into growth in the next year, i.e., there is a one year lag between reinvesting and generating growth from that reinvestment.
        'alternative_lag' : '1', # If yes, enter a different lag (0 = no lag to 3 = lag of 3 years)
        'override_tax_rate_assumption' : '', # I will assume that your effective tax rate will adjust to your marginal tax rate by your terminal year. If you override this assumption, I will leave the tax rate at your effective tax rate.
        'override_no_nol_assumption' : '', # I will assume that you have no losses carried forward from prior years ( NOL) coming into the valuation. If you have a money losing company, you may want to override tis.
        'nol_carryforward_into_year1' : '', # An NOL will shield your income from taxes, even after you start making money.
        'override_risk_free_rate_assumption' : '', # I will asssume that today's risk free rate will prevail in perpetuity. If you override this assumption, I will change the riskfree rate after year 10.
        'risk_free_rate_after_year_10' : '', # Enter your estimate of what the riskfree rate (in your currency of choice) will be after year 10
        'override_growth_risk_free_rate_assumption' : '', # I will assume that the growth rate in perpetuity will be equal to the risk free rate. This allows for both valuation consistency and prevents "impossible" growth rates.
        'growth_rate_in_perpetuity' : '', # This can be negative, if you feel the company will decline (and disappear) after growth is done. If you let it exceed the risk free rate, you are on your own in uncharted territory.
        'override_trapped_cash_assumption' : '', # I have assumed that none of the cash is trapped (in foreign countries) and that there is no additional tax liability coming due and that cash is a neutral asset.
        'trapped_cash' : '', # Cash that is trapped in foreign markets (and subject to additoinal tax) or cash that is being discounted by the market (because of management mistrust)
        'avg_tax_rate_cash_strap_foreign_markets' : '' # Additional tax rate due on trapped cash or discount being applied to cash balance because of mistrust.
    }
    return base_inputs, value_drivers, market_numbers, other_inputs, default_assumptions


base_inputs, value_drivers, market_numbers, other_inputs, default_assumptions = input_sheet() ### MOVE MOVE MOVE MOVE MOVE

def cost_of_capital(base_inputs):
    cost_of_capital_approaches = ['I will input', 'Detailed', 'Industry Average', 'Distribution']
    cost_of_capital_approach = cost_of_capital_approaches[3] # Input

    direct_input_cost_of_capital = 0.09
    approach_based_cost_of_capital = None

    # Approach 1: Detailed Cost of Capital
    # # Inputs: 
    # # # Equity
    shares_outstanding = base_inputs['current_year']['shares_outstanding']
    market_price_per_share = base_inputs['current_year']['stock_price']

    approaches_for_estimating_beta = ['Direct input', 'Single Business(US)', 'Single Business(Global)', 'Multibusiness(US)', 'Multibusiness(Global)']
    beta_estimation_approach = approaches_for_estimating_beta[1] # Input
    direct_input_levered_beta = 1.2 # can also take regression beta!
    unlevered_beta = None # =IF(B21="Single Business(US)",VLOOKUP('Input sheet'!B8,'Industry Averages(US)'!A2:G95,7),IF(B21="Multibusiness(US)",K48,IF(B21="Single Business(Global)",VLOOKUP('Input sheet'!B9,'Industry Average Beta (Global)'!A2:G95,7),'Cost of capital worksheet'!K64)))
    risk_free_rate = None # ='Input sheet'!B34
    
    direct_input_erp_approaches = ['Will input', 'Country of incorporation', 'Operating countries', 'Operating regions']
    direct_input_erp_approach = direct_input_erp_approaches[3] # Input
    direct_input_erp = 0.06
    erp_for_cost_of_equity = None # =IF(B25="Will Input",B26,IF(B25="Country of Incorporation",VLOOKUP('Input sheet'!B7,'Country equity risk premiums'!A5:E181,4),IF(B25="Operating regions",'Cost of capital worksheet'!K32,'Cost of capital worksheet'!K18)))

    # # # Debt
    bv_straight_debt = None # ='Input sheet'!B15
    interest_expense_on_debt = None # ='Input sheet'!B13
    average_maturity =	3
    approaches_for_estimating_pretax_cost_of_debt = ['Direct input', 'Synthetic rating', 'Actual rating']
    approach_for_estimating_pretax_cost_of_debt = approaches_for_estimating_pretax_cost_of_debt[2] # Input

    pretax_cost_of_debt = None # =IF(B33="Direct Input",B34,IF(B33="Synthetic Rating",'Synthetic rating'!D16,B24+VLOOKUP('Cost of capital worksheet'!B35,'Synthetic rating'!G42:H56,2)))
    tax_rate = base_inputs['current_year']['marginal_tax_rate'] # ='Input sheet'!B24

    bv_convertible_debt = None # Input
    interest_expense_on_convertible_debt = None # Input
    maturity_on_convertible_bond = None # Input
    market_value_of_convertible_bond = None # Input

    debt_value_of_operating_lease = None # =IF('Input sheet'!B17="Yes",'Operating lease converter'!F33,0)

    # # # Preferred Stock
    number_of_preferred_shares = None # Input
    market_price_per_preferred_share = None # Input
    annual_dividend_per_preferred_share = None # Input

    # Approach 1 Output
    mv_straight_debt_estimate = interest_expense_on_debt*(1-(1+pretax_cost_of_debt)^(-average_maturity))/pretax_cost_of_debt+bv_straight_debt/(1+pretax_cost_of_debt)^average_maturity
    value_straight_debt_in_convertible_estimate = interest_expense_on_convertible_debt*(1-(1+pretax_cost_of_debt)^(-maturity_on_convertible_bond))/pretax_cost_of_debt+bv_convertible_debt/(1+pretax_cost_of_debt)^maturity_on_convertible_bond
    value_debt_in_operating_lease = debt_value_of_operating_lease
    value_of_equity_in_convertible_estimate = market_value_of_convertible_bond - value_straight_debt_in_convertible_estimate
    levered_beta_of_equity = None # =IF(B21="Direct Input",B22,B23*(1+(1-B38)*(C60/B60)))

    # Operating Countries ERP calculations
    # # # # The last two rows in each of country/region risk premium tables is set aside for your input to provide you with flexibility to enter some numbers directly. For instance, assume that you have a company that breaks its revenues down into three countries and then puts the rest into "Rest of the World". 
    # # # # You can enter the "Rest of the World" in one of these two rows and enter an equity risk premium for the rest of the world. The easiest way to do that is to go into the country equity risk premium worksheet and change the GDP for the three countries that you have data for to zero and compute the global weighted average ERP for the remaining countries. 
    # # # # With the regional worksheet, you can use the last two rows to enter the data for an individual country (usually the domestic country) that might be broken out though the rest of the revenues are broken down by region. You can look up the ERP for the country in the country ERP worksheet.
    countries = [] # Input (United States, China, Rest of World)
    country_revenues = [] # Input
    total_country_revenue = sum(country_revenues)
    country_erps = [] # =IF(H5=0,0,VLOOKUP(G5,'Country equity risk premiums'!$A$5:$D$195,4))
    country_weights = np.divide(country_revenues, total_country_revenue) if country_revenues and total_country_revenue > 0 else 0 # =IF(H5>0,H5/$H$18,)
    country_weighted_erps = np.multiply(country_erps, country_weights) # =IF(J5=0,0,I5*J5)

    country_total_erp = sum(country_erps)
    country_weighted_erp = sum(country_weighted_erps)

    # Operating Regions ERP calculations
    regions = []
    regional_revenues = []
    total_regional_revenue = sum(regional_revenues)
    regional_erps = []
    regional_weights = np.divide(regional_revenues, total_regional_revenue) if regional_revenues and total_regional_revenue > 0 else 0 # =IF(H5>0,H5/$H$18,)
    regional_weighted_erps = np.multiply(country_erps, regional_weights)

    regional_total_erp = sum(regional_erps)
    regional_weighted_erp = sum(regional_weighted_erps)

    # Multi Business (US Industry Averages)
    # # The cost of capital  is in US dollars, using the riskfree rate at the start of the year. It will be adjusted for the difference in riskfree rates to make it more current and to change currencies.
    us_businesses = []
    us_business_revenues = []
    us_company_revenue = sum(us_business_revenues)
    us_ev_to_sales_ratios = [] # =IF(G36=0,,VLOOKUP(G36,'Industry Averages(US)'!$A$2:$S$95,15))
    us_estimated_values = np.multiply(us_business_revenues, us_ev_to_sales_ratios)
    us_business_unlevered_betas = [] # =IF(I36=0,0,VLOOKUP(G36,'Industry Averages(US)'!$A$2:$S$95,7))
    us_business_costs_of_capital = [] # =IF(I36=0,0,VLOOKUP(G36,'Industry Averages(US)'!$A$2:$S$95,13))

    us_company_estimated_value = sum(us_estimated_values)
    us_company_unlevered_beta = sum(np.divide(np.multiply(us_business_unlevered_betas, us_estimated_values), us_company_estimated_value))
    us_company_cost_of_capital = sum(np.divide(np.multiply(us_business_costs_of_capital, us_estimated_values), us_company_estimated_value))

    # Multi Business (Global Industry Averages)
    # # The cost of capital is in US dollars, using the riskfree rate at the start of the year. It will be adjusted for the difference in riskfree rates to make it more current and to change currencies.
    global_businesses = []
    global_business_revenues = []
    global_company_revenue = sum(global_business_revenues)
    global_ev_to_sales_ratios = [] # =IF(G36=0,,VLOOKUP(G36,'Industry Averages(US)'!$A$2:$S$95,15))
    global_estimated_values = np.multiply(global_business_revenues, global_ev_to_sales_ratios)
    global_business_unlevered_betas = [] # =IF(I36=0,0,VLOOKUP(G36,'Industry Averages(US)'!$A$2:$S$95,7))
    global_business_costs_of_capital = [] # =IF(I36=0,0,VLOOKUP(G36,'Industry Averages(US)'!$A$2:$S$95,13))

    global_company_estimated_value = sum(global_estimated_values)
    global_company_unlevered_beta = sum(np.divide(np.multiply(global_business_unlevered_betas, global_estimated_values), global_company_estimated_value))
    global_company_cost_of_capital = sum(np.divide(np.multiply(global_business_costs_of_capital, global_estimated_values), global_company_estimated_value))


    # Approach 2: Industry average cost of capital, adjusted for risk free rate differences
    industry_options = ['Single Business(US)', 'Single Business(Global)', 'Multibusiness(US)', 'Multibusiness(Global)']
    industry_choice = 'Multibusiness(US)'
    cost_of_capital_adjusted_for_risk_free_rate_differences = None # =IF(B66="Single Business(US)",(VLOOKUP('Input sheet'!B8,'Industry Averages(US)'!A2:M95,13)+('Input sheet'!B34-3.88%)),IF(B66="Multibusiness(US)",L48+('Input sheet'!B34-3.88%),IF(B66="Single Business(Global)",(VLOOKUP('Input sheet'!B8,'Industry Average Beta (Global)'!A2:M95,13)+('Input sheet'!B34-3.88%)),L64+('Input sheet'!B34-3.88%))))

    # Approach 3: Use histogram of costs of capital of all publicly traded firms
    groupings = ['US', 'Emerging Markets', 'Global']
    risk_groupings = ['First Decile', 'First Quartile', 'Median', 'Third Quartile', 'Ninth Decile']
    company_market_grouping = 'US'
    company_risk_grouping = 'Median'

    # # cost of capital by region table
    # # # Comment: These costs of capital are all in US dollars and reflect the US dollar  riskfree rate at the start of the year. Once you make your choice, though, I will adjust the rate by the difference in riskfree rates, effectively converting currency and bringing it up to date.
    region_list = ['Emerging', 'Europe', 'Global', 'Japan', 'US']
    first_decile_costs_of_capital = [] # get costs of capital in the following order: 'Emerging', 'Europe', 'Global', 'Japan', 'US'
    first_quartile_costs_of_capital = []
    median_costs_of_capital = []
    third_quartile_costs_of_capital = []
    ninth_decile_costs_of_capital = []
    regional_costs_of_capital = {
        'First Decile' : first_decile_costs_of_capital, 
        'First Quartile' : first_quartile_costs_of_capital, 
        'Median' : median_costs_of_capital, 
        'Third Quartile' : third_quartile_costs_of_capital, 
        'Ninth Decile' : ninth_decile_costs_of_capital
    }

    cost_of_capital_from_risk_group = regional_costs_of_capital[f'{company_market_grouping}'][region_list.index[f'{company_risk_grouping}']]

    return

def synthetic_rating():
    firm_type = None # ='Cost of capital worksheet'!B36
    current_earnings = None # =IF('Input sheet'!B17="Yes",'Input sheet'!B12+'Operating lease converter'!F32,'Input sheet'!B12) # EBIT # (Add back only long term interest expense for financial firms)
    current_interest_expense = None # ='Input sheet'!B34 # (Use only long term interest expense for financial firms)

    # output
    interest_coverage_ratio = 1000000 if current_interest_expense == 0 else (-100000 if current_earnings < 0 else current_earnings / current_interest_expense) # =IF(current_interest_expense=0,1000000,IF(current_earnings<0,-100000,current_earnings/current_interest_expense))
    
    return

def operating_lease_converter():
    # This function converts operating lease commitments to debt equivalent values.

    # Current year operating lease expense, to be pulled from the SEC filings.
    operating_lease_expense_current_year = None # pull from sec

    # Define time periods for the commitments
    year_col = ['1','2','3','4','5','6 and beyond']
    # Initialize the commitment values list, to be filled with actual data.
    commitment_col = []

    # Pre-tax cost of debt as per the cost of capital worksheet.
    pre_tax_cost_of_debt = None # cost of capital worksheet


    # Estimate the number of years embedded in year 6 estimate based on average of previous commitments.
    number_of_years_embedded_in_yr_6_estimate = (
        np.round(commitment_col[5] / np.average(commitment_col[0:4]), 0)
        if commitment_col[5] > 0 else 0
    )

    # Convert the commitment of '6 and beyond' into an annual commitment.
    commitment_yr_6_and_beyond = (
        (commitment_col[5] / number_of_years_embedded_in_yr_6_estimate if number_of_years_embedded_in_yr_6_estimate > 0 else commitment_col[5])
        if commitment_col[5] > 0 else 0
    )

    # Initialize the debt equivalent value of operating leases.
    debt_value_of_operating_leases = None

    # Calculate the present value of commitments for each year.
    for i in range(len(commitment_col)):
        if i <= 4:
            debt_value_of_operating_leases += commitment_col[i]/((1+pre_tax_cost_of_debt)**i)
        elif i == 5: # =IF(D18>0,(B27*(1-(1+C15)^(-D18))/C15)/(1+$C$15)^5,B27/(1+C15)^6)
            debt_value_of_operating_leases += ((commitment_yr_6_and_beyond * (1 - (1 + pre_tax_cost_of_debt) ** (-number_of_years_embedded_in_yr_6_estimate)) / pre_tax_cost_of_debt) / ((1 + pre_tax_cost_of_debt) ** 5) if (number_of_years_embedded_in_yr_6_estimate > 0) else (commitment_yr_6_and_beyond / ((1 + pre_tax_cost_of_debt) ** 6)))
    
    depreciation_on_operating_lease_asset = debt_value_of_operating_leases / (5 + number_of_years_embedded_in_yr_6_estimate) # Straight line depreciation
    adjustment_to_operating_earnings = operating_lease_expense_current_year - depreciation_on_operating_lease_asset # Add this to pre-tax operating income
    adjustment_to_total_debt_outstanding = debt_value_of_operating_leases # Add this amount to debt
    adjustment_to_depreciation = debt_value_of_operating_leases

    return debt_value_of_operating_leases, depreciation_on_operating_lease_asset, adjustment_to_operating_earnings, adjustment_to_total_debt_outstanding, adjustment_to_depreciation

# valuation_output goes last!!!
def valuation_output(base_inputs, value_drivers, market_numbers, other_inputs, default_assumptions):
    columns = ['Base','1','2','3','4','5','6','7','8','9','10','Terminal']
    row_names = [
        'revenue_growth_rate',
        'revenues',
        'operating_margin',
        'operating_income',
        'tax_rate',
        'operating_income_minus_tax',
        'reinvestment',
        'fcff',
        'nol',
        'cost_of_capital',
        'cumulated_discount_factor',
        'PV(FCFF)'
    ]

    projection_df = pd.DataFrame(index=row_names, columns=columns)

    # Base year inputs into projection data frame
    projection_df['Base', 'revenues'] = base_inputs['current_year']['revenues']
    projection_df['Base', 'operating_income'] = base_inputs['current_year']['operating_income'] # =IF(base_inputs['current_year']['has_operating_lease_commitments'] = "Yes", IF(base_inputs['current_year']['has_r&d_expenses_to_capitalize']="Yes",'Input sheet'!B12+'Operating lease converter'!F32+'R& D converter'!D39,'Input sheet'!B12+'Operating lease converter'!F32),IF('Input sheet'!B16="Yes",'Input sheet'!B12+'R& D converter'!D39,'Input sheet'!B12))
    projection_df['Base', 'operating_margin'] = projection_df['Base', 'operating_income']/projection_df['Base', 'revenues']
    projection_df['Base', 'tax_rate'] = base_inputs['current_year']['effective_tax_rate']
    projection_df['Base', 'operating_income_minus_tax'] = projection_df['Base', 'operating_income'] * projection_df['Base', 'tax_rate'] if projection_df['Base', 'operating_income'] > 0 else projection_df['Base', 'operating_income'] # =IF(B5>0,B5*(1-B6),B5)
    projection_df['Base', 'nol'] = default_assumptions['nol_carryforward_into_year1'] if default_assumptions['override_no_nol_assumption'] is False else 0 # =IF('Input sheet'!B61="Yes",'Input sheet'!B62,0

    for year in projection_df.index:
        projection_df.loc[year, 'revenue_growth_rate']
        print()
    return