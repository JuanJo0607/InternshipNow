# InternshipNow

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/JuanJo0607/InternshipNow.git
cd InternshipNowProject
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Apply migrations

```bash
python manage.py migrate
```

### 4. Load test data (Optional)

```bash
python manage.py loaddata test_users.json
python manage.py loaddata job_offers.json
```

> Fixtures are located at `accounts/fixtures/test_users.json` and `offers/fixtures/job_offers.json`. Django finds them automatically via the app fixture search path.

## Test Data

### Users

| Username | Password | Role | Notes |
|---|---|---|---|
| `admin` | `admin` | Admin | Superuser — access Django admin at `/admin/` |
| `student_test` | `student123` | Student | Has a `StudentProfile` with skills in Python, Django, SQL, React.js, ML, Git, Docker, Figma |
| `company_test` | `company123` | Company | Has a `CompanyProfile` for **CloudStream Analytics** (IT & Services) |

### Loading fixtures

```bash
# Run from the internshipNowProject/ directory
python manage.py loaddata test_users.json
python manage.py loaddata job_offers.json
```

Load `test_users.json` first — `job_offers.json` depends on the `CompanyProfile` it creates.

### 5. Run the server

```bash
python manage.py runserver
```
