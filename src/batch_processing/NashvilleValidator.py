import pandas as pd

class PreProcessorValidator:

    def __init__(self, df):
        self.df = df
        self.errors = []

    # ignore null values, only validate exiting values

    def run_all_validations(self):
        self.validate_format()
        self.validate_uniqueness()
        self.validate_data_type()
        self.validate_semantic_consistency()
        self.validate_referential_integrity()

    def validate_format(self):

        if 'Parcel ID' in self.df.columns:
            parcel_pattern = r'\d{3} \d{2} \w{1,2} \d{3}\.\d{2}'
            invalid_parcels = self.df[
                self.df['Parcel ID'].notna() &
                ~self.df['Parcel ID'].astype(str).str.match(parcel_pattern)
            ].index
            if len(invalid_parcels) > 0:
                self.errors.append(f"Some Parcel IDs are in an invalid format at index: {invalid_parcels.tolist()}")

        if 'Sale Date' in self.df.columns:
            invalid_dates = self.df[
                self.df['Sale Date'].notna() &
                pd.to_datetime(self.df['Sale Date'], errors='coerce').isna()
            ].index
            if len(invalid_dates) > 0:
                self.errors.append(f"Some Sale Dates are in an invalid format at index: {invalid_dates.tolist()}")

    def validate_uniqueness(self):

        # i deleted "Parcel ID".dropna() because parcel id can repeat

        # 每次销售应该有唯一编号 should be unique per sale
        if 'Legal Reference' in self.df.columns:
            legal_refs = self.df['Legal Reference'].dropna()
            if legal_refs.duplicated().any():
                self.errors.append("Duplicate Legal References found.")

        # 每块地每天只售一次 shouldn't repeat since A parcel might be sold multiple times, but not more than once on the same day
        if {'Parcel ID', 'Sale Date'}.issubset(self.df.columns):
            combined = self.df[['Parcel ID', 'Sale Date']].dropna()
            if combined.duplicated().any():
                self.errors.append("Duplicate Parcel ID and Sale Date combinations found.")

    def validate_data_type(self):
        expected_types = {
            'Unnamed: 0.1': 'int64',
            'Unnamed: 0': 'int64',
            'Parcel ID': 'object',
            'Land Use': 'object',
            'Property Address': 'object',
            'Suite/ Condo   #': 'object',
            'Property City': 'object',
            'Sale Date': 'datetime64[ns]', #not sure abt this datatype
            'Sale Price': 'int64',
            'Legal Reference': 'object',
            'Sold As Vacant': 'object',
            'Multiple Parcels Involved in Sale': 'object',
            'Owner Name': 'object',
            'Address': 'object',
            'City': 'object',
            'State': 'object',
            'Acreage': 'float64',
            'Tax District': 'object',
            'Neighborhood': 'float64',
            'image': 'object',
            'Land Value': 'float64',
            'Building Value': 'float64',
            'Total Value': 'float64',
            'Finished Area': 'float64',
            'Foundation Type': 'object',
            'Year Built': 'float64',
            'Exterior Wall': 'object',
            'Grade': 'object',
            'Bedrooms': 'float64',
            'Full Bath': 'float64',
            'Half Bath': 'float64'
        }

        if 'Sale Date' in self.df.columns:
            self.df['Sale Date'] = pd.to_datetime(self.df['Sale Date'], errors='coerce')

        for col, expected_dtype in expected_types.items():
            if col in self.df.columns:
                non_null_series = self.df[col].dropna()
                if not non_null_series.empty and str(non_null_series.dtype) != expected_dtype:
                    self.errors.append(f"Column '{col}' expected {expected_dtype} but got {non_null_series.dtype}")

    def validate_semantic_consistency(self):
        #Total Value should be >= Land Value + Building Value
        if {'Total Value', 'Land Value', 'Building Value'}.issubset(self.df.columns):
            inconsistent_value_rows = self.df[
                self.df['Total Value'].notna() &
                self.df['Land Value'].notna() &
                self.df['Building Value'].notna() &
                (self.df['Total Value'] < self.df['Land Value'] + self.df['Building Value'])
            ].index
            if not inconsistent_value_rows.empty:
                self.errors.append(
                    f"Total Value is less than Land + Building Value at index: {inconsistent_value_rows.tolist()}"
                )

        #Year Built should not be after Sale Date year
        if {'Year Built', 'Sale Date'}.issubset(self.df.columns):
            sale_dates = pd.to_datetime(self.df['Sale Date'], errors='coerce')
            invalid_years = self.df[
                self.df['Year Built'].notna() &
                sale_dates.notna() &
                (self.df['Year Built'] > sale_dates.dt.year)
            ].index
            if not invalid_years.empty:
                self.errors.append(f"Year Built is after Sale Date at index: {invalid_years.tolist()}")

        #Finished Area should be positive
        if 'Finished Area' in self.df.columns:
            invalid_area = self.df[
                self.df['Finished Area'].notna() &
                (self.df['Finished Area'] <= 0)
            ].index
            if not invalid_area.empty:
                self.errors.append(f"Finished Area must be greater than 0 at index: {invalid_area.tolist()}")

    def validate_referential_integrity(self):
        #Sold As Vacant should only be 'Yes' or 'No'
        if 'Sold As Vacant' in self.df.columns:
            invalid_vacant = self.df[
                self.df['Sold As Vacant'].notna() &
                ~self.df['Sold As Vacant'].isin(['Yes', 'No'])
            ].index
            if not invalid_vacant.empty:
                self.errors.append(f"'Sold As Vacant' contains invalid values at index: {invalid_vacant.tolist()}")

        #Multiple Parcels Involved in Sale should only be 'Yes' or 'No'
        if 'Multiple Parcels Involved in Sale' in self.df.columns:
            invalid_parcels = self.df[
                self.df['Multiple Parcels Involved in Sale'].notna() &
                ~self.df['Multiple Parcels Involved in Sale'].isin(['Yes', 'No'])
            ].index
            if not invalid_parcels.empty:
                self.errors.append(f"'Multiple Parcels Involved in Sale' contains invalid values at index: {invalid_parcels.tolist()}")


