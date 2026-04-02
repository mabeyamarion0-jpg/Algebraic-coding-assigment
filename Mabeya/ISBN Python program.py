from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import re

app = FastAPI()

# ---------- Helper Functions ----------

def clean_isbn(isbn: str) -> str:
    return re.sub(r"[-\s]", "", isbn.upper())


def compute_isbn10_check_digit(isbn9: str) -> str:
    if not re.fullmatch(r"\d{9}", isbn9):
        raise ValueError("ISBN-10 base must be 9 digits")

    total = sum((i + 1) * int(digit) for i, digit in enumerate(isbn9))
    remainder = total % 11

    return "X" if remainder == 10 else str(remainder)


def validate_isbn10(isbn: str) -> bool:
    isbn = clean_isbn(isbn)

    if not re.fullmatch(r"\d{9}[\dX]", isbn):
        return False

    total = 0
    for i in range(10):
        digit = 10 if isbn[i] == "X" else int(isbn[i])
        total += (i + 1) * digit

    return total % 11 == 0


def compute_isbn13_check_digit(isbn12: str) -> str:
    total = 0
    for i, digit in enumerate(isbn12):
        num = int(digit)
        total += num if i % 2 == 0 else num * 3

    remainder = total % 10
    return str((10 - remainder) % 10)


def validate_isbn13(isbn: str) -> bool:
    isbn = clean_isbn(isbn)

    if not re.fullmatch(r"\d{13}", isbn):
        return False

    expected = compute_isbn13_check_digit(isbn[:12])
    return isbn[-1] == expected


def convert_isbn10_to_isbn13(isbn10: str) -> str:
    isbn10 = clean_isbn(isbn10)

    if not validate_isbn10(isbn10):
        raise ValueError("Invalid ISBN-10")

    core = isbn10[:9]
    isbn12 = "978" + core
    check_digit = compute_isbn13_check_digit(isbn12)

    return isbn12 + check_digit


# ---------- Request Model ----------

class ISBNRequest(BaseModel):
    isbn: str


# ---------- API Endpoints ----------

@app.post("/isbn10/check-digit")
def isbn10_check_digit(req: ISBNRequest):
    try:
        isbn = clean_isbn(req.isbn)
        check_digit = compute_isbn10_check_digit(isbn[:9])
        return {
            "input": req.isbn,
            "computed_check_digit": check_digit
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/isbn10/validate")
def isbn10_validate(req: ISBNRequest):
    isbn = clean_isbn(req.isbn)
    valid = validate_isbn10(isbn)

    return {
        "input": req.isbn,
        "valid": valid
    }


@app.post("/isbn10/to-isbn13")
def isbn10_to_isbn13(req: ISBNRequest):
    try:
        converted = convert_isbn10_to_isbn13(req.isbn)
        return {
            "input": req.isbn,
            "isbn13": converted
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/isbn13/validate")
def isbn13_validate(req: ISBNRequest):
    isbn = clean_isbn(req.isbn)
    valid = validate_isbn13(isbn)

    return {
        "input": req.isbn,
        "valid": valid
    }