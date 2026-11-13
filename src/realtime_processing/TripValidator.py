import pandas as pd
import re


class PreTripProcessorValidator:
    def __init__(self, df):
        self.df = df
        self.errors = []

    def run_all_validations(self):
        self.validate_column_types()
        self.check_format_compliance()
        self.verify_value_ranges()
        self.check_unique_constraints()
        self.validate_semantic_values()
        self.enforce_business_rules()
        return self.errors

    def validate_column_types(self):
        type_specifications = {
            "Trip ID": {"dtype": "int64"},
            "Destination": {"dtype": "object"},
            "Start date": {"dtype": "object", "format": "date"},
            "End date": {"dtype": "object", "format": "date"},
            "Duration (days)": {"dtype": "float64"},
            "Traveler name": {"dtype": "object"},
            "Traveler age": {"dtype": "float64"},
            "Traveler gender": {"dtype": "object", "allowed": ["Male", "Female"]},
            "Traveler nationality": {"dtype": "object"},
            "Accommodation type": {"dtype": "object"},
            "Accommodation cost": {"dtype": "object", "currency": True},
            "Transportation type": {"dtype": "object"},
            "Transportation cost": {"dtype": "object", "currency": True}
        }

        for column, specs in type_specifications.items():
            if column not in self.df.columns:
                self.errors.append(f"❌ Missing column: Required column '{column}' not found")
                continue

            actual_type = self.df[column].dtype
            if actual_type != specs["dtype"]:
                self.errors.append(
                    f"❌ Type mismatch: Column '{column}' should be {specs['dtype']}, found {actual_type}"
                )

    def check_format_compliance(self):

        # date format: MM/DD/YYYY
        date_pattern = r"^\d{1,2}/\d{1,2}/\d{4}$"
        for date_col in ["Start date", "End date"]:
            if date_col in self.df.columns:
                invalid_dates = self.df[date_col].dropna().loc[
                    lambda x: ~x.astype(str).str.match(date_pattern)
                ]
                if not invalid_dates.empty:
                    self.errors.append(
                        f"❌ Date format error: {date_col} contains {len(invalid_dates)} "
                        f"entries with invalid MM/DD/YYYY format"
                    )

        # Currency format validation (supports multiple notations)
        currency_regex = re.compile(
            r'^\s*\$?\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*(USD)?\s*$|'  # $ / USD 
            r'^\s*\$?\s*\d+\.\d{2}\s*$|'  # $1234.56
            r'^\s*\d+\s*USD\s*$|'  # 1000 USD
            r'^\s*\d+\.?\d*\s*$',  # 1500
            flags=re.IGNORECASE
        )

        for amount_col in ["Accommodation cost", "Transportation cost"]:
            if amount_col in self.df.columns:
                invalid_entries = self.df[amount_col].dropna().loc[
                    lambda x: x.apply(
                        lambda val: not currency_regex.fullmatch(str(val))
                        if not pd.api.types.is_number(val)
                        else False
                    )
                ]

                if not invalid_entries.empty:
                    sample_errors = invalid_entries.head(3).astype(str).tolist()
                    self.errors.append(
                        f"❌ Currency format error: {amount_col} has {len(invalid_entries)} invalid entries\n"
                        # f"   - Valid formats: $1,234.56 / 1234.56 USD / 1500\n"
                        f"   - Found errors: {', '.join(sample_errors)}"
                    )

    def verify_value_ranges(self):
        # 18 < Age < 100
        if "Traveler age" in self.df.columns:
            invalid_ages = self.df[
                (self.df["Traveler age"].notna()) &
                ((self.df["Traveler age"] < 18) |
                 (self.df["Traveler age"] > 100))
            ]
            if not invalid_ages.empty:
                self.errors.append(
                    f"❌ Age range violation: Traveler age should be 18-100 years, "
                    f"found {len(invalid_ages)} outliers"
                )

            # duration > 0
            if "Duration (days)" in self.df.columns:
                invalid_durations = self.df[
                    self.df["Duration (days)"].notna() &
                    (self.df["Duration (days)"] <= 0)
                    ]
            if not invalid_durations.empty:
                self.errors.append(
                    f"❌ Duration error: Trip duration must be positive,"
                    f"found {len(invalid_durations)} invalid entries"
                )

    def check_unique_constraints(self):
        # Trip ID uniqueness
        if "Trip ID" in self.df.columns:
            duplicate_ids = self.df[self.df.duplicated("Trip ID", keep=False)]
            if not duplicate_ids.empty:
                self.errors.append(
                    f"❌ Duplicate records: Found {len(duplicate_ids)} "
                    f"entries with duplicate Trip IDs"
                )

    def validate_semantic_values(self):
        # Gender [male/female]
        if "Traveler gender" in self.df.columns:
            invalid_genders = self.df[
                ~self.df["Traveler gender"].isin(["Male", "Female"])
            ]
            if not invalid_genders.empty:
                self.errors.append(
                    f"❌ Gender validation: Found {len(invalid_genders)} "
                    # f"entries with invalid gender values (allowed: Male/Female)"
                )

    def enforce_business_rules(self):
        # The end date must be after the start date
        if {"Start date", "End date"}.issubset(self.df.columns):
            try:
                start_dates = pd.to_datetime(self.df["Start date"], errors="coerce")
                end_dates = pd.to_datetime(self.df["End date"], errors="coerce")
                invalid_periods = self.df[end_dates <= start_dates]
                if not invalid_periods.empty:
                    self.errors.append(
                        f"❌ Date logic error: End date must be after start date, "
                        f"found {len(invalid_periods)} violations"
                    )
            except Exception as e:
                pass  # Format errors already handled elsewhere

        # Accommodation price range (I assume those are reasonable price range)
        price_guidelines = {
            "Hotel": (50, 3000),
            "Hostel": (20, 1000),
            "Airbnb": (30, 2000),
            "Resort": (100, 10000)
        }

        if {"Accommodation type", "Accommodation cost"}.issubset(self.df.columns):
            # Clean currency values
            price_series = pd.to_numeric(
                self.df["Accommodation cost"].astype(str).str.replace(r"[^\d.]", "", regex=True),
                errors="coerce"
            )

            for property_type, (min_price, max_price) in price_guidelines.items():
                type_mask = self.df["Accommodation type"] == property_type
                price_mask = ~price_series.between(min_price, max_price)

                invalid_prices = self.df[type_mask & price_series.notna() & price_mask]
                if not invalid_prices.empty:
                    sample_values = invalid_prices["Accommodation cost"].head(3).tolist()
                    self.errors.append(
                        f"❌ Price policy violation: {property_type} rates should be "
                        f"${min_price}-${max_price}\n"
                        f"   - Found {len(invalid_prices)} exceptions (e.g.: {sample_values})"
                    )

