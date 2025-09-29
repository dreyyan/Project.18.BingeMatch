# BingeMatch
_Movie Database & Recommender System via Classification Model_

**BingeMatch** is a Python-based movie database and recommender system that leverages a classification model (model selection pending) to provide personalized movie recommendations. Designed for movie enthusiasts, BingeMatch allows users to explore a comprehensive movie database, access detailed movie information, and receive tailored suggestions based on their preferences. The system aims to enhance the movie-watching experience by combining data-driven insights with an intuitive interface.

The primary purpose of BingeMatch is to deliver accurate, user-specific movie recommendations while offering robust tools for browsing and managing movie data.

## FEATURES
✅ **Movie Database** – Store and retrieve detailed movie information (e.g., title, genre, year).  
✅ **Recommendation Engine** – Generate personalized movie suggestions using a classification model.  
✅ **User Interface** – Command-line interface for browsing movies and viewing recommendations.  

## FUTURE IMPLEMENTATIONS
🚀 **Model Optimization** – Finalize and optimize the classification model for better accuracy.  
🚀 **User Profiles** – Support for saving user preferences and watch history.  
🚀 **API Integration** – Connect to external movie databases (e.g., IMDb, TMDB) for enriched data.  
🚀 **Graphical UI** – Develop a GUI for a more user-friendly experience.  

## UPDATES
🔄 Initial release with core movie database and recommendation functionality.  
🔄 Basic command-line interface for user interaction.  
🔄 Ongoing evaluation of classification models for optimal performance.  

## PROJECT DETAILS
📌 **Author:** dreyyan  
📌 **Started:** 2025-04-07  
📌 **Finished:** 2025-07-20  

## TECH STACK
🛠️ **Language:** Python  
🛠️ **Libraries:** TBD (pending classification model selection, likely scikit-learn or TensorFlow)  

## INSTALLATION
### Prerequisites
- Python 3.8 or higher
- Create a virtual environment (recommended):
  ```
  python -m venv venv
  source venv/bin/activate  # On Unix/Mac
  venv\Scripts\activate     # On Windows
  ```

### Install Dependencies
Install required packages (update based on final model selection, e.g., scikit-learn):
```
pip install scikit-learn  # Example; adjust based on chosen model
```

### Verify Installation
Check Python version:
```
python --version
```

## USAGE
### Running the Application
Set the command prompt size to 72x30 for optimal display:
- On Windows: `mode con: cols=72 lines=30`
- On Unix/Mac: Adjust terminal size to 72 columns by 30 rows.

Start BingeMatch:
```
python main.py
```

### Example Workflow
1. **Launch the App**: Run `python main.py` to start the command-line interface.
2. **Browse Movies**: Explore the movie database by searching or filtering by genre, year, etc.
3. **Get Recommendations**: Input preferences to receive personalized movie suggestions.
4. **View Details**: Access detailed information about selected movies.

### Configuration
- Configure the command prompt size to 72x30 for the best experience.
- Adjust settings (e.g., model parameters) via configuration files or the command-line interface (details TBD).

## DEBUGGING
For issues, check console output for error messages related to data loading or model predictions. Run with:
```
python main.py
```
Report issues via GitHub Issues for detailed troubleshooting.

## PROJECT STRUCTURE
- `main.py`: Entry point for the application (assumed; adjust based on actual structure).
- Other files may include modules for database management, recommendation logic, and user interface (not specified in provided details).

## CONTRIBUTING
Contributions are welcome! Fork the repo, make changes, and submit a pull request:
1. Create a feature branch: `git checkout -b feature/new-feature`
2. Commit changes: `git commit -m "Add new feature"`
3. Push: `git push origin feature/new-feature`
4. Open a pull request

Report issues or suggest features via GitHub Issues.

## LICENSE
This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.