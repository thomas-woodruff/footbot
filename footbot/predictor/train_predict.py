import logging

import requests
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Lasso
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.preprocessing import StandardScaler

from footbot.data import utils

log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_fmt)
logger = logging.getLogger(__name__)


def get_predicted_points_df(
        train_sql_path,
        predict_sql_path,
        client
):
    bootstrap_data = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/').json()
    current_event = [i for i in bootstrap_data['events'] if i['is_current']][0]['id']

    logger.info('getting training dataset')
    with open(train_sql_path, 'r') as file:
        train_sql = file.read()
        train_df = utils.run_query(train_sql, client)

    logger.info('getting prediction dataset')
    with open(predict_sql_path, 'r') as file:
        predict_sql = file.read().format(current_event=current_event)
        predict_df = utils.run_query(predict_sql, client)

    categorical_features = [
        'element_type',
        'team',
        'opponent_team',
        'was_home',
        'was_sunday',
        'was_weekday',
        'was_late',
        'was_early'
    ]

    numerical_features = [i for i in train_df.columns[1:] if i not in categorical_features]

    numerical_transformer = Pipeline([
        ('impute missing values', SimpleImputer()),
        ('scale numerical features', StandardScaler())
    ])

    preprocess = ColumnTransformer([
        ('preprocess numerical features', numerical_transformer, numerical_features),
        ('preprocess categorical features', OneHotEncoder(), categorical_features)
    ])

    model = Pipeline([
        ('pre-process features', preprocess),
        ('predictive model', Lasso(alpha=0.0020))
    ])

    logger.info('fitting model')
    model.fit(train_df.drop('total_points', axis=1), train_df['total_points'])

    logger.info('making predictions')
    predict_df['predicted_total_points'] = model.predict(
        predict_df.drop(['event', 'element', 'safe_web_name'], axis=1)
    )

    return predict_df
