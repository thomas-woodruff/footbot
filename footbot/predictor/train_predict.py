import logging

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Lasso
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.preprocessing import StandardScaler

from footbot.data import utils

logger = logging.getLogger(__name__)


def get_predicted_points_df(train_sql_file, predict_sql_file, client):
    current_event = utils.get_current_event()

    logger.info("getting training dataset")
    train_df = utils.run_templated_query(train_sql_file, {}, client)
    logger.info("getting prediction dataset")
    predict_df = utils.run_templated_query(
        predict_sql_file, dict(current_event=current_event), client
    )

    categorical_features = [
        "element_type",
        "team",
        "opponent_team",
        "was_home",
        "was_sunday",
        "was_weekday",
        "was_late",
        "was_early",
    ]

    numerical_features = [
        i for i in train_df.columns[1:] if i not in categorical_features
    ]

    numerical_transformer = Pipeline(
        [
            ("impute missing values", SimpleImputer()),
            ("scale numerical features", StandardScaler()),
        ]
    )

    preprocess = ColumnTransformer(
        [
            (
                "preprocess numerical features",
                numerical_transformer,
                numerical_features,
            ),
            (
                "preprocess categorical features",
                OneHotEncoder(handle_unknown="ignore"),
                categorical_features,
            ),
        ]
    )

    model = Pipeline(
        [
            ("pre-process features", preprocess),
            ("predictive model", Lasso(alpha=0.0020)),
        ]
    )

    logger.info("fitting model")
    model.fit(train_df.drop("total_points", axis=1), train_df["total_points"])

    logger.info("making predictions")
    predict_df["predicted_total_points"] = model.predict(
        predict_df.drop(["event", "element", "safe_web_name"], axis=1)
    )

    return predict_df
