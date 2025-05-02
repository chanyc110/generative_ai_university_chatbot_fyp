import os
import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier
import joblib

# Update the file path to where your CSV file is located
file_path = "MOCK_DATA.csv"

# Ensure the file exists
if not os.path.exists(file_path):
    raise FileNotFoundError(f"File not found at {file_path}. Please check the file path.")

# Load the dataset
df = pd.read_csv(file_path)

# Clean the data by stripping extra whitespace from all string columns
for col in df.select_dtypes(include=['object']).columns:
    df[col] = df[col].str.strip()

# Define features and target
X = df[['MathsAptitude', 'Interest', 'HighestQualification', 'ComputerScienceRelated']]
y = df['Course']

# Preprocessing: Use OneHotEncoder for the categorical features
preprocessor = ColumnTransformer(
    transformers=[
        ('cat', OneHotEncoder(handle_unknown='ignore'), ['MathsAptitude', 'Interest', 'HighestQualification', 'ComputerScienceRelated'])
    ]
)

# Build a pipeline that first preprocesses the data, then fits the RandomForestClassifier
pipeline = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('classifier', RandomForestClassifier(random_state=42))
])
# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Define a parameter grid to search over different values for n_estimators (random forest)
param_grid = {
    'classifier__n_estimators': [50, 100, 200, 300, 400, 500]
}

# Set up the GridSearchCV with 5-fold cross-validation
grid_search = GridSearchCV(pipeline, param_grid, cv=5, scoring='accuracy')

# Fit GridSearchCV to the training data
grid_search.fit(X_train, y_train)

# Output the best parameter and corresponding score
print("Best parameters:", grid_search.best_params_)
print("Best cross-validation accuracy:", grid_search.best_score_)

# Evaluate the optimized model on the test set
optimized_model = grid_search.best_estimator_
test_accuracy = optimized_model.score(X_test, y_test)
print("Test accuracy of optimized model:", test_accuracy)


# Define your own input values in a dictionary. Ensure the keys match the feature names.
new_input = {
    "MathsAptitude": ["medium"],               # e.g., "low", "medium", or "high"
    "Interest": ["research and advanced studies"],                      # e.g., "General computer science", "AI", "research and advanced studies"
    "HighestQualification": ["degree"],     # e.g., "high school", "college", "diploma", "degree"
    "ComputerScienceRelated": ["Yes"]        # e.g., "Yes" or "No"
}

# Convert the dictionary to a DataFrame
new_df = pd.DataFrame(new_input)

# Use the optimized model to predict the course and the probability distribution
predicted_course = optimized_model.predict(new_df)[0]
predicted_probabilities = optimized_model.predict_proba(new_df)[0]
classes = optimized_model.named_steps['classifier'].classes_

print("Predicted course:", predicted_course)
print("Percentage match for each course:")
for course, prob in zip(classes, predicted_probabilities):
    print(f"{course}: {prob * 100:.2f}%")

joblib.dump(optimized_model, "course_recommendation_model.pkl")
print("Model saved successfully!")
