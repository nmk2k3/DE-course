import pandas as pd

df = pd.read_csv('data.csv')

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
