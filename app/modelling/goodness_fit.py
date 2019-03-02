from scipy.stats import chi2

def pearson_chi_squared_test(model, alpha=0.05):
	reject_h0 = model.pearson_chi2 > chi2.ppf(1-alpha, model.df_resid)
	p_value = 1 - chi2.cdf(model.pearson_chi2, model.df_resid)
	return reject_h0, p_value