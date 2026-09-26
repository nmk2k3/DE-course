import pandas as pd
import re
import unicodedata

df = pd.read_csv('mini_project_1/data.csv')

## R1: 1 + 2: Salary column cleaning and extracting salary unit and type

df['salary_clean'] = df['salary'].str.strip()

def get_salary_unit(salary):
    if 'USD' in salary:
        return 'USD'
    elif 'triệu' in salary:
        return 'VND'
    else:
        return None

df['salary_unit'] = df['salary_clean'].apply(get_salary_unit)

def get_salary_type(salary):
    if salary == 'Thoả thuận':
        return 'Negotiate'
    elif ' - ' in salary:
        return 'Range'
    elif 'Tới' in salary:
        return 'Max'
    elif 'Trên' in salary:
        return 'Min'
    else: 
        return None

df['salary_type'] = df['salary_clean'].apply(get_salary_type)

def get_number_from_salary_text(salary_text,salary_unit):
    if salary_unit == 'USD':
        return float(salary_text.split(" ")[0].replace(',',''))
    elif salary_unit == 'VND':
        return float(salary_text.split(" ")[0].replace(',','')) * 1_000_000

def get_salary_range(salary, salary_type,salary_unit):
    if salary_type == 'Negotiate':
        return None, None
    elif salary_type == 'Max':
        return None, get_number_from_salary_text(salary.split(" ")[1], salary_unit)
    elif salary_type == 'Min':
        return get_number_from_salary_text(salary.split(" ")[1], salary_unit), None
    elif salary_type == 'Range':
        return get_number_from_salary_text(salary.split(" - ")[0], salary_unit), get_number_from_salary_text(salary.split(" - ")[1], salary_unit)

df[['min_salary', 'max_salary']] = df[['salary_clean', 'salary_type', 'salary_unit']].apply(
    lambda row: get_salary_range(row['salary_clean'], row['salary_type'], row['salary_unit']), axis=1, result_type='expand')

def is_invalid(row):
    if row['salary_type'] == 'Range' and (pd.isna(row["min_salary"]) or pd.isna(row["max_salary"])):
        return True
    elif row['salary_type'] == 'Range' and row["min_salary"] >= row["max_salary"]:
        return True
    elif row["min_salary"] == 0 or row["max_salary"] == 0:
        return True
    elif row["salary_type"] == "Min" and (pd.isna(row["min_salary"]) or pd.notna(row["max_salary"])):
        return True
    elif row["salary_type"] == "Max" and (pd.notna(row["min_salary"]) or pd.isna(row["max_salary"])):
        return True
    elif row["salary_type"] == "Negotiate" and (pd.notna(row["min_salary"]) or pd.notna(row["max_salary"])):
        return True
    else:
        return False

df['invalid'] = df.apply(is_invalid, axis=1)

## R1: 3: mapping address to city and district column

df['address_clean'] = df['address'].str.strip()

location_df = pd.read_excel('mini_project_1/city_district_data.xls')

location_df = location_df[location_df["Cấp"].notna()].copy()

def normalize_location_name(name):
    name = name.strip().lower()

    name = unicodedata.normalize("NFD", name)

    name = "".join(
        char for char in name
        if unicodedata.category(char) != "Mn"
    )

    name = name.replace("đ", "d")

    return name

def get_district(district):
    if district["Tỉnh / Thành Phố"] == 'Thành phố Hồ Chí Minh' and re.search(r"\d", district["Tên"]):
        return district["Tên"].strip()
    else:
        return  district["Tên"].replace(district['Cấp'],'').strip()

location_df['district'] = location_df.apply(
    lambda x: get_district(x),
    axis = 1
)

location_df['district_key'] = location_df['district'].apply(normalize_location_name)

location_df['city'] = location_df.apply(
    lambda x: x['Tỉnh / Thành Phố'].replace('Tỉnh','').replace('Thành phố','').strip(),
    axis = 1
)

location_df['city_key'] = location_df['city'].apply(normalize_location_name)

addition_location_df = pd.read_csv('mini_project_1/addition_city_district_data.csv')

addition_location_df['city_key'] = addition_location_df['city'].apply(normalize_location_name)

addition_location_df['district_key'] = addition_location_df['district'].apply(
    lambda district: '' if pd.isna(district) else normalize_location_name(district)
)

def get_address(address, city_district_clean, city_district_addition):
    splits = address.split(":")

    city_key_set = set(city_district_clean["city_key"])
    district_key_set = set(city_district_clean["district_key"])
    city_addition_key_set = set(city_district_addition["city_key"])
    district_addition_key_set = set(city_district_addition["district_key"])

    parsed = []
    current_city = None

    for parts in splits:

        parts = parts.split(", ")

        for part in parts:
            part = part.strip()

            part_clean = normalize_location_name(part)

            if part in ['Nước Ngoài', 'Toàn Quốc']:
                parsed.append((None, None))

            elif part_clean in city_key_set:
                if current_city is not None:
                    parsed.append((current_city, None))

                current_city = part

            elif part_clean in district_key_set:
                if current_city is not None:
                    parsed.append((current_city, part))
                    current_city = None

            elif part_clean.startswith("tp "):
                if part_clean.replace("tp","").strip() in district_key_set:
                    if current_city is not None:
                        parsed.append((current_city, part))
                        current_city = None

            elif part_clean in city_addition_key_set:
                if current_city is not None:
                    parsed.append((current_city, None))

                current_city = part

            elif part_clean in district_addition_key_set:
                if current_city is not None:
                    parsed.append((current_city, part))
                    current_city = None

    if current_city is not None:
        parsed.append((current_city, None))

    return parsed

df["parsed_address"] = df.apply(
    lambda row: get_address(
        row["address"],
        location_df,
        addition_location_df
    ),
    axis=1
)

valid_location_pairs = set(
    zip(
        location_df["city_key"],
        location_df["district_key"]
    )
)

additional_location_pairs = set(
    zip(
        addition_location_df["city_key"],
        addition_location_df["district_key"]
    )
)

valid_location_pairs = (
    valid_location_pairs
    | additional_location_pairs
)

valid_city_keys = (
    set(location_df["city_key"])
    | set(addition_location_df["city_key"])
)

def is_invalid_address(parsed_address):
    for city, district in parsed_address:

        if city is None and district is None:
            continue

        city_key = normalize_location_name(city)

        if district is None:
            if city_key not in valid_city_keys:
                return True

        else:
            district_key = normalize_location_name(district)

            if district_key.startswith("tp "):
                district_key = district_key.replace("tp ", "", 1).strip()

            if (city_key, district_key) not in valid_location_pairs:
                return True

    return False

df["invalid_address"] = df["parsed_address"].apply(
    is_invalid_address
)

