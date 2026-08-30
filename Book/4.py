#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np 
import matplotlib.pyplot as plt

housing = pd.read_csv('/home/siyam/MyCodes/MachineLearning/Book/datasets/housing/housing.csv')

from sklearn.model_selection import train_test_split
train_set, test_set = train_test_split(housing, test_size=0.2, random_state=42)


housing["income_cat"] = pd.cut(housing["median_income"],
                        bins=[0., 1.5, 3.0, 4.5, 6., np.inf],
                        labels=[1, 2, 3, 4, 5])

print(housing["income_cat"])

housing["income_cat"].value_counts().sort_index().plot.bar(rot=0, grid=True)
plt.xlabel("Income category")
plt.ylabel("Number of districts")

from sklearn.model_selection import StratifiedShuffleSplit

splitter = StratifiedShuffleSplit(n_splits=10, test_size=.2, random_state=42)


# In[2]:


from sklearn.model_selection import StratifiedShuffleSplit
splitter = StratifiedShuffleSplit(n_splits=10,test_size=0.2,random_state=42)

# strat_splits = []

# for trainidx, testidx in splitter.split(housing, housing['income_cat']):
#     strat_trn = housing.iloc[trainidx]
#     strat_tst = housing.iloc[testidx]
#     strat_splits.append([strat_trn, strat_tst])

# for i, (train,test) in enumerate(strat_splits):
#     print(f"Split {i+1}:")
#     print("Train: ", train.shape)
#     print("Test : ", test.shape)
#     print()

strat_train_set, strat_test_set = train_test_split(housing, test_size=0.2, 
                                                   stratify=housing['income_cat'], 
                                                   random_state=42)

print(strat_test_set)

for x in (strat_train_set, strat_test_set):
    x.drop('income_cat', axis=1, inplace=True)

print(strat_test_set)


# In[3]:


housing = strat_train_set.copy()

housing.plot(kind='scatter', x='longitude', y= 'latitude', grid= 'True', alpha=.1)


# In[4]:


housing.plot(
    kind="scatter",
    x="longitude",
    y="latitude",
    grid=True,
    s=housing["population"] / 100,
    label="population",
    c="median_house_value",
    cmap="jet",
    colorbar=True,
    legend=True,
    sharex=False,
    figsize=(10, 7)
)
plt.show()


# In[5]:


correlation_matrix = housing.corr(numeric_only=True)
correlation_matrix["median_house_value"].sort_values(ascending=False)

print(housing.info())


# # Heatmap

# In[6]:


import seaborn as sns
sns.heatmap(correlation_matrix, cmap='coolwarm', annot=True)


# In[7]:


from pandas.plotting import scatter_matrix
attributes = ['median_house_value', 'housing_median_age', 'total_rooms', 'median_income']
scatter_matrix(housing[attributes], figsize=(12,8))


# In[8]:


housing.plot(x='median_income',
             y='median_house_value',
             alpha=0.1,
             grid=True,
             kind='scatter')


# In[9]:


housing.head()


# In[10]:


housing['rooms_per_house'] = housing['total_rooms'] / housing['households']
housing['bedrooms_ratio']  = housing['total_bedrooms'] / housing['total_rooms']
housing['people_per_house']= housing['population'] / housing['households']


# In[11]:


corr_matrix = housing.corr(numeric_only=True)
print(corr_matrix)


# In[12]:


housing = strat_train_set.drop("median_house_value", axis=1)
housing_labels = strat_train_set["median_house_value"].copy()


# ## Removing whole row where there is missing value

# In[13]:


# median=housing["total_bedrooms"].median()
# housing['total_bedrooms'] = housing['total_bedrooms'].fillna(median)


# # Imputer

# In[14]:


from sklearn.impute import SimpleImputer
imputer = SimpleImputer(strategy='median')

housing_num = housing.select_dtypes(include=np.number)
# print(housing_num.info())
imputer.fit(housing_num)
print(imputer.statistics_)
print(housing_num.median().values)

X = imputer.transform(housing_num)

print('Number of NaN inside housing_num :\n',np.isnan(housing_num).sum())
print('Number of NaN inside X :',np.isnan(X).sum())


# # RBF 

# In[15]:


from sklearn.metrics.pairwise import rbf_kernel

age_simil_35 = rbf_kernel(
    housing[['housing_median_age']],
    [[35]], 
    gamma=0.1
)


# In[16]:


from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
model = LinearRegression()
target_scaler = StandardScaler()

scaled_labels = target_scaler.fit_transform(housing_labels.to_frame())

model.fit(housing[['median_income']], scaled_labels)

new_data = np.array([[25000.0], [22000.0], [23000.0], [21000.0]], dtype=float)

scaled_predictions = model.predict(new_data)

