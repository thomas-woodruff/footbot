from scipy.stats import chi2

def pearson_chi_squared_test(model, alpha=0.05):
	reject_h0 = model.pearson_chi2 > chi2.ppf(0.95, model.df_resid)
	p_value = chi2.cdf(0.95, model.df_resid)
	return reject_h0, p_value