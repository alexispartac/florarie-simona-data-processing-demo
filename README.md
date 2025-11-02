# Florarie Simona Data Processing

## Overview
Florarie Simona Data Processing is a FastAPI application that connects to MongoDB Atlas to manage order data. This project provides a RESTful API for creating, reading, updating, and deleting orders, as well as exporting order data to Excel format.

## Project Structure
```
florarie-simona-data-processing
├── src
│   ├── main.py          # Entry point of the application
│   ├── db.py            # Database connection handling
│   ├── routers
│   │   └── orders.py    # Routes for order-related operations
│   ├── models
│   │   └── order.py     # Data model for an order
│   ├── schemas
│   │   └── order.py     # Pydantic schemas for order validation
│   └── utils
│       └── excel.py     # Utility functions for Excel file generation
├── .env.example          # Template for environment variables
├── requirements.txt      # Python dependencies
├── .gitignore            # Files and directories to ignore in Git
└── README.md             # Project documentation
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd florarie-simona-data-processing
   ```

2. **Create a virtual environment:**
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Copy the `.env.example` file to `.env` and fill in the required values:
   ```
   MONGO_URI=<your_mongodb_atlas_connection_string>
   DB_NAME=<your_database_name>
   COLLECTION_NAME=<your_collection_name>
   ```

5. **Run the application:**
   ```
   uvicorn src.main:app --reload
   ```

## Usage
- Access the API at `http://localhost:8000`.
- The following endpoints are available:
  - `GET /`: Check if the backend is running.
  - `GET /export-orders`: Export orders to an Excel file.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License
This project is licensed under the MIT License.