predictions = target_scaler.inverse_transform(scaled_predictions)
print(predictions)


# # Transformed Target Regressor

# In[17]:


from sklearn.compose import TransformedTargetRegressor

TTRmodel = TransformedTargetRegressor(regressor=LinearRegression(), transformer=StandardScaler())

TTRmodel.fit(
    housing[['median_income']],
    housing_labels
)

new_data = pd.DataFrame(
    new_data,
    columns=['median_income']
)

TTRpred = TTRmodel.predict(new_data)
print(TTRpred)


# # Custom Transformer

# In[18]:


from sklearn.preprocessing import FunctionTransformer

log_transformer = FunctionTransformer(
    func=np.log,
    inverse_func=np.exp
)


# # RBF using Function Transformer

# for 1 Feature

# In[19]:


rbf_transformer = FunctionTransformer(
    func=rbf_kernel,
    kw_args=dict(   
        Y=[[35.0]], # y= reference point, like 35 theke koto kom/beshi
        gamma=0.1
    )
)
""" *args → arguments → positional arguments
**kwargs → keyword arguments → নাম দিয়ে দেওয়া arguments """
age_simil_35 = rbf_transformer.transform(housing[['housing_median_age']])


# For 2 Features

# In[20]:


san_francisco_coords = 37.7749, -122.41

san_francisco_transformer = FunctionTransformer(
    func=rbf_kernel,
    kw_args= dict(
        Y=[san_francisco_coords],
        gamma=0.1
    )
)

similarity_to_sf = san_francisco_transformer.transform(housing[['latitude', 'longitude']])

similarity_to_sf


# In[21]:


print(X.shape)


# # Custom Transformer

# In[22]:


from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.utils.validation import check_array, check_is_fitted

class StandardScalerClone(BaseEstimator, TransformerMixin):
    def __init__(self, with_mean=True):
        self.with_mean = with_mean

    def fit(self,X, y=None):
        X = check_array(X)
        self.mean_ = X.mean(axis=0)
        self.scale_ = X.std(axis=0)
        self.n_features_in_ = X.shape[1]
        return self

    def transform(self,X):
        check_is_fitted(self)
        X = check_array(X)
        assert self.n_features_in_ == X.shape[1]

        if self.with_mean:
            X -= self.mean_
            return X / self.scale_ # standardization = (X - u) / sigma



# In[23]:


x = 5
assert x == 5


# # Cluster Clone

# In[24]:


from sklearn.cluster import KMeans

class ClusterSimilarity(BaseEstimator, TransformerMixin):
    def __init__(self, n_clusters=10, gamma=1.0, random_state=None):
        self.n_clusters = n_clusters
        self.gamma = gamma
        self.random_state = random_state

    def fit(self, X, y=None, sample_weight=None):
        self.kmeans_ = KMeans(
            self.n_clusters, random_state=self.random_state
        )
        self.kmeans_.fit(X,sample_weight=sample_weight)
        return self

    def transform(self,X):
        return rbf_kernel(X, self.kmeans_.cluster_centers_, gamma=self.gamma)

    def get_feature_names_out(self, names=None):
        return [f"Cluster {i} similarity" for i in range(1,self.n_clusters+1)]



cluster_sim = ClusterSimilarity(
    n_clusters=10,
    gamma=1.0,
    random_state=42
)


similarities = cluster_sim.fit_transform(housing[['latitude', 'longitude']], 
                                         sample_weight=housing_labels)

print(similarities[:3].round(2))

housing["Max cluster similarity"] = similarities.max(axis=1)

housing.plot(
    kind="scatter", x="longitude", y="latitude",
    s=housing["population"] / 100, label="population",
    c="Max cluster similarity",
    figsize=(10, 7),
    legend=True,
    cmap="jet",
    colorbar=True,
    sharex=False
)

plt.plot(cluster_sim.kmeans_.cluster_centers_[:, 1],
         cluster_sim.kmeans_.cluster_centers_[:, 0],
         linestyle="", color="black", marker="X", markersize=15,
         label="Cluster centers")

plt.legend(loc="upper right")
plt.show()
housing = housing.drop('Max cluster similarity', axis=1, inplace= True)


# # Transformation Pipelines

# In[25]:


import sklearn
from sklearn.pipeline import Pipeline
sklearn.set_config(display="diagram")
num_pipeline = Pipeline([
("impute", SimpleImputer(strategy="median")),
("standardize", StandardScaler()),
])

# num_pipeline
housing_num_prepared = num_pipeline.fit_transform(housing_num)
print(housing_num_prepared[:2].round(2))

df_housing_num_prepared = pd.DataFrame(
housing_num_prepared,
columns=num_pipeline.get_feature_names_out(),
index=housing_num.index)

# print(df_housing_num_prepared)
print(num_pipeline[1])
num_pipeline[1] 


