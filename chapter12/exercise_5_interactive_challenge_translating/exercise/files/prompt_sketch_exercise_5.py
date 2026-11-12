# Assume this array is the result of a successful NDVI calculation
# (e.g., the output from Exercise 4, but without the -9999 nodata value, 
# ensuring clean values between -1.0 and 1.0 for classification)
final_ndvi_map = np.load('simulated_ndvi_data.npy') 
# Note: In the actual exercise environment, this file would be provided.
