# InternshipNow

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/JuanJo0607/InternshipNow.git
cd InternshipNow
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Apply migrations

```bash
python manage.py migrate
```

### 4. Load test data

```bash
python manage.py loaddata internshipApp/fixtures/test_users.json
python manage.py loaddata internshipApp/fixtures/job_offers.json
```

### 5. Run the server

```bash
python manage.py runserver
```
