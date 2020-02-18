import logging
from footbot.data import utils
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Ridge


log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_fmt)
logger = logging.getLogger(__name__)


def get_dataframe_from_sql(
        file_path,
        client
):
    '''get training data from bigquery'''

    with open(file_path, 'r') as file:
        sql = file.read()

    df = utils.run_query(sql, client)

    return df


def get_predicted_points_df(
        train_sql_path,
        predict_sql_path,
        client
):
    logger.info('getting training dataset')
    train_df = get_dataframe_from_sql(train_sql_path, client)
    logger.info('getting prediction dataset')
    predict_df = get_dataframe_from_sql(predict_sql_path, client)

    train_features_df = train_df.drop('total_points', axis=1)
    predict_features_df = predict_df.drop(['event', 'element', 'safe_web_name'], axis=1)

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

    numerical_features = [i for i in train_features_df.columns if i not in categorical_features]

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
        ('predictive model', Ridge(alpha=180))
    ])

    logger.info('fitting model')
    model.fit(train_features_df, train_df['total_points'])

    logger.info('making predictions')
    predict_df['predicted_total_points'] = model.predict(predict_features_df)

    return predict_df