class PostTripProcessorValidator:
    def __init__(self, df):
        self.df = df
        self.errors = []

    def run_all_validations(self):
        self.validate_no_missing_fields()
        self.check_total_cost()
        self.verify_cost_per_day()
        self.validate_age_group_assignment()
        self.validate_season_assignment()
        self.verify_unique_trip_ids()
        return self.errors

    def validate_no_missing_fields(self):
        critical_fields = [
            "Trip ID", "Traveler name", "Traveler age", "Traveler gender",
            "Destination", "Start date", "End date", "Total cost", "Duration (days)"
        ]
        missing_columns = [col for col in critical_fields if col not in self.df.columns]
        if missing_columns:
            self.errors.append(f"❌ Missing critical columns: {', '.join(missing_columns)}")
            return  # no need to check missing values if columns missing

        missing_data = self.df[critical_fields].isnull().sum()
        for col, missing_count in missing_data.items():
            if missing_count > 0:
                self.errors.append(
                    f"❌ Missing data: Column '{col}' has {missing_count} missing entries"
                )

    def check_total_cost(self):
        if {"Accommodation cost", "Transportation cost", "Total cost"}.issubset(self.df.columns):
            # Clean and convert all relevant columns to numeric
            def clean_cost(series):
                return pd.to_numeric(series.astype(str).str.replace(r"[^\d.]", "", regex=True), errors="coerce")

            accom = clean_cost(self.df["Accommodation cost"])
            transport = clean_cost(self.df["Transportation cost"])
            total = clean_cost(self.df["Total cost"])

            calc_total = accom.fillna(0) + transport.fillna(0)
            mismatch = (total - calc_total).abs() > 0.01  # Allow small rounding tolerance
            if mismatch.any():
                self.errors.append(
                    f"❌ Total cost mismatch: Found {mismatch.sum()} rows where total cost calculation is wrong"
                )

    def verify_cost_per_day(self):
        if {"Total cost", "Duration (days)", "Cost per day"}.issubset(self.df.columns):
            # Ensure 'Duration (days)' is not zero or NaN before dividing
            self.df["Duration (days)"] = pd.to_numeric(self.df["Duration (days)"], errors="coerce")
            self.df["Total cost"] = pd.to_numeric(self.df["Total cost"], errors="coerce")
            valid_duration = self.df["Duration (days)"] > 0
            calc_cost_per_day = self.df["Total cost"] / self.df["Duration (days)"]
            calc_cost_per_day[~valid_duration] = 0  # Set cost per day to 0 where duration is invalid

            mismatch = (self.df["Cost per day"] - calc_cost_per_day).abs() > 0.01
            if mismatch.any():
                self.errors.append(
                    f"❌ Cost per day mismatch: Found {mismatch.sum()} rows with incorrect cost/day values"
                )

    def validate_age_group_assignment(self):
        if {"Traveler age", "Age group"}.issubset(self.df.columns):
            age_groups = {
                'Child': (0, 17),
                'Young Adult': (18, 29),
                'Adult': (30, 59),
                'Senior': (60, 120)  # Assume 120 as max age
            }
            invalid_rows = 0
            for idx, row in self.df.iterrows():
                age = row["Traveler age"]
                group = row["Age group"]
                if pd.notnull(age) and pd.notnull(group):
                    for grp, (min_age, max_age) in age_groups.items():
                        if group == grp and not (min_age <= age <= max_age):
                            invalid_rows += 1
                            break
            if invalid_rows > 0:
                self.errors.append(
                    f"❌ Age group assignment error: {invalid_rows} travelers have incorrect age groups"
                )

    def validate_season_assignment(self):
        if {"Start date", "Season"}.issubset(self.df.columns):
            valid_seasons = {"Winter", "Spring", "Summer", "Fall"}
            invalid_seasons = self.df[~self.df["Season"].isin(valid_seasons)]
            if not invalid_seasons.empty:
                self.errors.append(
                    f"❌ Invalid season entries: Found {len(invalid_seasons)} invalid season values"
                )

    def verify_unique_trip_ids(self):
        if "Trip ID" in self.df.columns:
            duplicate_ids = self.df[self.df.duplicated("Trip ID", keep=False)]
            if not duplicate_ids.empty:
                self.errors.append(
                    f"❌ Duplicate Trip IDs: Found {len(duplicate_ids)} duplicated Trip ID entries"
                )