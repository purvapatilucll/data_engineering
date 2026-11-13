import pandas as pd
import numpy as np

class NashvilleProcessor:
    def __init__(self, df):
        self.df = df.copy()

    def handle_missing_values(self):
        non_mandatory = [
            'Suite/ Condo   #',
            'Owner Name',
            'Address',
            'City',
            'State',
            'Tax District',
            'image',
            'Foundation Type',
            'Exterior Wall',
            'Grade'
        ]
        mandatory = [col for col in self.df.columns if col not in non_mandatory]
        self.df = self.df.dropna(subset=mandatory)
        return self

    def remove_columns(self):
        self.df.columns = self.df.columns.str.strip()
        columns_to_drop = ['image', 'Sold As Vacant', 'Multiple Parcels Involved in Sale']
        # important: have to add columns= !!!
        self.df = self.df.drop(columns=columns_to_drop)
        return self

    def add_columns(self):
        self._add_price_per_sqft()
        self._add_sale_year_month()
        self._add_age_of_property()
        self._add_land_building_ratio()
        self._add_price_category()
        self._add_owner_names()
        return self

    # assume reasonable area between(50, 10000), can use "# print((df['Finished Area'] >= 10000).sum())" check
    def _add_price_per_sqft(self):
        self.df['Price per square foot'] = (self.df['Sale Price'] / self.df['Finished Area']).where(
            self.df['Finished Area'].between(50, 10000, inclusive='neither'))

    def _add_age_of_property(self):
        current_year = pd.Timestamp.now().year
        self.df['Age of property'] = np.where(
            self.df['Year Built'] <= current_year,
            current_year - self.df['Year Built'],
            np.nan)

    def _add_sale_year_month(self):
        self.df['Year'] = pd.to_datetime(self.df['Sale Date']).dt.year
        self.df['Month'] = pd.to_datetime(self.df['Sale Date']).dt.month

    # value ratio = land value / building value
    def _add_land_building_ratio(self):
        self.df['Land-to-building value ratio'] = np.where(
            self.df['Building Value'] > 0,
            self.df['Land Value'] / self.df['Building Value'],
            np.nan
        )

    def _add_price_category(self):
        self.df['price_category'] = pd.cut(
            self.df['Sale Price'],
            bins=[0, 100_000, 300_000, np.inf],
            labels=['Low', 'Medium', 'High'],
            right=False,  # 左闭右开区间 [low, high)
            ordered=True,  # 分类有序
            duplicates='raise'  # 确保区间无重复
        )

    def _add_owner_names(self):
        company_keywords = ['LLC', 'L.L.C', 'INC', 'INC.', 'CO', 'CORP', 'CORPORATION', 'LTD', 'LP', 'TRUST', 'BANK', 'GROUP']

        companies = (
            self.df['Owner Name']
            .str.upper()
            .str.contains('|'.join(company_keywords), na=False)
            # = .str.contains('LLC|INC|CO|CORP.....', na=False)
        )

        # first owners separate by（ ; or & ）
        # example: "Smith, John & Lee, Amy" →   Smith, John[0]   Lee, Amy[1]
        first_owners = (
            self.df['Owner Name']
            .str.split(r'[;&]', n=1, expand=True)[0]
            .str.strip()
            .fillna('') # if data missing, shows ''
        )

        # split name to first - last name by ','
        # example: Smith[0]  John[1] both need use strip() , but we could use \s* as well
        split_names = first_owners.str.split(r"\s*,\s*", n=1, expand=True)

        # if company → family name is company name
        self.df['Family Name'] = np.where(
            companies,
            first_owners,
            split_names[0]
        )

        # if company → first name is none
        self.df['First Name'] = np.where(
            companies,
            np.nan,
            split_names[1]
        )

        # name without comma: ("John Smith"）
        name_without_comma = ~companies & split_names[1].isnull()
                             # ~companies == not companies; split_names[1].isnull() == no comma
        split_no_comma = (
            first_owners[name_without_comma]
            .str.rsplit(n=1, expand=True)  # split by right side( "Mary Ann Garcia" → "Mary Ann"  "Graica")
            .fillna('')
        )
        self.df.loc[name_without_comma, 'Family Name'] = split_no_comma[1]
        self.df.loc[name_without_comma, 'First Name'] = split_no_comma[0]

        # replace '' to NaN (because of .fillna(''))
        self.df['Family Name'] = self.df['Family Name'].replace('', np.nan)
        self.df['First Name'] = self.df['First Name'].replace('', np.nan)

# --------------------------------- clean invalid data though validator --------------------------------------

    # delete Parcel ID, Legal Reference, Parcel ID + Sale Date duplicates(repeat)
    def _remove_duplicates(self):
        self.df = self.df.drop_duplicates(subset=['Parcel ID'], keep='first')
        self.df = self.df.drop_duplicates(subset=['Legal Reference'], keep='first')
        self.df = self.df.drop_duplicates(subset=['Parcel ID', 'Sale Date'], keep='first')
        return self

    # filter the rows(Year Built <= Sale Date)
    def _fix_year_built(self):
        self.df['Sale Date'] = pd.to_datetime(
            self.df['Sale Date'],
        )
        sale_year = self.df['Sale Date'].dt.year
        is_year_valid = self.df['Year Built'] <= sale_year
        # only get rows which <= sale_year

        self.df = self.df[is_year_valid]
        return self

# ------------------------------------------------------------------------------------------------------------

    def run_all_processors(self):
        return (
            self
            .handle_missing_values()
            .remove_columns()
            ._remove_duplicates()
            ._fix_year_built()
            .add_columns()
        )

    # result = NashvilleProcessor(df).get_processed_data()
    def get_processed_data(self):
        return self.df.copy()