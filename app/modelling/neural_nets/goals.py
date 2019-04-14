from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from sklearn.preprocessing import StandardScaler


def train_model(X, y):
	model = Sequential()
	model.add(Dense(units=25, activation='relu', input_shape=(len(X.columns),)))
	model.add(Dense(units=1, activation='linear'))

	model.compile(
	    loss='mean_absolute_error',
	    optimizer='adam'
	)

	model.fit(X, y, epochs=20, batch_size=10, verbose=1)

	return model


def predict(X_pred):
	return model.predict(X_pred).flatten()