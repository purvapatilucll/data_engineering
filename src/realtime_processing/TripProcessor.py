import pandas as pd
import numpy as np
import re

class TripProcessor:
    def __init__(self, df):
        self.df = df.copy()

    @staticmethod
    def normalize_to_dollar_format(value: str) -> float | None:
        try:
            currency_regex = re.compile(
                r'^\s*\$?\s*\d{1,3}(?:,\d{3})?(?:\.\d{2})?\s*(USD)?\s*$|'  # $ / USD 
                r'^\s*\$?\s*\d+\.\d{2}\s*$|'  # $1234.56
                r'^\s*\d+\s*USD\s*$|'         # 1000 USD
                r'^\s*\d+\.?\d*\s*$',         # 1500
                flags=re.IGNORECASE
            )
            val = str(value).strip()
            if not val or not currency_regex.fullmatch(val):
                return np.nan
            val = re.sub(r'[^\d.]', '', val)
            return float(val)
        except Exception:
            return np.nan

    def clean_cost_columns(self):
        cost_columns = ['Accommodation cost', 'Transportation cost']
        
        for col in cost_columns:
            if col in self.df.columns:
                self.df[col] = self.df[col].apply(self.normalize_to_dollar_format)
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0)

        return self

    def add_total_cost(self):
        if 'Accommodation cost' in self.df.columns and 'Transportation cost' in self.df.columns:
            self.df["Total cost"] = (
                self.df["Accommodation cost"] +
                self.df["Transportation cost"]
            ).fillna(0)
        else:
            self.df["Total cost"] = np.nan

        return self



    def add_cost_per_day(self):
        if 'Total cost' not in self.df.columns:
            raise KeyError("'Total cost' column is missing. Please run 'add_total_cost()' first.")
        self.df["Duration (days)"] = pd.to_numeric(self.df["Duration (days)"], errors="coerce")
        self.df["Cost per day"] = self.df["Total cost"] / self.df["Duration (days)"]
        return self

    def add_season(self):
        self.df['Start date'] = pd.to_datetime(self.df['Start date'], errors='coerce')
        season_mapping = {
            (12, 1, 2): 'Winter',
            (3, 4, 5): 'Spring',
            (6, 7, 8): 'Summer',
            (9, 10, 11): 'Fall'
        }

        def month_to_season(month):
            for months, season in season_mapping.items():
                if month in months:
                    return season
            return np.nan

        self.df['Season'] = self.df['Start date'].dt.month.map(month_to_season)
        return self

    def add_age_group(self):
        bins = [0, 17, 29, 59, 120]
        labels = ['Child', 'Young Adult', 'Adult', 'Senior']
        self.df['Age group'] = pd.cut(self.df["Traveler age"], bins=bins, labels=labels, right=True)
        return self

    def normalize_gender(self):
        gender_map = {
            'M': 'Male', 'MALE': 'Male', 'male': 'Male', 'm': 'Male',
            'F': 'Female', 'FEMALE': 'Female', 'female': 'Female', 'f': 'Female'
        }
        if "Traveler gender" in self.df.columns:
            self.df["Traveler gender"] = self.df["Traveler gender"].str.strip().map(lambda x: gender_map.get(str(x), x))
        return self

    def remove_duplicates(self):
        self.df = self.df.drop_duplicates(subset='Trip ID', keep='first')
        return self

    def drop_missing_fields(self):
        critical_fields = [
            "Trip ID", "Traveler name", "Traveler age", "Traveler gender",
            "Destination", "Start date", "End date", "Duration (days)"
        ]
        self.df.dropna(subset=critical_fields, inplace=True)
        return self

    def format_cost_columns(self):
        cost_columns = ['Accommodation cost', 'Transportation cost', 'Total cost', 'Cost per day']
        for col in cost_columns:
            if col in self.df.columns and pd.api.types.is_numeric_dtype(self.df[col]):
                self.df[col] = self.df[col].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else "")
        return self

    def run_all_processors(self):
        return (
            self
            .remove_duplicates()
            .clean_cost_columns()
            .normalize_gender()
            .add_total_cost()
            .add_cost_per_day()
            .add_age_group()
            .add_season()
            .drop_missing_fields()
        )


    def get_processed_data(self):
        return self.df.copy()
