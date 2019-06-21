from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense


def train_model(X, y, loss='mean_squared_error'):
	model = Sequential()
	model.add(Dense(units=25, activation='relu', input_shape=(len(X.columns),)))
	model.add(Dense(units=1, activation='linear'))

	model.compile(
		loss=loss,
		optimizer='adam'
	)

	model.fit(X, y, epochs=20, batch_size=10, verbose=1)

	return model


def predict(X_pred):
	return model.predict(X_pred).flatten()
