import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score
import joblib

# Load data
df = pd.read_csv('data/loan_data.csv')
TARGET = 'Loan_Status'

# Features
cat_features = ['Gender','Married','Dependents','Education','Self_Employed','Property_Area']
num_features = ['ApplicantIncome','CoapplicantIncome','LoanAmount','Loan_Amount_Term','Credit_History']

X = df[cat_features + num_features]
y = df[TARGET].map({'Y':0,'N':1})  # 1=default

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

num_pipe = Pipeline([('imputer', SimpleImputer(strategy='median')), ('scaler', StandardScaler())])
cat_pipe = Pipeline([('imputer', SimpleImputer(strategy='constant', fill_value='Missing')), ('ohe', OneHotEncoder(handle_unknown='ignore'))])
preprocessor = ColumnTransformer([('num', num_pipe, num_features), ('cat', cat_pipe, cat_features)])

model = Pipeline([('preprocessor', preprocessor), ('clf', RandomForestClassifier(n_estimators=200, class_weight='balanced', random_state=42))])
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
y_proba = model.predict_proba(X_test)[:,1]
print(classification_report(y_test, y_pred))
print('ROC-AUC:', roc_auc_score(y_test, y_proba))

# Save model
joblib.dump(model, 'models/pipeline.joblib')