class PostProcessorValidator:

    def __init__(self, df):
        self.df = df
        self.errors = []

    def run_all_validations(self):
        self.validate_mandatory_columns()
        self.validate_removed_columns()
        self.validate_new_columns()
        self.validate_business_rules()

    def validate_mandatory_columns(self):

        mandatory_cols = [
            'Parcel ID', 'Land Use', 'Property Address',
            'Property City', 'Sale Date', 'Sale Price',
            'Legal Reference'
        ]
        for col in mandatory_cols:
            if col in self.df.columns and self.df[col].isna().any():
                self.errors.append(f"Missing values in mandatory column: {col}")

    def validate_removed_columns(self):

        forbidden_cols = ['image', 'Sold As Vacant', 'Multiple Parcels Involved in Sale']
        for col in forbidden_cols:
            if col in self.df.columns:
                self.errors.append(f"Column {col} was not removed")

    def validate_new_columns(self):

        required_new_cols = [
            'Price per square foot',
            'Age of property',
            'Year',
            'Month',
            'Land-to-building value ratio',
            'price_category',
            'Family Name',
            'First Name'
        ]
        for col in required_new_cols:
            if col not in self.df.columns:
                self.errors.append(f"Missing new column: {col}")

    def validate_business_rules(self):

        if 'price_category' in self.df.columns:
            valid_cats = ['Low', 'Medium', 'High']
            invalid = self.df[~self.df['price_category'].isin(valid_cats)]
            if not invalid.empty:
                self.errors.append(f"Invalid price categories at index: {invalid.index.tolist()}")

        if 'Age of property' in self.df.columns:
            invalid_age = self.df[self.df['Age of property'] < 0]
            if not invalid_age.empty:
                self.errors.append(f"Negative property age at index: {invalid_age.index.tolist()}")
