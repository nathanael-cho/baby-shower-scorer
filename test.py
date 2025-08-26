import datetime
import math
import scorer

class bcolors:
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

if __name__ == '__main__':
    guess1 = {
        "Your Name": "Jackie",
        "Your Email": "Jac.kie",
        "Timestamp": ":)",
        "Baby's First Name": "Gus",
        "Middle Name": "Pat",
        "Gender": "Chip",
        "Hair Color": "Blue",
        "Eye Color": "Purple",
        "Length (in inches)": 4,
        "Weight, pounds part (this question is together with the next question)": 2,
        "Weight, ounces part (this question is together with the previous question)": 7,
        "Birthday": "10/11/2025",
        "Hours in labor *in the hospital* before delivery": 2,
        "Did Ashlynne get an epidural?": "Yes",
        "Did Nacho cut the cord?": "Yes",
        "Did Nacho catch the baby?!": "No",
        "Did Nacho faint?!!": "No"
    }
    guess2 = {
        "Your Name": "Brian",
        "Your Email": "Bri.an",
        "Timestamp": "0",
        "Baby's First Name": "Gustavo",
        "Middle Name": "Patrick",
        "Gender": "Dip",
        "Eye Color": "Purple",
        "Length (in inches)": 4,
        "Length (in inches)": 2,
        "Weight, pounds part (this question is together with the next question)": 3,
        "Weight, ounces part (this question is together with the previous question)": 14,
        "Birthday": "10/10/2025",
        "Hours in labor *in the hospital* before delivery": 1,
        "Did Ashlynne get an epidural?": "No",
        "Did Nacho cut the cord?": "No",
        "Did Nacho catch the baby?!": "No",
        "Did Nacho faint?!!": "No"
    }
    guesses = [guess1, guess2]
    actual = scorer.BabyStats("Gustavo", "Patrick", "Chip", "purple", "blue", 42, 3, 14, datetime.date(2025, 10, 11), 1, "Yes", "Yes", "No", "No")

    result = scorer.calc_scores(guesses, actual)

    assert(result.shape == (2, 4))
    assert(result.columns == ["Your Name", "Your Email", "Timestamp", "Overall Score"])
    assert(result["Your Name"][0] == "Jackie")
    assert(result["Your Email"][0] == "Jac.kie")
    assert(result["Timestamp"][0] == ":)")
    assert(math.isclose(result["Overall Score"][0], 2.64875))
    assert(result["Your Name"][1] == "Brian")
    assert(result["Your Email"][1] == "Bri.an")
    assert(result["Timestamp"][1] == "0")
    assert(result["Overall Score"][1] == 2.0)
    print(bcolors.OKGREEN + "All tests pass!" + bcolors.ENDC)
