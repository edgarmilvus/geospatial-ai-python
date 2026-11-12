# Simulated noisy data (1000x1000 array)
nir_noisy = np.random.randint(50, 800, size=(1000, 1000)).astype(np.float32)
red_noisy = np.random.randint(30, 700, size=(1000, 1000)).astype(np.float32)

# Introduce areas where the sum is zero or near zero (simulating deep water/shadow)
nir_noisy[100:110, 100:110] = 5
red_noisy[100:110, 100:110] = 5
NODATA_VALUE = -9999.0