# In[26]:


from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder

# আমাদের ধরে নেওয়া dataset-এর columns:
# age, income, city, gender

# =========================================================
# 1. "drop" → column বাদ দেওয়া
# =========================================================

preprocessing_drop = ColumnTransformer([
    # age এবং income → StandardScaler দিয়ে scale হবে
    ("num", StandardScaler(), ["age", "income"]),

    # city → পুরোপুরি বাদ যাবে
    ("cat", "drop", ["city"])
])


# =========================================================
# 2. "passthrough" → column কোনো পরিবর্তন ছাড়াই রাখা
# =========================================================

preprocessing_passthrough = ColumnTransformer([
    # age এবং income → StandardScaler দিয়ে scale হবে
    ("num", StandardScaler(), ["age", "income"]),

    # city → কোনো transformation হবে না
    # যেমন আছে তেমনই থাকবে
    ("cat", "passthrough", ["city"])
])


# =========================================================
# 3. remainder="drop" → যেসব column list করা হয়নি,
#    সেগুলো default হিসেবে বাদ যাবে
# =========================================================

preprocessing_remainder_drop = ColumnTransformer(
    [
    # age এবং income → StandardScaler
    ("num", StandardScaler(), ["age", "income"]),

    # city → OneHotEncoder
    ("cat", OneHotEncoder(), ["city"])

    # gender এখানে দেওয়া হয়নি
    # তাই defaultভাবে gender বাদ যাবে
    ]
)


# =========================================================
# 4. remainder="passthrough" → যেসব column list করা হয়নি,
#    সেগুলো unchanged অবস্থায় থাকবে
# =========================================================

preprocessing_remainder_pass = ColumnTransformer(
    [
        # age এবং income → StandardScaler
        ("num", StandardScaler(), ["age", "income"]),

        # city → OneHotEncoder
        ("cat", OneHotEncoder(), ["city"])
    ],

    # gender-এর মতো unlisted columns unchanged থাকবে
    remainder="passthrough"
)


# =========================================================
# 5. remainder-এ transformer দেওয়া
# =========================================================

preprocessing_remainder_transformer = ColumnTransformer(
    [
        # age এবং income → StandardScaler
        ("num", StandardScaler(), ["age", "income"]),

        # city → OneHotEncoder
        ("cat", OneHotEncoder(), ["city"])
    ],

    # list করা হয়নি এমন columns-গুলোর ওপরও
    # StandardScaler() প্রয়োগ হবে
    remainder=StandardScaler()
)


# # Complete Pre-processing Pipeline

# In[27]:


from sklearn.pipeline import make_pipeline
from sklearn.compose import make_column_selector
def column_ratio(X):
    return X[:,[0]] / X[:,[1]]

def ratio_name(function_transformer, feature_names_in):
    return ['ratio']

def ratio_pipeline():
    return make_pipeline(
        SimpleImputer(strategy='median'),
        FunctionTransformer(
            column_ratio, feature_names_out=ratio_name
        ),
        StandardScaler()
    )

log_pipeline = make_pipeline(
    SimpleImputer(strategy='median'),
    FunctionTransformer(
        np.log, feature_names_out='one-to-one'
    ),
    StandardScaler()
)

cat_pipeline = make_pipeline(
    SimpleImputer(strategy='most_frequent'),
    OneHotEncoder(handle_unknown='ignore')
)

cluster_simil = ClusterSimilarity(
    n_clusters=10,
    gamma=1.0,
    random_state=42
)

default_num_pipeline = make_pipeline(
    SimpleImputer(strategy='median'),
    StandardScaler()
)

preprocessing = ColumnTransformer(
    [
        ('bedrooms_per_house', ratio_pipeline(), ['total_bedrooms', 'total_rooms']),
        ('rooms_per_house', ratio_pipeline(), ['total_rooms', 'households']),
        ("log", log_pipeline, ["total_bedrooms", "total_rooms",
                                "population","households", "median_income"]),
        ("geo", cluster_simil, ["latitude", "longitude"]),
        ("cat", cat_pipeline, make_column_selector(dtype_include=object))
    ],
    remainder = default_num_pipeline
)


# # Using the pipeline

# In[30]:


housing_prepared = preprocessing.fit_transform(housing)
print(housing_prepared.shape)
print(preprocessing.get_feature_names_out)


# # Training a model

# Linear Regression

# In[ ]:


from sklearn.linear_model import LinearRegression
lin_reg = make_pipeline(preprocessing, LinearRegression())
lin_reg.fit(housing, housing_labels)


# Predictions

# In[ ]:


housing_predictions = lin_reg.predict(housing)
print(housing_predictions.round(2))


# Performance metrics using RMSE

# In[ ]:


from sklearn.metrics import root_mean_squared_error

lin_mse = root_mean_squared_error(housing_labels, housing_predictions)
lin_mse


# Decision Tree Regressor

# In[ ]:


from sklearn.tree import DecisionTreeRegressor
tree_reg = make_pipeline(preprocessing, DecisionTreeRegressor(random_state=42))
tree_reg.fit(housing, housing_labels)


# In[ ]:


tree_reg_predictions = tree_reg.predict(housing)
tree_reg_rmse = root_mean_squared_error(housing_labels, tree_reg_predictions)
tree_reg_rmse


# # Better Evaluation Using Cross-Validation

# In[ ]:


from sklearn.model_selection import cross_val_score

tree_rmses = -cross_val_score(tree_reg, housing, housing_labels, cv=10, scoring='neg_root_mean_squared_error')
pd.Series(tree_rmses).describe().round(2)


# # Using Random Forest Regressor

# In[ ]:


from sklearn.ensemble import RandomForestRegressor
import os
import joblib

forest_reg = make_pipeline(preprocessing, RandomForestRegressor(n_jobs=-1,random_state=42))

forest_reg_path = 'models/forest_reg.pkl'

if os.path.exists(forest_reg_path):
    print('loading model...')
    forest_reg = joblib.load(forest_reg_path)
else:
    print('training random forest model')
    forest_rmses = -cross_val_score(forest_reg, housing, housing_labels, cv=10, scoring='neg_root_mean_squared_error')
    print("RMSE scores:", forest_rmses)
    print("Mean RMSE:", forest_rmses.mean())
    print("Std:", forest_rmses.std())

    forest_reg.fit(housing, housing_labels)
    os.makedirs('models', exist_ok=True)
    joblib.dump(forest_reg, forest_reg_path)
    print('Model Saved')


# # Fine Tuning Model

# ### ==> Grid Search

# In[ ]:


from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV
import joblib
import os

full_pipeline = Pipeline([
    ('preprocessing', preprocessing),
    ('random_forest', RandomForestRegressor(random_state=42))
])

param_grid = [
    {
        'preprocessing__geo__n_clusters': [5,8,10],
        'random_forest__max_features': [4,6,8]
    },

    {
        'preprocessing__geo__n_clusters': [10,15],
        'random_forest__max_features': [6,8,10]
    }
] # Double underscore __ দিয়ে pipeline-এর ভিতরের step-এ ঢোকা হয়।

model_path = 'models/grid_search.pkl'

if os.path.exists(model_path):
    print('Loading saved model...')
    grid_search = joblib.load(model_path)
else:
    print("Training model...")
    grid_search = GridSearchCV(full_pipeline, param_grid, cv=3, n_jobs=-1, scoring='neg_root_mean_squared_error')
    grid_search.fit(housing, housing_labels)
    os.makedirs("models", exist_ok=True)
    joblib.dump(grid_search, model_path)

    print("Model has been saved")


# In[ ]:


cv_res = pd.DataFrame(grid_search.cv_results_)
cv_res.sort_values(by="mean_test_score", ascending=False,
inplace=True)

cv_res[['params', 'mean_test_score', 'std_test_score', 'rank_test_score']].head()


# ### ==> Randomized Search

# In[ ]:


from sklearn.model_selection import RandomizedSearchCV
from scipy.stats import randint

param_distribs = {
                    'preprocessing__geo__n_clusters': randint(low=3, high=20),
                    'random_forest__max_features': randint(low=2, high=20)
                }

rnd_search_path = 'models/rnd_search.pkl'

if os.path.exists(rnd_search_path):
    print('Loading saved model')
    rnd_search = joblib.load(rnd_search_path)
else:
    print('Training Model')
    rnd_search = RandomizedSearchCV(full_pipeline, 
                                    param_distributions=param_distribs, 
                                    n_iter=10, 
                                    cv=3, 
                                    scoring='neg_root_mean_squared_error', 
                                    random_state=42, 
                                    n_jobs=-1)

    rnd_search.fit(housing, housing_labels)
    os.makedirs('models', exist_ok=True)
    joblib.dump(rnd_search, rnd_search_path)


# In[ ]:


# from sklearn.model_selection import HalvingRandomSearchCV, HalvingGridSearchCV
# # These are useful when there are low resources


# In[ ]:


final_model = rnd_search.best_estimator_
# final_model
feature_importances = final_model['random_forest'].feature_importances_
# print(feature_importances.round(2))

sorted(zip(feature_importances.round(2), final_model['preprocessing'].get_feature_names_out()), reverse=True)


# In[ ]:


X_test = strat_test_set.drop(
    ["median_house_value"],
    axis=1
)
y_test = strat_test_set['median_house_value'].copy()

final_pred = final_model.predict(X_test)

