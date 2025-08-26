import datetime as dt
import difflib
import os
from pathlib import Path
from typing import Dict, List, NamedTuple, Union

import gspread
import polars as pl
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials


load_dotenv()

KEY_PATH = os.getenv('GOOGLE_SHEETS_KEY')
SHEET_ID = os.getenv('SHEET_ID')
SCOPE = ['https://www.googleapis.com/auth/spreadsheets.readonly']  # Permission scope

OUTPUT_DIR = Path(__file__).parent / 'outputs'

class BabyStats(NamedTuple):
    first: str
    middle: str
    gender: str
    hair: str
    eye: str
    length: int
    weight_lbs: int
    weight_ozs: int
    birthday: dt.date
    labor_hours: int
    epidural: str
    cut_cord: str
    catch: str
    faint: str

def calc_name_distance(n1: str, n2: str) -> float:
    # The ratio is a measure of similarity between 0 and 1, so 1 - it yields a "typical" distance
    #      where closer is better
    return 1 - difflib.SequenceMatcher(None, n1.strip().lower(), n2.strip().lower()).ratio()

def score_str(prop_name: str, actual_val: str) -> pl.Expr:
    return (1 - (pl.col(prop_name) == actual_val).cast(pl.Float64)).alias(prop_name)

def calc_scores(records: List[Dict[str, Union[str, int, float]]], actual: BabyStats) -> pl.DataFrame:
    # The DataFrame is definitely overkill, but oh well
    df = pl.DataFrame(records)
    entries = df.rename({
        # Your Name
        # Your Email
        "Baby's First Name": 'First Name',
        # Middle Name
        # Gender
        # Hair Color
        # Eye Color
        'Length (in inches)': 'Length',
        'Weight, pounds part (this question is together with the next question)': 'Pounds',
        'Weight, ounces part (this question is together with the previous question)': 'Ounces',
        # Birthday
        'Hours in labor *in the hospital* before delivery': 'Labor Hours',
        'Did Ashlynne get an epidural?': 'Epidural',
        'Did Nacho cut the cord?': 'Cut Cord',
        'Did Nacho catch the baby?!': 'Catch Baby',
        'Did Nacho faint?!!': 'Faint'
    })

    # Clean up the dates
    entries = entries.with_columns(pl.col('Birthday').str.strptime(pl.Date, '%m/%d/%Y').alias('Birthday'))

    # For all of these, make sure that a lower value is better, "closer" in distance terms
    # Furthermore, make sure all of these are nonnegative and yield 0 for an exact answer
    # Also, make sure all of these are Float64s
    distances = entries.with_columns(
        pl.col('First Name').map_elements(lambda f: calc_name_distance(f, actual.first), return_dtype=pl.Float64).alias('First Name'),
        pl.col('Middle Name').map_elements(lambda m: calc_name_distance(m, actual.middle), return_dtype=pl.Float64).alias('Middle Name'),
        score_str('Gender', actual.gender),
        score_str('Hair Color', actual.hair),
        score_str('Eye Color', actual.eye),
        (pl.col('Length') - actual.length).abs().cast(pl.Float64).alias('Length'),
        pl.struct(['Pounds', 'Ounces']).map_elements(lambda e: abs((e['Pounds'] + e['Ounces'] / 16.) - (actual.weight_lbs + actual.weight_ozs / 16.)), return_dtype=pl.Float64).alias('Weight'),
        pl.col('Birthday').map_elements(lambda b: abs((b - actual.birthday).days), return_dtype=pl.Int64).alias('Birthday'),
        (pl.col('Labor Hours') - actual.labor_hours).abs().cast(pl.Float64).alias('Labor Hours'),
        score_str('Epidural', actual.epidural),
        score_str('Cut Cord', actual.cut_cord),
        score_str('Catch Baby', actual.catch),
        score_str('Faint', actual.faint),
    ).drop(['Pounds', 'Ounces'])  # Now that we calculated weight, we don't need these

    # Scale some distances so that all distances are between 0 and 1
    distances_scaled_01 = distances.with_columns(*[
        pl.col(c) / pl.when(pl.col(c).max() > 0).then(pl.col(c).max()).otherwise(0.).alias(c)
         for c in ['Length', 'Weight', 'Birthday', 'Labor Hours']
    ])

    # The higher the average distance away from the correct answer, the harder the question
    difficulty = distances_scaled_01.drop(['Your Name', 'Your Email', 'Timestamp']).mean()
    # The maximum error anyone achieved compared to the correct answer, possibly 0
    max_error = distances_scaled_01.drop(['Your Name', 'Your Email', 'Timestamp']).max()

    scores_by_column = distances_scaled_01.with_columns(*[
        (difficulty[c][0] * (1 - pl.col(c)) / (max_error[c][0] if max_error[c][0] > 0 else 1)).alias(c)
        for c in distances_scaled_01.columns if c in difficulty.columns
    ])

    columns_for_score = [
        'First Name', 'Middle Name', 'Gender', 'Hair Color',
        'Eye Color', 'Length', 'Weight', 'Birthday',
        'Labor Hours', 'Epidural', 'Cut Cord', 'Catch Baby',
        'Faint'
    ]
    overall_scores = scores_by_column.with_columns(
        pl.sum_horizontal(pl.col(c) for c in columns_for_score).alias('Overall Score')
    ).drop(columns_for_score)

    return overall_scores

if __name__ == '__main__':
    actual = BabyStats(
        os.getenv('ACTUAL_FIRST_NAME'),
        os.getenv('ACTUAL_MIDDLE_NAME'),
        os.getenv('ACTUAL_GENDER'),
        os.getenv('ACTUAL_HAIR_COLOR'),
        os.getenv('ACTUAL_EYE_COLOR'),
        int(os.getenv('ACTUAL_LENGTH')),
        int(os.getenv('ACTUAL_WEIGHT_LBS')),
        int(os.getenv('ACTUAL_WEIGHT_OZS')),
        dt.datetime.strptime(os.getenv('ACTUAL_BIRTHDAY'), '%m/%d/%Y').date(),
        int(os.getenv('ACTUAL_LABOR_HOURS')),
        os.getenv('ACTUAL_EPIDURAL'),
        os.getenv('ACTUAL_CUT_CORD'),
        os.getenv('ACTUAL_CATCH'),
        os.getenv('ACTUAL_FAINT')
    )

    creds = ServiceAccountCredentials.from_json_keyfile_name(KEY_PATH, SCOPE)
    client = gspread.authorize(creds)

    sheet = client.open_by_key(SHEET_ID)
    worksheet = sheet.sheet1
    records = worksheet.get_all_records()

    overall_scores = calc_scores(records, actual)

    OUTPUT_DIR.mkdir(exist_ok=True)

    overall_scores.write_csv(OUTPUT_DIR / 'overall_scores.csv')
