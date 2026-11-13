## Project Context
Academic team project developed at UCLL in collaboration with ['Purva Patil', 'Shulin Xu'].

## VALIDATION RULES
## Batch Processing (Nashville dataset)
## ✅ Pre-Processing Validation Rules

### 🔹 Format Validation
- **Parcel ID** must follow the pattern: `\d{3} \d{2} \w{1,2} \d{3}\.\d{2}`  
  _Example: `105 03 0D 008.00`_
- **Sale Date** must be in a valid datetime format

---

### 🔹 Uniqueness
- **Legal Reference** must be **unique**
- A combination of **Parcel ID** and **Sale Date** must be **unique**  
  _A parcel can be sold multiple times, but not more than once on the same date._

---

### 🔹 Data Type Validation
- Validate non-null entries only.
- Expected types (examples):
  - `Sale Price`: `int64`
  - `Sale Date`: `datetime64[ns]`
  - `Finished Area`: `float64`
  - `Year Built`: `float64`

---

### 🔹 Semantic Validations
- **Total Value** must be ≥ **Land Value** + **Building Value**
- **Year Built** should not be after **Sale Date**
- **Finished Area** should be positive
---

### 🔹 Referential Integrity
- **Sold As Vacant** must be either `'Yes'` or `'No'`
- **Multiple Parcels Involved in Sale** must be either `'Yes'` or `'No'`

---

## ✅ Post-Processing Validation Rules

### 🔹 Mandatory Columns
Must exist and contain no missing values:
- `Parcel ID`
- `Land Use`
- `Property Address`
- `Property City`
- `Sale Date`
- `Sale Price`
- `Legal Reference`

---

### 🔹 Removed Columns
These columns must be removed:
- `image`
- `Sold As Vacant`
- `Multiple Parcels Involved in Sale`

---

### 🔹 New Columns
These new columns must be added:
- `Price per square foot`
- `Age of property`
- `Year`
- `Month`
- `Land-to-building value ratio`
- `price_category`
- `Family Name`
- `First Name`

---

### 🔹 Business Rule Checks
- `price_category` must be one of: `'Low'`, `'Medium'`, `'High'`
- `Age of property` must be **0 or greater**

# Real Time Processing (Traveler trip dataset)
## ✅ Pre-Processing Validation Rules

### 🔹 Data Type Validation
Validate non-null entries only. Expected types:
- `Trip ID`: `int64`
- `Destination`: `object`
- `Start date`, `End date`: `object` (parse as date)
- `Duration (days)`: `float64`
- `Traveler name`: `object`
- `Traveler age`: `float64`
- `Traveler gender`: `object` _(allowed: `Male`, `Female`)_
- `Traveler nationality`: `object`
- `Accommodation type`: `object`
- `Accommodation cost`: `object` _(currency format)_
- `Transportation type`: `object`
- `Transportation cost`: `object` _(currency format)_

---

### 🔹 Format Validation

- **Start date** and **End date** must be in `MM/DD/YYYY` format  
  _Example: `5/1/2023`_

- **Accommodation cost** and **Transportation cost** must follow any of these valid currency formats:  
  - `$1,234.56`  
  - `1234.56 USD`  
  - `1000 USD`  
  - `1500`  
  - `$1234.56`  
  - `  $ 1,000.00 USD  ` _(with optional spaces and currency symbol)_

### 🔹 Range & Logic Checks
- `Traveler age` must be between **18 and 100**
- `Duration (days)` must be **greater than 0**
- `End date` must be **after** `Start date`

---

### 🔹 Uniqueness Constraints

- `Trip ID` must be **unique**

---

### 🔹 Semantic Validations

- `Traveler gender` must be either `'Male'` or `'Female'`

---

### 🔹 Business Rule Checks

- `End date` must be **after** `Start date`

- **Accommodation cost range (based on type)**:
  - Hotel: `$50 - $3000`
  - Hostel: `$20 - $1000`
  - Airbnb: `$30 - $2000`
  - Resort: `$100 - $10000`

## ✅ Post-Processing Validation Rules

### 🔹 Check for missing values 

Must exist and contain **no missing values**:
- `Trip ID`
- `Traveler name`
- `Traveler age`
- `Traveler gender`
- `Destination`
- `Start date`
- `End date`
- `Total cost`
- `Duration (days)`

---

### 🔹 Total Cost Calculation

- `Total cost` must equal the **sum of** `Accommodation cost` and `Transportation cost`  
---

### 🔹 Cost Per Day Validation

- `Cost per day` = `Total cost / Duration (days)`
  - If duration is zero or invalid, cost per day should be `0`

---

### 🔹 Age Group Assignment

`Age group` must align with `Traveler age`:
- `Child`: `0–17`
- `Young Adult`: `18–29`
- `Adult`: `30–59`
- `Senior`: `60–120`

---

### 🔹 Season Assignment

- `Season` must be one of: `'Winter'`, `'Spring'`, `'Summer'`, `'Fall'`

---

### 🔹 Uniqueness

- `Trip ID` must remain **unique** after processing
